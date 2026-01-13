"""Database models for the shipment tracking system."""

from .user import User, Role
from .shipment import Shipment, ShipmentStatusHistory, ShipmentChangeLog
from .user_log import UserLog
from .organization import Organization
from .warehouse import Warehouse, ProductModel, ProductColor, Supplier, Fulfillment, SupplierFulfillment, SupplierWarehouse
from .user_supplier import UserSupplier

__all__ = [
    "User",
    "Role",
    "Shipment",
    "ShipmentStatusHistory",
    "ShipmentChangeLog",
    "UserLog",
    "Organization",
    "Warehouse",
    "ProductModel",
    "ProductColor",
    "Supplier",
    "Fulfillment",
    "SupplierFulfillment",
    "SupplierWarehouse",
    "UserSupplier",
]
