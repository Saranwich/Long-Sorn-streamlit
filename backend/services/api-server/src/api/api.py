# @track_context("api_setup.md")

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Supabase Auth API",
    description="Production-ready authentication API with Supabase",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}
