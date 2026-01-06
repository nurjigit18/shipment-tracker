from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..models.organization import Organization
from ..models.user import User
from ..models.shipment import Shipment
from ..schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationWithStats,
)


class OrganizationService:
    """Service for managing organizations"""

    @staticmethod
    async def create_organization(
        db: AsyncSession, org_data: OrganizationCreate
    ) -> OrganizationResponse:
        """
        Create new organization.

        Args:
            db: Database session
            org_data: Organization creation data

        Returns:
            Created organization

        Raises:
            HTTPException 400: If organization name already exists
        """
        # Check if organization name already exists
        result = await db.execute(
            select(Organization).where(Organization.name == org_data.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists",
            )

        organization = Organization(name=org_data.name)
        db.add(organization)
        await db.commit()
        await db.refresh(organization)

        return OrganizationResponse.model_validate(organization)

    @staticmethod
    async def get_organization(
        db: AsyncSession, org_id: int
    ) -> OrganizationResponse:
        """
        Get organization by ID.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Organization data

        Raises:
            HTTPException 404: If organization not found
        """
        result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        return OrganizationResponse.model_validate(organization)

    @staticmethod
    async def get_organization_with_stats(
        db: AsyncSession, org_id: int
    ) -> OrganizationWithStats:
        """
        Get organization with statistics (user count, shipment count).

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Organization data with statistics

        Raises:
            HTTPException 404: If organization not found
        """
        org = await OrganizationService.get_organization(db, org_id)

        # Count users
        user_count_result = await db.execute(
            select(func.count(User.id)).where(User.organization_id == org_id)
        )
        user_count = user_count_result.scalar()

        # Count shipments
        shipment_count_result = await db.execute(
            select(func.count(Shipment.id)).where(Shipment.organization_id == org_id)
        )
        shipment_count = shipment_count_result.scalar()

        return OrganizationWithStats(
            **org.model_dump(),
            total_users=user_count or 0,
            total_shipments=shipment_count or 0,
        )
