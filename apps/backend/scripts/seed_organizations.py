"""
Seed script to create organizations for multi-tenant testing.

Creates sample organizations:
- Default Company (already exists from migration)
- Test Company A
- Test Company B

Usage:
    python scripts/seed_organizations.py
"""

import asyncio
import sys
from pathlib import Path

# Fix for Windows: Use selector event loop instead of proactor
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization


async def seed_organizations():
    """Create organizations if they don't exist"""
    async with AsyncSessionLocal() as db:
        # Check existing organizations
        result = await db.execute(select(Organization))
        existing_orgs = {org.name for org in result.scalars().all()}

        print(f"Existing organizations: {existing_orgs}\n")

        # Define organizations to create
        organizations = [
            "Default Company",  # Created by migration
            "Test Company A",
            "Test Company B",
        ]

        # Create missing organizations
        created_count = 0
        for org_name in organizations:
            if org_name not in existing_orgs:
                org = Organization(name=org_name)
                db.add(org)
                created_count += 1
                print(f"Creating organization: {org_name}")
            else:
                print(f"Organization already exists: {org_name}")

        if created_count > 0:
            await db.commit()
            print(f"\n✓ Created {created_count} organization(s)")
        else:
            print("\n✓ All organizations already exist")


if __name__ == "__main__":
    print("=== Seeding Organizations ===\n")
    asyncio.run(seed_organizations())
