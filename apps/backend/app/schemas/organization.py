from pydantic import BaseModel, Field
from datetime import datetime


class OrganizationBase(BaseModel):
    """Base organization schema"""

    name: str = Field(..., min_length=1, max_length=200, description="Organization name")


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""

    pass


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithStats(OrganizationResponse):
    """Organization with statistics (user count, shipment count)"""

    total_users: int = 0
    total_shipments: int = 0
