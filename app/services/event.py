import uuid

from sqlalchemy.orm import Session

from app.db.models import Event, Campaign, Notification, User, Zone
from app.core.fcm import send_fcm_to_token


def _resolve_zone(
    db: Session,
    zone_id: str | None,
    zone_name: str | None,
    floor_id: int | None,
) -> Zone | None:
    if zone_id is not None and zone_id.strip() != "":
        try:
            zone_uuid = uuid.UUID(zone_id)
        except (ValueError, TypeError):
            return None
        return db.query(Zone).filter(Zone.id == zone_uuid).first()
    if zone_name is not None and floor_id is not None:
        return (
            db.query(Zone)
            .filter(Zone.floor_id == floor_id, Zone.name == zone_name)
            .first()
        )
    return None


def record_event_and_maybe_notify(
    db: Session,
    user_id: int,
    zone_id: str | None = None,
    zone_name: str | None = None,
    floor_id: int | None = None,
) -> tuple[bool, bool, str | None]:
    zone = _resolve_zone(db, zone_id, zone_name, floor_id)
    if zone is None:
        return False, False, None

    event = Event(user_id=user_id, zone_id=zone.id)
    db.add(event)
    db.commit()

    campaign = (
        db.query(Campaign)
        .filter(Campaign.zone_id == zone.id, Campaign.active.is_(True))
        .first()
    )
    if not campaign:
        return True, False, None

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.fcm_token:
        return True, False, None

    status = "failed"
    fcm_message_id = None
    try:
        fcm_message_id = send_fcm_to_token(
            user.fcm_token, "GeoEngage", campaign.message
        )
        status = "sent"
    except Exception:
        pass

    notif = Notification(
        user_id=user_id,
        campaign_id=campaign.id,
        status=status,
        fcm_message_id=fcm_message_id,
    )
    db.add(notif)
    db.commit()
    return True, status == "sent", campaign.message
