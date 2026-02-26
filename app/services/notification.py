from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Notification, Campaign, Zone


def list_notifications_for_user(
    db: Session, user_id: int, limit: int = 50, offset: int = 0
) -> list[dict]:
    rows = (
        db.query(Notification, Campaign.message, Zone.name.label("zone_name"))
        .join(Campaign, Notification.campaign_id == Campaign.id)
        .join(Zone, Campaign.zone_id == Zone.id)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        {
            "id": n.id,
            "campaign_id": n.campaign_id,
            "message": message,
            "zone_name": zone_name,
            "created_at": n.created_at,
            "clicked": n.clicked_at is not None,
        }
        for n, message, zone_name in rows
    ]


def record_click(db: Session, user_id: int, campaign_id: int) -> bool:
    n = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.campaign_id == campaign_id,
        )
        .order_by(Notification.created_at.desc())
        .first()
    )
    if not n:
        return False
    n.clicked_at = datetime.now(timezone.utc)
    db.commit()
    return True
