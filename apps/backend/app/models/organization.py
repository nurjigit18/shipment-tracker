from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base


class Organization(Base):
    """Organization/Company model for multi-tenant isolation"""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    users = relationship("User", back_populates="organization")
    shipments = relationship("Shipment", back_populates="organization")
    user_logs = relationship("UserLog", back_populates="organization")
    status_history = relationship("ShipmentStatusHistory", back_populates="organization")
    warehouses = relationship("Warehouse", back_populates="organization")
    suppliers = relationship("Supplier", back_populates="organization")
    fulfillments = relationship("Fulfillment", back_populates="organization")
    product_models = relationship("ProductModel", back_populates="organization")
    product_colors = relationship("ProductColor", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
