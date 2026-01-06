from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional
import uuid

from ..models.shipment import Shipment, ShipmentStatusHistory
from ..models.user import User
from ..schemas.shipment import ShipmentStatus


class ShipmentService:
    """Shipment business logic and data access"""

    @staticmethod
    async def list_shipments(
        db: AsyncSession,
        organization_id: int,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List shipments for organization with optional filtering and pagination.

        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of shipment dictionaries

        Raises:
            HTTPException: If database error occurs
        """
        # Build query with organization filter
        query = select(Shipment).where(Shipment.organization_id == organization_id)

        # Apply status filter if provided
        if status:
            query = query.where(Shipment.current_status == status)

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
        db: AsyncSession, shipment_id: str, organization_id: int
    ) -> dict:
        """
        Get shipment by ID with status history (organization-filtered for security).

        Args:
            db: Database session
            shipment_id: Shipment ID
            organization_id: Organization ID for multi-tenant filtering

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
                db, shipment_id, user.organization_id
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

        return await ShipmentService.get_shipment(db, shipment_id, user.organization_id)

    @staticmethod
    def _validate_status_transition(current: Optional[str], new: str):
        """
        Validate status can transition from current to new.

        Args:
            current: Current status (can be None)
            new: New status to transition to

        Raises:
            HTTPException 400: If transition is invalid
        """
        valid_transitions = {
            None: ["SENT_FROM_FACTORY"],
            "SENT_FROM_FACTORY": ["SHIPPED_FROM_FF"],
            "SHIPPED_FROM_FF": ["DELIVERED"],
            "DELIVERED": [],  # Terminal state
        }

        if new not in valid_transitions.get(current, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from {current} to {new}",
            )
