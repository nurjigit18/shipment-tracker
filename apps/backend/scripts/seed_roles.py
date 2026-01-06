"""
Seed script to populate roles table.

This script creates the required roles: supplier, ff, driver, admin (if not exists).
The 'admin' role should already exist in your database.

Usage:
    python scripts/seed_roles.py
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
from app.models.user import Role


async def seed_roles():
    """Create roles if they don't exist"""
    async with AsyncSessionLocal() as db:
        # Check existing roles
        result = await db.execute(select(Role))
        existing_roles = {role.name for role in result.scalars().all()}

        print(f"Existing roles: {existing_roles}")

        # Define required roles
        required_roles = ["admin", "supplier", "ff", "driver"]

        # Create missing roles
        created_count = 0
        for role_name in required_roles:
            if role_name not in existing_roles:
                role = Role(name=role_name)
                db.add(role)
                created_count += 1
                print(f"Creating role: {role_name}")
            else:
                print(f"Role already exists: {role_name}")

        if created_count > 0:
            await db.commit()
            print(f"\n✓ Created {created_count} new role(s)")
        else:
            print("\n✓ All roles already exist")


if __name__ == "__main__":
    print("=== Seeding Roles ===\n")
    asyncio.run(seed_roles())
