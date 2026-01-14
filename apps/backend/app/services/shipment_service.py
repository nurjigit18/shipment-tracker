from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional, List, Dict
import uuid
from datetime import datetime

from ..models.shipment import Shipment, ShipmentStatusHistory
from ..models.user import User
from ..schemas.shipment import ShipmentStatus, ShipmentCreate
from .google_sheets_service import sheets_service


class ShipmentService:
    """Shipment business logic and data access"""

    @staticmethod
    async def create_shipment(
        db: AsyncSession,
        shipment_data: ShipmentCreate,
        organization_id: int,
        current_user: User = None,
    ) -> dict:
        """
        Create a new shipment with auto-generated ID.

        Args:
            db: Database session
            shipment_data: Shipment creation data
            organization_id: Organization ID for multi-tenant filtering

        Returns:
            Created shipment data
        """
        # Auto-generate shipment ID with format: SHIP-YYYYMMDD-XXX
        # date_str = datetime.now().strftime("%Y%m%d")

        # Find the last shipment created today
        result = await db.execute(
            select(Shipment)
            .where(
                Shipment.organization_id == organization_id,
                Shipment.id.like(f"SHIP-{organization_id}-%")
            )
            .order_by(Shipment.id.desc())
            .limit(1)
        )
        last_shipment = result.scalars().first()

        # Generate next sequence number
        if last_shipment:
            # Extract sequence number from last ID (e.g., SHIP-20260106-003 -> 003)
            last_seq = int(last_shipment.id.split('-')[-1])
            next_seq = last_seq + 1
        else:
            next_seq = 1

        shipment_id = f"SHIP-{organization_id}-{next_seq:04d}"

        # Calculate totals from bags_data with items
        total_bags = len(shipment_data.bags_data)
        total_pieces = sum(
            sum(item_sizes.values())
            for bag in shipment_data.bags_data
            for item in bag.items
            for item_sizes in [item.sizes]
        )

        # Transform bags_data to include items with model/color
        bags_data_dict = [
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
            for bag in shipment_data.bags_data
        ]

        # Create shipment
        shipment = Shipment(
            id=shipment_id,
            supplier=shipment_data.supplier,
            warehouse=shipment_data.warehouse,
            route_type=shipment_data.route_type.value,
            shipment_type=shipment_data.shipment_type.value,
            fulfillment=shipment_data.fulfillment,
            shipment_date=shipment_data.shipment_date,
            bags_data=bags_data_dict,
            total_bags=total_bags,
            total_pieces=total_pieces,
            organization_id=organization_id,
            current_status="новая отправка",
        )

        db.add(shipment)
        await db.commit()
        await db.refresh(shipment)

        # Build response data
        response_data = {
            "shipment": {
                "id": shipment.id,
                "supplier": shipment.supplier,
                "warehouse": shipment.warehouse,
                "route_type": shipment.route_type,
                "shipment_type": shipment.shipment_type,
                "fulfillment": shipment.fulfillment,
                "shipment_date": shipment.shipment_date.isoformat() if shipment.shipment_date else None,
                "current_status": shipment.current_status,
                "bags": shipment.bags_data,
                "totals": {"bags": shipment.total_bags, "pieces": shipment.total_pieces},
            },
            "events": [],
        }

        # Sync to Google Sheets (non-blocking, don't fail if it errors)
        try:
            username = current_user.username if current_user else "Unknown"
            sheets_service.sync_shipment_to_sheets(response_data, username)
        except Exception as e:
            print(f"⚠️  Failed to sync to Google Sheets: {e}")
            # Continue anyway - don't fail the shipment creation

        return response_data

    @staticmethod
    async def list_shipments(
        db: AsyncSession,
        organization_id: int,
        current_user: User = None,
        status: Optional[str] = None,
        supplier: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List shipments with role-based filtering.

        Access Control:
        - Owner/Admin/Supplier: See all shipments in their organization
        - FF: See only shipments where fulfillment field matches their company
        - Driver: Cannot list (returns empty), can only access via direct URL

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            current_user: Current authenticated user
            status: Optional status filter
            supplier: Optional supplier name filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of shipment dictionaries

        Raises:
            HTTPException: If database error occurs
        """
        if not current_user:
            return []

        # Driver role: cannot list shipments, can only access via direct URL
        if current_user.role.name == 'driver':
            return []

        # Users without organization cannot see any shipments
        if organization_id is None:
            return []

        # Build query with organization filter
        query = select(Shipment).where(Shipment.organization_id == organization_id)

        # FF role: filter by fulfillment company
        if current_user.role.name == 'ff':
            # Get user's fulfillment company
            user_with_ff = await db.execute(
                select(User).options(selectinload(User.fulfillment))
                .where(User.id == current_user.id)
            )
            user = user_with_ff.scalar_one_or_none()

            if user and user.fulfillment:
                # Only show shipments where fulfillment matches their company name
                query = query.where(Shipment.fulfillment == user.fulfillment.name)
            else:
                # FF user has no fulfillment assigned, return empty list
                return []

        # Owner/Admin/Supplier: see all shipments in organization (no additional filter)

        # Apply status filter if provided
        if status:
            query = query.where(Shipment.current_status == status)

        # Apply supplier filter if provided
        if supplier:
            query = query.where(Shipment.supplier == supplier)

        # Order by most recent first
        query = query.order_by(Shipment.created_at.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        shipments = result.scalars().all()

        # Format response
        return [
            {
                "id": s.id,
                "supplier": s.supplier,
                "warehouse": s.warehouse,
                "route_type": s.route_type,
                "shipment_type": s.shipment_type,
                "fulfillment": s.fulfillment,
                "current_status": s.current_status,
                "total_bags": s.total_bags,
                "total_pieces": s.total_pieces,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in shipments
        ]

    @staticmethod
    async def get_shipment(
        db: AsyncSession,
        shipment_id: str,
        organization_id: int,
        current_user: User = None
    ) -> dict:
        """
        Get shipment by ID with status history and role-based access control.

        Access Control:
        - Owner/Admin/Supplier: Can access all shipments in their organization
        - FF: Can only access shipments where fulfillment matches their company
        - Driver: Can access any shipment in their organization (via direct URL)

        Args:
            db: Database session
            shipment_id: Shipment ID
            organization_id: Organization ID for multi-tenant filtering
            current_user: Current authenticated user

        Returns:
            Dictionary with shipment and events matching frontend expectations

        Raises:
            HTTPException 404: If shipment not found or access denied
        """
        # CRITICAL: Filter by BOTH shipment_id AND organization_id for security
        result = await db.execute(
            select(Shipment).where(
                Shipment.id == shipment_id, Shipment.organization_id == organization_id
            )
        )
        shipment = result.scalar_one_or_none()

        if not shipment:
            # Don't leak info about whether shipment exists in other organizations
            raise HTTPException(
                status_code=404, detail="Shipment not found or access denied"
            )

        # Additional check for FF role: must match fulfillment company
        if current_user and current_user.role.name == 'ff':
            user_with_ff = await db.execute(
                select(User).options(selectinload(User.fulfillment))
                .where(User.id == current_user.id)
            )
            user = user_with_ff.scalar_one_or_none()

            if user and user.fulfillment:
                # Check if shipment's fulfillment matches user's company
                if shipment.fulfillment != user.fulfillment.name:
                    raise HTTPException(
                        status_code=404, detail="Shipment not found or access denied"
                    )
            else:
                # FF user has no fulfillment assigned
                raise HTTPException(
                    status_code=404, detail="Shipment not found or access denied"
                )

        # Get status history with user info
        history_result = await db.execute(
            select(ShipmentStatusHistory)
            .options(selectinload(ShipmentStatusHistory.changed_by_user))
            .where(ShipmentStatusHistory.shipment_id == shipment_id)
            .order_by(ShipmentStatusHistory.changed_at.desc())
        )
        history = history_result.scalars().all()

        # Format response matching frontend expectations
        return {
            "shipment": {
                "id": shipment.id,
                "supplier": shipment.supplier,
                "warehouse": shipment.warehouse,
                "route_type": shipment.route_type,
                "shipment_type": shipment.shipment_type,
                "fulfillment": shipment.fulfillment,
                "shipment_date": shipment.shipment_date.isoformat() if shipment.shipment_date else None,
                "current_status": shipment.current_status,
                "bags": shipment.bags_data,
                "totals": {"bags": shipment.total_bags, "pieces": shipment.total_pieces},
            },
            "events": [
                {
                    "id": h.id,
                    "status": h.status,
                    "changed_by": h.changed_by_user.username,
                    "changed_at": h.changed_at.isoformat(),
                    "notes": h.notes,
                }
                for h in history
            ],
        }

    @staticmethod
    async def update_status(
        db: AsyncSession,
        shipment_id: str,
        new_status: ShipmentStatus,
        user: User,
        idempotency_key: str,
    ) -> dict:
        """
        Update shipment status and create history record (organization-validated).

        Args:
            db: Database session
            shipment_id: Shipment ID
            new_status: New status to set
            user: User making the change (contains organization_id)
            idempotency_key: Key to prevent duplicate submissions

        Returns:
            Updated shipment data

        Raises:
            HTTPException 404: If shipment not found or access denied
            HTTPException 400: If status transition is invalid
            HTTPException 403: If organization mismatch
        """
        # CRITICAL: Get shipment filtered by user's organization
        result = await db.execute(
            select(Shipment).where(
                Shipment.id == shipment_id,
                Shipment.organization_id == user.organization_id,
            )
        )
        shipment = result.scalar_one_or_none()

        if not shipment:
            raise HTTPException(
                status_code=404, detail="Shipment not found or access denied"
            )

        # Double-check organization match (defense in depth)
        if shipment.organization_id != user.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot update shipment from different organization",
            )

        # Validate status transition
        ShipmentService._validate_status_transition(
            shipment.current_status, new_status.value
        )

        # Check idempotency - prevent duplicate submissions
        existing = await db.execute(
            select(ShipmentStatusHistory).where(
                ShipmentStatusHistory.idempotency_key == idempotency_key
            )
        )
        if existing.scalar_one_or_none():
            # Already processed, return current state
            return await ShipmentService.get_shipment(
                db, shipment_id, user.organization_id, user
            )

        # Update shipment status
        shipment.current_status = new_status.value

        # Create history record with organization_id
        history = ShipmentStatusHistory(
            shipment_id=shipment_id,
            status=new_status.value,
            changed_by=user.id,
            organization_id=user.organization_id,  # NEW - Track organization
            idempotency_key=idempotency_key,
        )
        db.add(history)

        await db.commit()
        await db.refresh(shipment)

        # Sync status update to Google Sheets (non-blocking)
        try:
            sheets_service.update_shipment_status_in_sheets(
                shipment_id=shipment_id,
                new_status=new_status.value,
                supplier_name=shipment.supplier
            )
        except Exception as e:
            print(f"⚠️  Failed to update status in Google Sheets: {e}")
            # Continue anyway - don't fail the status update

        return await ShipmentService.get_shipment(db, shipment_id, user.organization_id, user)

    @staticmethod
    def _validate_status_transition(current: Optional[str], new: str):
        """
        Validate status can transition from current to new.

        Args:
            current: Current status (can be None or "новая отправка")
            new: New status to transition to

        Raises:
            HTTPException 400: If transition is invalid
        """
        valid_transitions = {
            None: ["SENT_FROM_FACTORY"],
            "новая отправка": ["SENT_FROM_FACTORY"],
            "SENT_FROM_FACTORY": ["SHIPPED_FROM_FF"],
            "SHIPPED_FROM_FF": ["DELIVERED"],
            "DELIVERED": [],  # Terminal state
        }

        if new not in valid_transitions.get(current, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from {current} to {new}",
            )

    @staticmethod
    async def update_shipment(
        db: AsyncSession,
        shipment_id: str,
        update_data: dict,
        user: User,
    ) -> dict:
        """
        Update shipment data and log all changes.

        Args:
            db: Database session
            shipment_id: Shipment ID
            update_data: Dictionary of fields to update
            user: User making the change (contains organization_id)

        Returns:
            Updated shipment data

        Raises:
            HTTPException 404: If shipment not found or access denied
            HTTPException 403: If organization mismatch
        """
        from .shipment_change_log_service import ShipmentChangeLogService

        # CRITICAL: Get shipment filtered by user's organization
        result = await db.execute(
            select(Shipment).where(
                Shipment.id == shipment_id,
                Shipment.organization_id == user.organization_id,
            )
        )
        shipment = result.scalar_one_or_none()

        if not shipment:
            raise HTTPException(
                status_code=404, detail="Shipment not found or access denied"
            )

        # Double-check organization match (defense in depth)
        if shipment.organization_id != user.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot update shipment from different organization",
            )

        # Track changes and update fields
        changes_made = False

        if "supplier" in update_data and update_data["supplier"] != shipment.supplier:
            old_value = shipment.supplier
            shipment.supplier = update_data["supplier"]
            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "supplier", old_value, update_data["supplier"], user.organization_id
            )
            changes_made = True

        if "warehouse" in update_data and update_data["warehouse"] != shipment.warehouse:
            old_value = shipment.warehouse
            shipment.warehouse = update_data["warehouse"]
            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "warehouse", old_value, update_data["warehouse"], user.organization_id
            )
            changes_made = True

        if "route_type" in update_data and update_data["route_type"] != shipment.route_type:
            old_value = shipment.route_type
            shipment.route_type = update_data["route_type"]
            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "route_type", old_value, update_data["route_type"], user.organization_id
            )
            changes_made = True

        if "shipment_type" in update_data and update_data["shipment_type"] != shipment.shipment_type:
            old_value = shipment.shipment_type
            shipment.shipment_type = update_data["shipment_type"]
            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "shipment_type", old_value, update_data["shipment_type"], user.organization_id
            )
            changes_made = True

        if "fulfillment" in update_data and update_data["fulfillment"] != shipment.fulfillment:
            old_value = shipment.fulfillment
            shipment.fulfillment = update_data["fulfillment"]
            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "fulfillment", old_value, update_data["fulfillment"], user.organization_id
            )
            changes_made = True

        if "shipment_date" in update_data and update_data["shipment_date"] != shipment.shipment_date:
            old_value = shipment.shipment_date.isoformat() if shipment.shipment_date else None
            shipment.shipment_date = update_data["shipment_date"]
            new_value = update_data["shipment_date"].isoformat() if update_data["shipment_date"] else None
            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "shipment_date", old_value, new_value, user.organization_id
            )
            changes_made = True

        if "bags_data" in update_data and update_data["bags_data"] != shipment.bags_data:
            old_value = shipment.bags_data
            new_bags_data = update_data["bags_data"]

            # Recalculate totals
            total_bags = len(new_bags_data)
            total_pieces = sum(
                sum(item["sizes"].values())
                for bag in new_bags_data
                for item in bag.get("items", [])
            )

            shipment.bags_data = new_bags_data
            shipment.total_bags = total_bags
            shipment.total_pieces = total_pieces

            await ShipmentChangeLogService.log_change(
                db, shipment_id, user.id, "bag_contents", old_value, new_bags_data, user.organization_id
            )
            changes_made = True

        if changes_made:
            await db.commit()
            await db.refresh(shipment)

        return await ShipmentService.get_shipment(db, shipment_id, user.organization_id, user)
