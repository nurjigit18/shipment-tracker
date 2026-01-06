from pydantic import BaseModel, ConfigDict


class UserLogin(BaseModel):
    """Login request schema"""

    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema"""

    id: int
    username: str
    role: str  # Role name (supplier, ff, driver, admin)
    organization_id: int  # Organization ID for multi-tenant isolation

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data"""

    user_id: int
    username: str
    role: str
    organization_id: int  # Organization ID for multi-tenant isolation
