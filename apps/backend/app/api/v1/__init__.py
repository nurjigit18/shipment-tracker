"""API v1 routes combining all endpoint routers."""

from fastapi import APIRouter
from .auth import router as auth_router
from .shipments import router as shipments_router
from .organizations import router as organizations_router

api_router = APIRouter()

# Include sub-routers with their prefixes
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(shipments_router, prefix="/shipments", tags=["shipments"])
api_router.include_router(organizations_router, tags=["organizations"])
