from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Shipment(Base):
    """
    Shipment tracking table with multi-tenant organization support.
    Stores information about garment shipments with JSONB bag data.

    bags_data format: [
        {
            "bag_id": "SHIP-001-1",
            "items": [
                {"model": "shirt", "color": "red", "sizes": {"XS": 10, "S": 10}},
                {"model": "pants", "color": "black", "sizes": {"M": 16, "L": 25}}
            ]
        }
    ]
    """

    __tablename__ = "shipments"

    id = Column(String(50), primary_key=True)  # Auto-generated: SHIP-{year}-{seq}
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    route_type = Column(String(20), nullable=False)  # DIRECT or VIA_FF
    current_status = Column(String(50))  # NULL, SENT_FROM_FACTORY, SHIPPED_FROM_FF, DELIVERED
    bags_data = Column(JSONB, nullable=False)  # Structured bag data with items
    total_bags = Column(Integer, nullable=False)
    total_pieces = Column(Integer, nullable=False)
    ship_date = Column(Date, nullable=False)  # дата отправки
    actual_arrival_date = Column(Date)  # факт. дата прибытия
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    google_sheets_id = Column(String(100))  # For future Google Sheets integration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="shipments")
    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    status_history = relationship(
        "ShipmentStatusHistory", back_populates="shipment", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_shipments_current_status", "current_status"),
        Index("idx_shipments_created_at", "created_at"),
        Index("idx_shipments_organization_id", "organization_id"),
    )

    def __repr__(self):
        return f"<Shipment(id='{self.id}', org_id={self.organization_id}, status='{self.current_status}')>"


class ShipmentStatusHistory(Base):
    """
    Track all status changes for shipments.
    Provides complete audit trail of who changed what and when.
    Includes organization_id for analytics and reporting.
    """

    __tablename__ = "shipment_status_history"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)  # SENT_FROM_FACTORY, SHIPPED_FROM_FF, DELIVERED
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)  # Optional notes about the status change
    idempotency_key = Column(String(100), unique=True)  # Prevent duplicate submissions
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )  # Nullable for analytics

    # Relationships
    shipment = relationship("Shipment", back_populates="status_history")
    changed_by_user = relationship("User", back_populates="status_changes")
    organization = relationship("Organization", back_populates="status_history")

    # Indexes for performance
    __table_args__ = (
        Index("idx_shipment_history_shipment_id", "shipment_id"),
        Index("idx_shipment_history_changed_at", "changed_at"),
        Index("idx_shipment_history_organization_id", "organization_id"),
    )
