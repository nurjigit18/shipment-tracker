from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid
import os

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.shipment import StatusUpdateRequest, ShipmentListItem, ShipmentCreate, ShipmentResponse, ShipmentUpdate
from ...services.shipment_service import ShipmentService
from ...services.user_log_service import UserLogService
from ...services.pdf_service import PDFService
from ...models.user import User

router = APIRouter()


@router.post("/", response_model=ShipmentResponse, status_code=201)
async def create_shipment(
    shipment: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new shipment with auto-generated ID.

    Frontend calls: POST /api/shipments
    with body: {
        "supplier": "Supplier Name",
        "warehouse": "Казань",
        "route_type": "VIA_FF" | "DIRECT",
        "bags_data": [{
            "bag_id": "BAG-1",
            "items": [
                {"model": "shirt", "color": "red", "sizes": {"S": 10, "M": 20}}
            ]
        }]
    }

    Shipment ID is auto-generated in format: SHIP-YYYYMMDD-XXX

    Args:
        shipment: Shipment creation data
        db: Database session
        current_user: Authenticated user (contains organization_id)

    Returns:
        Created shipment data with empty events list

    Raises:
        HTTPException 401: If not authenticated
    """
    result = await ShipmentService.create_shipment(
        db=db,
        shipment_data=shipment,
        organization_id=current_user.organization_id,
    )

    # Log the shipment creation
    await UserLogService.log_action(
        db,
        user_id=current_user.id,
        action="create_shipment",
        shipment_id=result["shipment"]["id"],
        details={"supplier": shipment.supplier, "warehouse": shipment.warehouse},
        organization_id=current_user.organization_id,
    )

    return result


@router.get("/", response_model=List[ShipmentListItem])
async def list_shipments(
    status: Optional[str] = Query(None, description="Filter by status"),
    supplier: Optional[str] = Query(None, description="Filter by supplier"),
    limit: int = Query(default=20, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Skip results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List shipments for current user's organization.

    Frontend calls: GET /api/shipments?status=...&supplier=...&limit=20&offset=0

    Args:
        status: Optional status filter (SENT_FROM_FACTORY, SHIPPED_FROM_FF, DELIVERED)
        supplier: Optional supplier name filter
        limit: Maximum number of results (default 20, max 100)
        offset: Number of results to skip for pagination (default 0)
        db: Database session
        current_user: Authenticated user (contains organization_id)

    Returns:
        List of shipments for user's organization

    Security:
        - Automatically filtered by user's organization_id
        - Users can only see shipments from their organization
    """
    shipments = await ShipmentService.list_shipments(
        db=db,
        organization_id=current_user.organization_id,
        status=status,
        supplier=supplier,
        limit=limit,
        offset=offset,
    )
    return shipments


@router.get("/{shipment_id}")
async def get_shipment(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get shipment details by ID (organization-filtered for security).

    Frontend calls: GET /api/shipments/{shipment_id}

    Args:
        shipment_id: Shipment ID
        db: Database session
        current_user: Authenticated user (contains organization_id)

    Returns:
        Shipment data with events (status history)

    Raises:
        HTTPException 404: If shipment not found or access denied
        HTTPException 401: If not authenticated
    """
    # CRITICAL: Pass organization_id to filter shipment by organization
    data = await ShipmentService.get_shipment(
        db, shipment_id, current_user.organization_id
    )
    return data


@router.post("/{shipment_id}/events")
async def create_shipment_event(
    shipment_id: str,
    request: StatusUpdateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update shipment status (confirm action).

    Frontend calls: POST /api/shipments/{shipment_id}/events
    with body: {"action": "SENT_FROM_FACTORY" | "SHIPPED_FROM_FF" | "DELIVERED"}

    Args:
        shipment_id: Shipment ID
        request: Status update request with action
        idempotency_key: Optional header to prevent duplicate submissions
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated shipment data with events

    Raises:
        HTTPException 403: If user role doesn't have permission for this action
        HTTPException 404: If shipment not found
        HTTPException 400: If status transition is invalid
    """
    # Define role permissions for each status
    role_permissions = {
        "SENT_FROM_FACTORY": ["supplier", "admin"],
        "SHIPPED_FROM_FF": ["ff", "admin"],
        "DELIVERED": ["driver", "warehouse", "admin"],
    }

    allowed_roles = role_permissions.get(request.action.value, [])
    if current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{current_user.role.name}' cannot perform action '{request.action.value}'",
        )

    # Generate idempotency key if not provided
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())

    # Update status (service validates organization)
    result = await ShipmentService.update_status(
        db, shipment_id, request.action, current_user, idempotency_key
    )

    # Log action with organization tracking
    await UserLogService.log_action(
        db,
        user_id=current_user.id,
        action="confirm_status",
        shipment_id=shipment_id,
        details={"new_status": request.action.value},
        organization_id=current_user.organization_id,
    )

    return result


@router.put("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: str,
    update_data: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update shipment data (supplier-only).

    Frontend calls: PUT /api/shipments/{shipment_id}
    with body: {
        "supplier": "New Supplier",
        "warehouse": "New Warehouse",
        "route_type": "VIA_FF",
        "shipment_date": "2026-01-15",
        "bags_data": [...]
    }

    All changes are logged in shipment_change_log table.

    Args:
        shipment_id: Shipment ID
        update_data: Fields to update (all optional)
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated shipment data with events

    Raises:
        HTTPException 403: If user is not a supplier
        HTTPException 404: If shipment not found
    """
    # Only suppliers can edit shipments
    if current_user.role.name not in ["supplier", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only suppliers can edit shipments"
        )

    # Convert Pydantic model to dict, excluding None values
    update_dict = update_data.model_dump(exclude_none=True)

    # Convert route_type enum to string value if present
    if "route_type" in update_dict:
        update_dict["route_type"] = update_dict["route_type"].value

    # Convert bags_data from Pydantic models to dicts if present
    if "bags_data" in update_dict:
        update_dict["bags_data"] = [
            {
                "bag_id": bag.bag_id,
                "items": [
                    {
                        "model": item.model,
                        "color": item.color,
                        "sizes": item.sizes
                    }
                    for item in bag.items
                ]
            }
            for bag in update_data.bags_data
        ]

    result = await ShipmentService.update_shipment(
        db=db,
        shipment_id=shipment_id,
        update_data=update_dict,
        user=current_user,
    )

    # Log the update action
    await UserLogService.log_action(
        db,
        user_id=current_user.id,
        action="update_shipment",
        shipment_id=shipment_id,
        details={"updated_fields": list(update_dict.keys())},
        organization_id=current_user.organization_id,
    )

    return result


@router.get("/{shipment_id}/pdf")
async def download_shipment_pdf(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download PDF report for a shipment with embedded QR code.

    Args:
        shipment_id: ID of the shipment
        db: Database session
        current_user: Authenticated user

    Returns:
        PDF file as bytes

    Raises:
        HTTPException 404: If shipment not found or access denied
    """
    # Get shipment data
    shipment_data = await ShipmentService.get_shipment(
        db=db,
        shipment_id=shipment_id,
        organization_id=current_user.organization_id
    )

    # Get base URL from environment or use default
    base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Generate PDF
    pdf_bytes = PDFService.generate_shipment_pdf(
        shipment_data=shipment_data['shipment'],
        base_url=base_url
    )

    # Log the download action
    await UserLogService.log_action(
        db,
        user_id=current_user.id,
        action="download_pdf",
        shipment_id=shipment_id,
        details={"format": "pdf"},
        organization_id=current_user.organization_id,
    )

    # Return PDF with proper headers
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=shipment_{shipment_id}.pdf"
        }
    )
