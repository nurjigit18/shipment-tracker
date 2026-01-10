from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title="Nova Eris Shipment Tracker API",
    description="Backend API for garment shipment tracking system",
    version="1.0.0",
    root_path="",  # Important for proxy setups
)

# Middleware to trust proxy headers (Railway/Cloudflare)
# This ensures FastAPI generates HTTPS URLs for redirects
@app.middleware("http")
async def trust_proxy_headers(request, call_next):
    # Trust X-Forwarded-Proto header from Railway/Cloudflare
    if "x-forwarded-proto" in request.headers:
        request.scope["scheme"] = request.headers["x-forwarded-proto"]
    response = await call_next(request)
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nova Eris Shipment Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/test/google-sheets")
async def test_google_sheets():
    """Test Google Sheets connection"""
    from app.services.google_sheets_service import sheets_service
    return sheets_service.test_connection()