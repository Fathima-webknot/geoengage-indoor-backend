from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsResponse,
    ZoneEntryItem,
    TopZoneItem,
)
from app.services.analytics import get_analytics

router = APIRouter(tags=["Admin (Web)"], prefix="")


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Dashboard analytics",
    description="Zone entries, notifications sent, clicks, CTR, top zones by CTR.",
)
def analytics(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = get_analytics(db)
    return AnalyticsResponse(
        zone_entries=[
            ZoneEntryItem(zone=e["zone"], count=e["count"])
            for e in data["zone_entries"]
        ],
        notifications_sent=data["notifications_sent"],
        clicks=data["clicks"],
        ctr=data["ctr"],
        top_zones=[
            TopZoneItem(zone_name=t["zone_name"], ctr=t["ctr"])
            for t in data["top_zones"]
        ],
    )
