from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
import json

from ..models.shipment import ShipmentChangeLog
from ..models.user import User


class ShipmentChangeLogService:
    """Service for logging changes to shipments"""

    @staticmethod
    async def log_change(
        db: AsyncSession,
        shipment_id: str,
        changed_by: int,
        change_type: str,
        old_value: Any,
        new_value: Any,
        organization_id: int,
        notes: Optional[str] = None,
    ) -> None:
        """
        Log a change to a shipment.

        Args:
            db: Database session
            shipment_id: ID of the shipment being changed
            changed_by: User ID who made the change
            change_type: Type of change (bag_contents, shipment_date, supplier, warehouse, route_type)
            old_value: Previous value (will be JSON serialized)
            new_value: New value (will be JSON serialized)
            organization_id: Organization ID
            notes: Optional notes about the change
        """
        # Convert values to JSON-serializable format
        old_json = old_value if isinstance(old_value, (dict, list)) else str(old_value) if old_value is not None else None
        new_json = new_value if isinstance(new_value, (dict, list)) else str(new_value) if new_value is not None else None

        change_log = ShipmentChangeLog(
            shipment_id=shipment_id,
            changed_by=changed_by,
            change_type=change_type,
            old_value=old_json,
            new_value=new_json,
            notes=notes,
            organization_id=organization_id,
        )

        db.add(change_log)
        await db.commit()
