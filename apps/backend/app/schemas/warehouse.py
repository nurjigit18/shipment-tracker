from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class WarehouseBase(BaseModel):
    """Base warehouse schema"""

    name: str


class WarehouseCreate(WarehouseBase):
    """Create warehouse request"""

    pass


class WarehouseUpdate(BaseModel):
    """Update warehouse request"""

    name: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    """Warehouse response"""

    id: int
    is_active: bool
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductModelBase(BaseModel):
    """Base product model schema"""

    name: str


class ProductModelCreate(ProductModelBase):
    """Create product model request"""

    pass


class ProductModelResponse(ProductModelBase):
    """Product model response"""

    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductColorBase(BaseModel):
    """Base product color schema"""

    name: str


class ProductColorCreate(ProductColorBase):
    """Create product color request"""

    pass


class ProductColorResponse(ProductColorBase):
    """Product color response"""

    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierBase(BaseModel):
    """Base supplier schema"""

    name: str


class SupplierCreate(SupplierBase):
    """Create supplier request"""

    pass


class SupplierUpdate(BaseModel):
    """Update supplier request"""

    name: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Supplier response"""

    id: int
    is_active: bool
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
