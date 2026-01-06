from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from .config import settings

# Create async engine
# Note: Use postgresql+psycopg:// for async psycopg driver
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    if "postgresql+asyncpg://" in settings.DATABASE_URL
    else settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # SQL logging in dev
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session for each request.
    Automatically closes the session after the request is complete.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
