from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from .database import get_db
from .security import decode_access_token

# Import models (will be available after models are created)
# from ..models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Extract and validate current user from JWT token with organization validation.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object from database with role and organization loaded

    Raises:
        HTTPException 401: If token is invalid, user not found, or organization mismatch
    """
    # Import here to avoid circular imports
    from ..models.user import User

    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user_id and organization_id from token
    user_id: int = payload.get("user_id")
    organization_id: int = payload.get("organization_id")

    # CRITICAL: Validate both user_id and organization_id are present
    if user_id is None or organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Eagerly load role AND organization relationships to avoid lazy loading issues
    # Use joinedload to fetch everything in ONE query instead of 3 separate queries
    from sqlalchemy.orm import joinedload

    result = await db.execute(
        select(User)
        .options(joinedload(User.role), joinedload(User.organization))
        .where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # CRITICAL: Validate organization_id in token matches user's organization_id
    if user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Organization mismatch in token",
        )

    return user


def require_role(required_roles: List[str]):
    """
    Dependency factory for role-based access control.

    Args:
        required_roles: List of role names that are allowed

    Returns:
        Async dependency function that validates user role

    Raises:
        HTTPException 403: If user's role is not in required_roles

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
    """

    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role.name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )
        return current_user

    return role_checker


def get_current_organization_id(current_user=Depends(get_current_user)) -> int:
    """
    Extract organization ID from current user.

    Args:
        current_user: Current authenticated user

    Returns:
        Organization ID of the current user
    """
    return current_user.organization_id
