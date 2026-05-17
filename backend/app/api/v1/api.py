from fastapi import APIRouter

from app.api.v1.routers import health, live_interviews

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(live_interviews.router)
