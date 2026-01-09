from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, date
from enum import Enum


class RouteType(str, Enum):
    """Shipment route types"""

    DIRECT = "DIRECT"
    VIA_FF = "VIA_FF"


class ShipmentStatus(str, Enum):
    """Shipment status stages"""

    SENT_FROM_FACTORY = "SENT_FROM_FACTORY"
    SHIPPED_FROM_FF = "SHIPPED_FROM_FF"
    DELIVERED = "DELIVERED"


class BagItemInfo(BaseModel):
    """Individual item within a bag"""

    model: str
    color: str
    sizes: Dict[str, int]  # {"S": 10, "M": 20, "L": 15}


class BagInfo(BaseModel):
    """Individual bag information"""

    bag_id: str
    items: List['BagItemInfo']  # List of items in the bag


class ShipmentTotals(BaseModel):
    """Shipment totals"""

    bags: int
    pieces: int


class ShipmentCreate(BaseModel):
    """Create shipment request"""

    supplier: str
    warehouse: str
    route_type: RouteType
    shipment_date: Optional[date] = None
    bags_data: List[BagInfo]


class ShipmentDetail(BaseModel):
    """Shipment detail object matching frontend expectations"""

    id: str
    supplier: str
    warehouse: str
    route_type: str
    shipment_date: Optional[str] = None  # ISO format date string
    current_status: Optional[str] = None
    bags: List[Dict]  # List of bag objects
    totals: Dict[str, int]  # {"bags": 3, "pieces": 81}


class StatusHistoryItem(BaseModel):
    """Individual status change record"""

    id: int
    status: str
    changed_by: str  # Username
    changed_at: str  # ISO format datetime string
    notes: Optional[str] = None


class ShipmentResponse(BaseModel):
    """Shipment response matching frontend expectations"""

    shipment: Dict  # Complete shipment object
    events: List[Dict]  # Status history


class StatusUpdateRequest(BaseModel):
    """Status update request from frontend"""

    action: ShipmentStatus


class StatusHistoryResponse(BaseModel):
    """Status history response"""

    id: int
    status: str
    changed_by: str  # Username
    changed_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ShipmentListItem(BaseModel):
    """Shipment list item for dashboard/list views"""

    id: str
    supplier: str
    warehouse: str
    shipment_date: Optional[date] = None
    current_status: Optional[str] = None
    total_bags: int
    total_pieces: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShipmentUpdate(BaseModel):
    """Update shipment request (all fields optional)"""

    supplier: Optional[str] = None
    warehouse: Optional[str] = None
    route_type: Optional[RouteType] = None
    shipment_date: Optional[date] = None
    bags_data: Optional[List[BagInfo]] = None
