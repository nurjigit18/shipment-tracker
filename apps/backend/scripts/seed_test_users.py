"""
Seed script to create test users for each role.

Creates test users:
- test_supplier (password: test123)
- test_ff (password: test123)
- test_driver (password: test123)

Usage:
    python scripts/seed_test_users.py
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
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.organization import Organization


async def seed_test_users():
    """Create test users if they don't exist"""
    async with AsyncSessionLocal() as db:
        # Get Default Company organization
        result = await db.execute(
            select(Organization).where(Organization.name == "Default Company")
        )
        default_org = result.scalar_one_or_none()

        if not default_org:
            print("ERROR: Default Company not found. Please run migration first.")
            return

        default_org_id = default_org.id

        # Get roles
        result = await db.execute(select(Role))
        roles = {role.name: role.id for role in result.scalars().all()}

        if not all(r in roles for r in ["supplier", "ff", "driver"]):
            print("ERROR: Required roles not found. Please run seed_roles.py first.")
            return

        # Define test users with organization
        test_users = [
            {
                "username": "test_supplier",
                "password": "test123",
                "role": "supplier",
                "organization_id": default_org_id,
            },
            {
                "username": "test_ff",
                "password": "test123",
                "role": "ff",
                "organization_id": default_org_id,
            },
            {
                "username": "test_driver",
                "password": "test123",
                "role": "driver",
                "organization_id": default_org_id,
            },
        ]

        # Check existing users
        result = await db.execute(select(User))
        existing_usernames = {user.username for user in result.scalars().all()}

        print(f"Existing users: {existing_usernames}\n")

        # Create missing test users
        created_count = 0
        for user_data in test_users:
            if user_data["username"] not in existing_usernames:
                user = User(
                    username=user_data["username"],
                    password_hash=get_password_hash(user_data["password"]),
                    role_id=roles[user_data["role"]],
                    organization_id=user_data["organization_id"],
                )
                db.add(user)
                created_count += 1
                print(f"Creating user: {user_data['username']} (role: {user_data['role']}, org: Default Company)")
            else:
                print(f"User already exists: {user_data['username']}")

        if created_count > 0:
            await db.commit()
            print(f"\n✓ Created {created_count} test user(s)")
            print("\nTest credentials:")
            print("  Username: test_supplier | Password: test123")
            print("  Username: test_ff       | Password: test123")
            print("  Username: test_driver   | Password: test123")
        else:
            print("\n✓ All test users already exist")


if __name__ == "__main__":
    print("=== Seeding Test Users ===\n")
    asyncio.run(seed_test_users())
