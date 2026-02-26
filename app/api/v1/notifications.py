from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.schemas.notification import NotificationClickRequest
from app.services.notification import list_notifications_for_user, record_click

router = APIRouter(tags=["User (Android)"], prefix="")


@router.get(
    "/notifications",
    summary="Notification history",
    description="Paginated list with zone_name and clicked.",
)
def get_notifications(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_notifications_for_user(
        db, current_user.id, limit=limit, offset=offset
    )


@router.post(
    "/notification-click",
    summary="Record notification tap",
    description="Track click for CTR analytics.",
)
def notification_click(
    body: NotificationClickRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = record_click(db, current_user.id, body.campaign_id)
    return {"success": ok}
