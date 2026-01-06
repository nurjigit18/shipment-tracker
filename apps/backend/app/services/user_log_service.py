from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..models.user_log import UserLog


class UserLogService:
    """User activity logging service for audit trail"""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: int,
        action: str,
        shipment_id: Optional[str] = None,
        details: Optional[dict] = None,
        organization_id: Optional[int] = None,
    ):
        """
        Log user action to audit trail.

        Args:
            db: Database session
            user_id: ID of user performing action
            action: Action name (login, logout, confirm_status, etc.)
            shipment_id: Optional shipment ID related to action
            details: Optional additional details (IP address, user agent, etc.)
            organization_id: Optional organization ID for analytics
        """
        log = UserLog(
            user_id=user_id,
            action=action,
            shipment_id=shipment_id,
            details=details,
            organization_id=organization_id,
        )
        db.add(log)
        await db.commit()
