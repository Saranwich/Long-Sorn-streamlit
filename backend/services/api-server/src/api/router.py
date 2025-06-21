# @track_context("api_setup.md")

from fastapi import APIRouter

from src.api.endpoints import auth, videos

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])