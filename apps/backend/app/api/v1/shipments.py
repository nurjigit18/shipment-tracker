from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.shipment import StatusUpdateRequest, ShipmentListItem, ShipmentCreate, ShipmentResponse
from ...services.shipment_service import ShipmentService
from ...services.user_log_service import UserLogService
from ...models.user import User

router = APIRouter()


@router.post("/", response_model=ShipmentResponse, status_code=201)
async def create_shipment(
    shipment: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new shipment.

    Frontend calls: POST /api/shipments
    with body: {
        "id": "SHIP-001",
        "supplier": "Supplier Name",
        "warehouse": "Казань",
        "route_type": "VIA_FF" | "DIRECT",
        "bags": [{"bag_id": "SHIP-001-1", "sizes": {"S": 10, "M": 20}}]
    }

    Args:
        shipment: Shipment creation data
        db: Database session
        current_user: Authenticated user (contains organization_id)

    Returns:
        Created shipment data with empty events list

    Raises:
        HTTPException 400: If shipment ID already exists
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
        shipment_id=shipment.id,
        details={"supplier": shipment.supplier, "warehouse": shipment.warehouse},
        organization_id=current_user.organization_id,
    )

    return result


@router.get("/", response_model=List[ShipmentListItem])
async def list_shipments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(default=20, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Skip results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List shipments for current user's organization.

    Frontend calls: GET /api/shipments?status=...&limit=20&offset=0

    Args:
        status: Optional status filter (SENT_FROM_FACTORY, SHIPPED_FROM_FF, DELIVERED)
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
