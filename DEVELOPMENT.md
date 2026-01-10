# Development Setup Guide

This guide explains how to run the shipment tracker locally for development.

## Prerequisites

- **Node.js 20+** (for frontend)
- **Python 3.11+** (for backend)
- **PostgreSQL 16+** (for database)

## Backend Setup

### 1. Create Virtual Environment

```bash
cd apps/backend
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Unix/macOS:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set your values:
- `DATABASE_URL` - Your local PostgreSQL connection string
- `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `BACKEND_CORS_ORIGINS` - Set to `["http://localhost:5173"]` for local frontend

### 5. Set Up Database

Make sure PostgreSQL is running, then:

```bash
# Create database
createdb shipment_tracker

# Run migrations
alembic upgrade head
```

### 6. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Frontend Setup

### 1. Install Dependencies

```bash
cd apps/frontend
npm install
```

### 2. Environment Variables

The `.env.development` file is already configured to use `http://localhost:8000` for the backend.

### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

## How Environment Variables Work

### Frontend (Vite)

- **Development:** Uses `.env.development` (localhost:8000)
  - Run with: `npm run dev`
  - Uses: `VITE_API_BASE_URL=http://localhost:8000`

- **Production:** Uses `.env.production` (api.novaeris.net)
  - Run with: `npm run build`
  - Uses: `VITE_API_BASE_URL=https://api.novaeris.net`

Vite automatically picks the right file based on the command you run.

### Backend (FastAPI)

- Uses environment variables from `.env` file (local development)
- In production (Railway), uses Railway environment variables
- Falls back to defaults in `app/core/config.py`

## Common Issues

### Backend can't connect to database
- Make sure PostgreSQL is running
- Check `DATABASE_URL` in `.env` is correct
- Verify database exists: `psql -l`

### Frontend gets CORS errors
- Make sure backend `BACKEND_CORS_ORIGINS` includes `http://localhost:5173`
- Restart backend after changing `.env`

### "Module not found" errors
- Backend: Make sure virtual environment is activated
- Frontend: Run `npm install`

## Production Deployment

See `CLAUDE.md` for production deployment instructions to Railway.

**Key differences:**
- Backend uses Railway PostgreSQL database
- Frontend uses Railway's build environment variables
- HTTPS everywhere
- Proxy headers trusted for correct redirects
