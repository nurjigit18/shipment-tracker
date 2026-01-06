from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.user import UserLogin, Token, UserResponse
from ...services.auth_service import AuthService
from ...services.user_log_service import UserLogService
from ...models.user import User

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Args:
        login_data: Username and password
        request: FastAPI request object (for logging IP, user agent)
        db: Database session

    Returns:
        Token with access_token and user info

    Raises:
        HTTPException 401: If credentials are invalid
    """
    token = await AuthService.authenticate_user(db, login_data)

    # Log login action
    await UserLogService.log_action(
        db,
        user_id=token.user.id,
        action="login",
        details={
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )

    return token


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Logout user (client should discard token).

    Note: JWT tokens are stateless, so logout is client-side only.
    We just log the action for audit purposes.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    await UserLogService.log_action(db, user_id=current_user.id, action="logout")

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        User information (id, username, role)
    """
    return UserResponse(
        id=current_user.id, username=current_user.username, role=current_user.role.name
    )
