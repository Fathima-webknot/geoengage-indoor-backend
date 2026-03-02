from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.schemas.event import EventRequest
from app.services.event import record_event_and_maybe_notify

router = APIRouter(tags=["User (Android)"], prefix="")


@router.post(
    "/event",
    response_model=dict,
    summary="Zone entry event",
    description="Log zone entry and trigger FCM if active campaign. Use zone_id (UUID string) or (zone_name + floor_id).",
)
def post_event(
    body: EventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success, notification_sent, message = record_event_and_maybe_notify(
        db,
        current_user.id,
        zone_id=body.zone_id,
        zone_name=body.zone_name,
        floor_id=body.floor_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")
    if notification_sent and message:
        return {
            "success": True,
            "notification_sent": True,
            "campaign_message": message,
        }
    return {
        "success": True,
        "notification_sent": False,
        "message": "Event logged, no active campaign",
    }
