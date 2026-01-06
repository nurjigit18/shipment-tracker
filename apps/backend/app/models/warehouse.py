from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Warehouse(Base):
    """
    Warehouse/destination locations table.
    Managers select from these warehouses when creating shipments.
    """

    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)  # e.g., "Казань"
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="warehouses")

    def __repr__(self):
        return f"<Warehouse(id={self.id}, name='{self.name}', active={self.is_active})>"


class ProductModel(Base):
    """
    Product models table (e.g., "shirt", "pants", "jacket").
    Supports autocomplete and allows managers to add new models.
    """

    __tablename__ = "product_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="product_models")

    def __repr__(self):
        return f"<ProductModel(id={self.id}, name='{self.name}')>"


class ProductColor(Base):
    """
    Product colors table (e.g., "red", "blue", "black").
    Supports autocomplete and allows managers to add new colors.
    """

    __tablename__ = "product_colors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="product_colors")

    def __repr__(self):
        return f"<ProductColor(id={self.id}, name='{self.name}')>"


class Supplier(Base):
    """
    Suppliers table.
    Each manager can be assigned to one or more suppliers.
    """

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="suppliers")
    users = relationship("UserSupplier", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', active={self.is_active})>"
