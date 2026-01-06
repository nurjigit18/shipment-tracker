from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class UserLog(Base):
    """
    Track user actions for audit trail.
    Records all user activities including logins and status confirmations.
    Includes organization_id for analytics and reporting.
    """

    __tablename__ = "user_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)  # login, confirm_status, logout, etc.
    shipment_id = Column(String(50))  # Optional, links action to specific shipment
    details = Column(JSONB)  # Flexible metadata: {"ip": "1.2.3.4", "user_agent": "..."}
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )  # Nullable for analytics
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="logs")
    organization = relationship("Organization", back_populates="user_logs")

    # Indexes for performance
    __table_args__ = (
        Index("idx_user_logs_user_id", "user_id"),
        Index("idx_user_logs_shipment_id", "shipment_id"),
        Index("idx_user_logs_created_at", "created_at"),
        Index("idx_user_logs_organization_id", "organization_id"),
    )
