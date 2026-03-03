from fastapi import APIRouter

from app.api.v1 import auth, events, campaigns, notifications, analytics, zones, floors

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(auth.admin_router)
api_router.include_router(events.router)
api_router.include_router(campaigns.router)
api_router.include_router(notifications.router)
api_router.include_router(analytics.router)
api_router.include_router(zones.router)
api_router.include_router(floors.router)
