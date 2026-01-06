# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo for a shipment tracking web application that monitors garment shipments from manufacturers to warehouses. The application uses a FastAPI backend and React frontend with Tailwind CSS for styling.

### Business Problem

Suppliers don't know where goods are located. Goods can get lost or not arrive at their destination. A system is needed to determine the shipment status at any given time.

### Solution

Create a QR code-based tracking system where users scan QR codes in PDF reports to check and update shipment status. The system serves three user types:
1. **Цех (Factory/Supplier)** - First point in the chain, produces clothing and sends to fulfillment
2. **Фулфилмент (Fulfillment Center)** - Receives and stores goods from factory, sorts, labels, packages and sends to cargo for shipment to Russia and other countries
3. **Водитель (Driver)** - Receives goods from cargo and delivers to destination, checks integrity of delivered goods

### Workflow

1. User scans QR code → redirected to `www.*website-name*.com/shipment/[shipment_id]`
2. User must login first (authentication required)
3. After login, user can view shipment details and click "Подтвердить" (Confirm) button to change status
4. Status changes are logged with user information and timestamp
5. Notifications sent via Telegram and email when status changes

## Project Structure

```
shipment-tracker/
├── apps/
│   ├── backend/          # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/   # API version 1 endpoints (empty, ready for development)
│   │   │   ├── core/     # Core configuration and utilities
│   │   │   ├── schemas/  # Pydantic schemas
│   │   │   ├── services/ # Business logic services
│   │   │   └── main.py   # FastAPI app entry point
│   │   ├── utils/        # Utility scripts (e.g., hash_pass.py for bcrypt)
│   │   ├── tests/        # Backend tests
│   │   └── .venv/        # Python virtual environment
│   └── frontend/         # React + TypeScript + Vite frontend
│       ├── src/
│       │   ├── App.tsx   # Main application component (shipment tracker UI)
│       │   ├── main.tsx  # React entry point
│       │   ├── index.css # Tailwind source
│       │   └── tw.css    # Generated Tailwind output
│       └── index.html    # HTML entry point
```

## Development Commands

### Backend (FastAPI)

The backend is located in `apps/backend/`.

**Setup:**
```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/macOS
pip install -r requirements.txt
```

**Run development server:**
```bash
cd apps/backend
uvicorn app.main:app --reload
```

The backend runs on default uvicorn port (typically http://localhost:8000).

**Database setup (PostgreSQL):**
```bash
# Install PostgreSQL if not already installed
# Create database for the project
# Update database connection string in backend configuration
# Run migrations (to be implemented)
```

**Run tests (when implemented):**
```bash
cd apps/backend
pytest
```

**API Endpoints (To Be Implemented):**

Authentication & User Management:
- `GET /login?next=<redirect>` - Login page (with optional redirect after login)
- `POST /api/login/` - Authenticate user and return JWT token
- `GET /forgot-password/` - Password reset request page
- `POST /api/request-password/` - Request password reset email
- `POST /api/change-password/` - Change user password
- `POST /api/logout/` - Logout and invalidate JWT token

Shipment Tracking:
- `GET /shipment/{shipment_id}` - Shipment detail page (requires authentication)
- `GET /api/shipment/{shipment_id}` - Get shipment data as JSON
- `POST /api/confirm/` - Confirm and update shipment status (logs user action)

Current Placeholder Endpoints:
- `POST /api/v1/login` - Returns "Test" (to be replaced)
- `GET /shipments/{shipment_id}` - Returns hardcoded shipment (to be replaced)

### Frontend (React + Vite)

The frontend is located in `apps/frontend/`.

**Install dependencies:**
```bash
cd apps/frontend
npm install
```

**Run development server:**
```bash
cd apps/frontend
npm run dev
```

**Build for production:**
```bash
cd apps/frontend
npm run build
```

**Preview production build:**
```bash
cd apps/frontend
npm run preview
```

**Tailwind CSS:**

The project uses Tailwind CSS v4 via CLI. The source file is `src/index.css` and it outputs to `src/tw.css`.

- **Development (watch mode):**
  ```bash
  npm run tw:dev
  ```

- **Build (minified):**
  ```bash
  npm run tw:build
  ```

Note: The build script (`npm run build`) automatically runs `tw:build` before building the React app.

**Linting:**
```bash
cd apps/frontend
npx eslint .
```

## Architecture Notes

### Backend Architecture

- **Framework:** FastAPI with Python
- **Structure:** The backend follows a modular architecture with separation of concerns:
  - `api/v1/` - API route handlers (currently empty, ready for expansion)
  - `core/` - Configuration, database, and core utilities
  - `schemas/` - Pydantic models for request/response validation
  - `services/` - Business logic layer
- **Current State:** Basic setup with placeholder endpoints in `main.py`. The structured directories exist but are not yet populated, indicating the app is in early development.
- **Authentication:** Uses bcrypt for password hashing (see `utils/hash_pass.py`)

### Frontend Architecture

- **Framework:** React 19 with TypeScript
- **Build Tool:** Vite 7
- **Styling:** Tailwind CSS v4 (CLI-based, not PostCSS plugin)
- **Animations:** Framer Motion
- **Icons:** Lucide React
- **Architecture Pattern:** Single-component application in `App.tsx` containing:
  - Auth system using localStorage (`ne_auth` key)
  - Role-based UI (поставщик/supplier, фуллфилмент/ff, водитель/driver, склад/warehouse)
  - Shipment tracking with three stages:
    1. `SENT_FROM_FACTORY` - From supplier
    2. `SHIPPED_FROM_FF` - From fulfillment center
    3. `DELIVERED` - To warehouse
  - Status progression tracking system
  - URL query parameter support for role selection

### Shipment Status Flow

The system tracks garment shipments through three stages:

**Stage 1: SENT_FROM_FACTORY (Поставщик - Supplier/Factory)**
- Role: Цех (Factory)
- Action: Factory produces clothing and confirms shipment to fulfillment
- Status Label: "Отправлено от Поставщика" (Sent from Supplier)
- Icon: CheckCircle2

**Stage 2: SHIPPED_FROM_FF (Фулфилмент - Fulfillment Center)**
- Role: Фулфилмент (Fulfillment)
- Action: Fulfillment receives, sorts, labels, packages goods and confirms shipment to cargo
- Status Label: "Отправлено из Фулфилмента" (Shipped from Fulfillment)
- Icon: PackageCheck

**Stage 3: DELIVERED (Склад - Warehouse/Driver)**
- Role: Водитель (Driver)
- Action: Driver receives from cargo, verifies integrity, and confirms delivery to destination
- Status Label: "Доставлено" (Delivered)
- Icon: Warehouse

Each role can only update the status for their stage by clicking "Подтвердить" (Confirm).

### Key Implementation Details

1. **Monorepo Layout:** Frontend and backend are separate apps that can be developed independently
2. **Russian Language UI:** The frontend uses Russian labels and messaging
3. **Status Flow:** Shipments progress through factory → fulfillment → warehouse stages
4. **Role-based Views:** Different user roles see different UI states based on their permissions
5. **Local Storage Auth:** Currently using localStorage for authentication (mock implementation noted in code)

## Tech Stack

**Backend:**
- FastAPI - Web framework
- Python - Programming language (with virtual environment)
- PostgreSQL - Database for authentication, user logs, and shipment data
- JWT (JSON Web Tokens) - Authentication and authorization
- bcrypt - Password hashing
- Google Sheets API - Integration with existing shipment data
- Telegram Bot API - Instant notifications on status changes
- SendGrid - Email notifications via noreply@novaeris.net

**Frontend:**
- React 19.1
- TypeScript 5.6
- Vite 7.1
- Tailwind CSS 4.1 (CLI)
- Framer Motion 12.23
- Lucide React 0.546
- ESLint with typescript-eslint

**Deployment:**
- Railway - Backend hosting platform
- GitHub - Version control and code repository

## Project Requirements & Features

### Core Features (Required)

1. **PostgreSQL Database Setup**
   - Separate database for authentication (login, password)
   - User logs table (track who logged in and when they clicked confirm)
   - Role-based user system (Factory, Fulfillment, Driver)
   - Shipment status tracking

2. **API Development**
   - Implement all authentication endpoints with JWT
   - Implement shipment tracking endpoints
   - All endpoints must be properly secured with JWT authentication

3. **Google Sheets Integration**
   - Retrieve shipment data from existing Google Sheets database
   - Status changes must sync bidirectionally (DB ↔ Google Sheets)
   - Google Sheets acts as a data source and must stay updated

4. **Telegram Notifications**
   - Instant notifications to users when shipment status changes
   - Integration with Telegram Bot API

5. **Email Notifications (SendGrid)**
   - Send emails via noreply@novaeris.net
   - Password reset confirmation emails
   - Shipment status change notifications

6. **Authentication & Security**
   - JWT token-based authentication system
   - Password hashing with bcrypt
   - Secure role-based access control
   - Login redirect functionality (`/login?next=<url>`)

7. **Deployment**
   - Deploy backend to Railway platform
   - GitHub repository with proper version control

### Optional Features

- Separate dev and prod branches
- Unit tests (recommended)
- Frontend-backend API integration

## Important Implementation Notes

### User Registration

**CRITICAL:** User registration strategy is not yet finalized. The system must prevent unauthorized third parties from changing shipment statuses. Therefore:
- Public registration page is questionable/not recommended
- Consider pre-creating accounts for authorized users only
- May integrate with Telegram bot for user verification before account creation

### Data Flow Architecture

There's a proposal for a unified database architecture:
- Telegram bot → Common Database → Google Sheets + Tracking System
- This ensures all data flows through a single source of truth
- Status changes propagate to all systems (DB, Sheets, notifications)

### User Action Logging

Every status change must log:
- Which user made the change
- Timestamp of the change
- What status was changed (from → to)
- Store in user_logs table for audit trail

### Russian Language

- UI is in Russian (Русский язык)
- All user-facing text should be in Russian
- Status labels, button text, notifications all in Russian

## Development Notes

- The backend is in early development with structure prepared but minimal implementation
- Frontend has a complete shipment tracking UI with role-based access
- Currently no database integration; shipments are hardcoded in `main.py`
- The app is set up for a Russian-speaking user base
- Code should be understandable and well-documented (team uses AI for development)
