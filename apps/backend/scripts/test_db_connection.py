"""
Test database connection to Railway PostgreSQL.

This script verifies:
1. DATABASE_URL is configured correctly
2. Connection to PostgreSQL works
3. Existing tables are visible
4. You can query the database

Usage:
    python scripts/test_db_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Fix for Windows: Use selector event loop instead of proactor
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine


async def test_connection():
    """Test database connection and show existing tables"""

    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)

    # Show DATABASE_URL (masked for security)
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        # Mask password: postgresql+psycopg://user:***@host:port/db
        parts = db_url.split("@")
        user_part = parts[0].split("://")[1].split(":")[0]
        host_part = "@".join(parts[1:])
        masked_url = f"postgresql+psycopg://{user_part}:***@{host_part}"
    else:
        masked_url = db_url

    print(f"\n📍 Database URL: {masked_url}")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")

    try:
        # Test connection
        print("\n🔌 Testing connection...")
        async with AsyncSessionLocal() as db:
            # Test basic query
            result = await db.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected successfully!")
            print(f"📦 PostgreSQL Version: {version.split(',')[0]}")

            # List all tables
            print("\n📋 Existing tables in database:")
            result = await db.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.scalars().all()

            if tables:
                for table in tables:
                    print(f"   • {table}")
            else:
                print("   (No tables found)")

            # Check for required existing tables
            print("\n🔍 Checking for required existing tables:")
            required_tables = ["users", "roles"]
            for table_name in required_tables:
                if table_name in tables:
                    # Count rows in table
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"   ✅ {table_name}: {count} rows")
                else:
                    print(f"   ❌ {table_name}: NOT FOUND")

            # Check roles if table exists
            if "roles" in tables:
                print("\n👥 Roles in database:")
                result = await db.execute(text("SELECT id, name FROM roles ORDER BY name"))
                roles = result.all()
                if roles:
                    for role_id, role_name in roles:
                        print(f"   • {role_name} (id: {role_id})")
                else:
                    print("   (No roles found)")

            # Check users if table exists
            if "users" in tables:
                print("\n👤 Users in database:")
                result = await db.execute(text("""
                    SELECT u.id, u.username, r.name as role_name
                    FROM users u
                    LEFT JOIN roles r ON u.role_id = r.id
                    ORDER BY u.id
                """))
                users = result.all()
                if users:
                    for user_id, username, role_name in users:
                        print(f"   • {username} (role: {role_name}, id: {user_id})")
                else:
                    print("   (No users found)")

            # Check for new tables (that will be created by migration)
            print("\n🆕 Tables to be created by migration:")
            new_tables = ["shipments", "user_logs", "shipment_status_history"]
            for table_name in new_tables:
                if table_name in tables:
                    print(f"   ⚠️  {table_name}: ALREADY EXISTS (migration may skip)")
                else:
                    print(f"   📝 {table_name}: Will be created")

            print("\n" + "=" * 60)
            print("✅ DATABASE CONNECTION TEST PASSED")
            print("=" * 60)
            print("\nYou can now proceed with:")
            print("1. alembic revision --autogenerate -m 'Add shipment tracking tables'")
            print("2. alembic upgrade head")
            print("3. python scripts/seed_roles.py")
            print("4. python scripts/seed_test_users.py")
            print("5. python scripts/seed_test_shipment.py")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ DATABASE CONNECTION FAILED")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your .env file exists and has DATABASE_URL set")
        print("2. Verify DATABASE_URL format: postgresql+psycopg://user:pass@host:port/db")
        print("3. Ensure Railway database is accessible (check firewall/VPN)")
        print("4. Verify credentials are correct")
        print("\nExample DATABASE_URL:")
        print("DATABASE_URL=postgresql+psycopg://postgres:password@containers-us-west-123.railway.app:5432/railway")

        return False

    finally:
        # Close engine
        await engine.dispose()

    return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
