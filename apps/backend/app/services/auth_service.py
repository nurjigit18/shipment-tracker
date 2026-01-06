from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import timedelta

from ..models.user import User
from ..core.security import verify_password, create_access_token
from ..core.config import settings
from ..schemas.user import UserLogin, Token, UserResponse


class AuthService:
    """Authentication service handling user login and token generation"""

    @staticmethod
    async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> Token:
        """
        Authenticate user and return JWT token.

        Args:
            db: Database session
            login_data: Username and password

        Returns:
            Token object with access_token and user info

        Raises:
            HTTPException 401: If credentials are invalid
        """
        # Query user with role and organization relationships (eager loading)
        result = await db.execute(
            select(User)
            .options(selectinload(User.role), selectinload(User.organization))
            .where(User.username == login_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # Verify password using password_hash field
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # Create access token with organization_id (CRITICAL for multi-tenancy)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
                "role": user.role.name,
                "organization_id": user.organization_id,  # NEW - Critical for security
            },
            expires_delta=access_token_expires,
        )

        # Return token with user info including organization_id
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            role=user.role.name,
            organization_id=user.organization_id,
        )

        return Token(access_token=access_token, user=user_response)
