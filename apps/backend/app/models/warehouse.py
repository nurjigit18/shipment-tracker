from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Warehouse(Base):
    """
    Warehouse/destination locations table.
    Managers select from these warehouses when creating shipments.
    Warehouses are associated with suppliers through SupplierWarehouse junction table.
    """

    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # Removed unique constraint to allow same name in different orgs
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="warehouses")
    suppliers = relationship("SupplierWarehouse", back_populates="warehouse")

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
    fulfillments = relationship("SupplierFulfillment", back_populates="supplier")
    warehouses = relationship("SupplierWarehouse", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', active={self.is_active})>"


class Fulfillment(Base):
    """
    Fulfillment centers table.
    These are the FF companies that suppliers can work with.
    """

    __tablename__ = "fulfillments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="fulfillments")
    suppliers = relationship("SupplierFulfillment", back_populates="fulfillment")

    def __repr__(self):
        return f"<Fulfillment(id={self.id}, name='{self.name}', active={self.is_active})>"


class SupplierFulfillment(Base):
    """
    Many-to-many relationship between suppliers and fulfillments.
    Each supplier can work with multiple fulfillment centers.
    """

    __tablename__ = "supplier_fulfillments"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    fulfillment_id = Column(Integer, ForeignKey("fulfillments.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="fulfillments")
    fulfillment = relationship("Fulfillment", back_populates="suppliers")

    def __repr__(self):
        return f"<SupplierFulfillment(supplier_id={self.supplier_id}, fulfillment_id={self.fulfillment_id})>"


class SupplierWarehouse(Base):
    """
    Many-to-many relationship between suppliers and warehouses.
    Each supplier can have multiple warehouses they ship to.
    """

    __tablename__ = "supplier_warehouses"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="warehouses")
    warehouse = relationship("Warehouse", back_populates="suppliers")

    def __repr__(self):
        return f"<SupplierWarehouse(supplier_id={self.supplier_id}, warehouse_id={self.warehouse_id})>"
