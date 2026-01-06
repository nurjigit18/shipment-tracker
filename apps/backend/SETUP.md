# Backend Setup Guide

## What's Been Implemented

✅ All dependencies installed (FastAPI, SQLAlchemy, psycopg, Alembic, JWT, bcrypt)
✅ Core configuration (config.py, database.py, security.py)
✅ Database models (User, Role, Shipment, ShipmentStatusHistory, UserLog)
✅ Pydantic schemas for request/response validation
✅ Service layer (AuthService, ShipmentService, UserLogService)
✅ API endpoints (auth and shipments)
✅ Main application with CORS configured
✅ Alembic configured for async migrations
✅ Seed scripts for roles, test users, and test shipment

## Next Steps

### 1. Create .env File

Copy the `.env.example` file and create `.env` with your Railway database credentials:

```bash
cd apps/backend
cp .env.example .env
```

Edit `.env` and update these values:

```env
# Get this from your Railway PostgreSQL database
DATABASE_URL=postgresql+psycopg://user:password@host:port/database

# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-generated-secret-key-here

# Your frontend URL
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

**Important:** The DATABASE_URL should use `postgresql+psycopg://` (not `postgresql+asyncpg://`)

### 2. Run Database Migrations

Create the new tables (shipments, user_logs, shipment_status_history):

```bash
cd apps/backend
alembic revision --autogenerate -m "Add shipment tracking tables"
alembic upgrade head
```

**⚠️ Important:** Before running the migration, review the generated migration file in `alembic/versions/` to ensure it:
- Only creates NEW tables (shipments, user_logs, shipment_status_history)
- Does NOT modify existing users or roles tables

### 3. Seed the Database

Run the seed scripts to populate roles and create test data:

```bash
# 1. Create roles (supplier, ff, driver - admin should already exist)
python scripts/seed_roles.py

# 2. Create test users (test_supplier, test_ff, test_driver)
python scripts/seed_test_users.py

# 3. Create a sample shipment
python scripts/seed_test_shipment.py
```

### 4. Start the Development Server

```bash
cd apps/backend
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with username/password, get JWT token
- `POST /api/auth/logout` - Logout (client discards token)
- `GET /api/auth/me` - Get current user info

### Shipments
- `GET /api/shipments/{shipment_id}` - Get shipment details
- `POST /api/shipments/{shipment_id}/events` - Update shipment status

## Testing the API

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_supplier", "password": "test123"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "test_supplier",
    "role": "supplier"
  }
}
```

### 2. Get Shipment
```bash
curl -X GET http://localhost:8000/api/shipments/S-2025-00123 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Update Status
```bash
curl -X POST http://localhost:8000/api/shipments/S-2025-00123/events \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"action": "SENT_FROM_FACTORY"}'
```

## Test Users

| Username | Password | Role | Can Confirm Status |
|----------|----------|------|-------------------|
| test_supplier | test123 | supplier | SENT_FROM_FACTORY |
| test_ff | test123 | ff | SHIPPED_FROM_FF |
| test_driver | test123 | driver | DELIVERED |

## Project Structure

```
apps/backend/
├── app/
│   ├── core/           # Configuration, database, security
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── api/v1/         # API endpoints
│   └── main.py         # FastAPI application
├── alembic/            # Database migrations
├── scripts/            # Seed scripts
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
└── .env                # Your configuration (create this)
```

## Database Schema

### Existing Tables (DO NOT MODIFY)
- **users** - id, username, password_hash, role_id, password
- **roles** - id, name

### New Tables (Created by Migration)
- **user_logs** - Track user actions (login, status confirmations)
- **shipments** - Core shipment data with JSONB bags
- **shipment_status_history** - Audit trail of status changes

## Key Features

✅ **Async PostgreSQL** - Using psycopg driver for better Windows compatibility
✅ **JWT Authentication** - Secure token-based auth with bcrypt password hashing
✅ **Role-Based Access Control** - Supplier, FF, Driver, Admin roles
✅ **Status Flow Validation** - Enforces correct status transitions
✅ **Audit Logging** - User actions logged to database
✅ **Idempotency** - Prevents duplicate status submissions
✅ **CORS** - Configured for frontend integration

## Troubleshooting

### Database Connection Error
- Verify DATABASE_URL in `.env` is correct
- Ensure Railway database is accessible
- Check firewall/network settings

### Import Errors
- Make sure you're in the `apps/backend` directory
- Virtual environment activated (if using venv)
- All dependencies installed: `pip install -r requirements.txt`

### Migration Issues
- Review generated migration before running
- Ensure existing users/roles tables are not modified
- Check Alembic revision history: `alembic history`

## What's Next?

After the basic setup works:
1. **Google Sheets Integration** - Sync shipment data bidirectionally
2. **Telegram Notifications** - Send status update notifications
3. **SendGrid Emails** - Password reset and status notifications
4. **Frontend Integration** - Connect React app to these endpoints
5. **Deploy to Railway** - Production deployment

All the infrastructure is in place - you just need to configure your Railway database and run the migrations!
