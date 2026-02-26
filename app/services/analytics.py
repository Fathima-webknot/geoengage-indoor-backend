from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Event, Zone, Notification, Campaign


def get_analytics(db: Session) -> dict:
    zone_entries = (
        db.query(Zone.name, func.count(Event.id).label("count"))
        .join(Event, Event.zone_id == Zone.id)
        .group_by(Zone.id, Zone.name)
        .all()
    )
    sent = db.query(Notification).filter(Notification.status == "sent").count()
    clicks = db.query(Notification).filter(
        Notification.clicked_at.isnot(None)
    ).count()
    total = db.query(Notification).count()
    ctr = (clicks / total) if total else 0.0

    top_zones_rows = (
        db.query(
            Zone.name,
            func.count(Notification.id).label("total"),
            func.count(Notification.clicked_at).label("clicks"),
        )
        .join(Campaign, Campaign.zone_id == Zone.id)
        .join(Notification, Notification.campaign_id == Campaign.id)
        .group_by(Zone.id, Zone.name)
        .all()
    )
    top_zones_list = [
        {
            "zone_name": name,
            "ctr": round((clicks_count / total_count) if total_count else 0.0, 4),
        }
        for name, total_count, clicks_count in top_zones_rows
    ]

    return {
        "zone_entries": [{"zone": name, "count": c} for name, c in zone_entries],
        "notifications_sent": sent,
        "clicks": clicks,
        "ctr": round(ctr, 4),
        "top_zones": top_zones_list,
    }
