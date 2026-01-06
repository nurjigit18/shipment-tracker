"""Core module containing configuration, database, security, and dependencies."""

from .config import settings
from .database import Base, engine, get_db, AsyncSessionLocal
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from .dependencies import get_current_user, require_role

__all__ = [
    "settings",
    "Base",
    "engine",
    "get_db",
    "AsyncSessionLocal",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "require_role",
]
