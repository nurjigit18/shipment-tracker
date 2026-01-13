from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...core.database import get_db
from ...core.dependencies import get_current_user, require_role, get_current_organization_id
from ...services.organization_service import OrganizationService
from ...schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationWithStats,
)
from ...models.organization import Organization

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "owner"])),
):
    """
    List all organizations (admin and owner only).

    Args:
        db: Database session
        current_user: Current authenticated user (must be admin or owner)

    Returns:
        List of all organizations

    Raises:
        HTTPException 403: If user is not admin or owner
    """
    result = await db.execute(select(Organization).order_by(Organization.name))
    organizations = result.scalars().all()

    return [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            created_at=org.created_at,
            updated_at=org.updated_at
        )
        for org in organizations
    ]


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    """
    Create new organization (admin only).

    Args:
        org_data: Organization creation data
        db: Database session
        current_user: Current authenticated user (must be admin)

    Returns:
        Created organization

    Raises:
        HTTPException 400: If organization name already exists
        HTTPException 403: If user is not admin
    """
    return await OrganizationService.create_organization(db, org_data)


@router.get("/me", response_model=OrganizationWithStats)
async def get_my_organization(
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's organization with statistics.

    Returns organization data including:
    - Organization details
    - Total user count
    - Total shipment count

    Args:
        organization_id: Organization ID from current user (extracted from JWT)
        db: Database session

    Returns:
        Organization with statistics
    """
    return await OrganizationService.get_organization_with_stats(db, organization_id)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    """
    Get organization by ID (admin only).

    Args:
        org_id: Organization ID
        db: Database session
        current_user: Current authenticated user (must be admin)

    Returns:
        Organization data

    Raises:
        HTTPException 404: If organization not found
        HTTPException 403: If user is not admin
    """
    return await OrganizationService.get_organization(db, org_id)
