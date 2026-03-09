import uuid

from sqlalchemy.orm import Session

from app.db.models import (
    Event,
    Campaign,
    Notification,
    User,
    Zone,
    Floor,
    UserZoneSession,
)
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


def send_floor_entry_notification(
    db: Session,
    user_id: int,
    floor_id: int,
) -> tuple[bool, bool, str | None]:
    """Send floor entry notification without saving to database."""
    floor = db.query(Floor).filter(Floor.floor_id == floor_id).first()
    if not floor:
        return False, False, None

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.fcm_token:
        return True, False, None

    message = f"Welcome to {floor.floor_name}!"
    try:
        send_fcm_to_token(user.fcm_token, "GeoEngage", message)
        return True, True, message
    except Exception as e:
        print(f"Failed to send floor notification: {e}")
        return True, False, None


def record_event_and_maybe_notify(
    db: Session,
    user_id: int,
    zone_id: str | None = None,
    zone_name: str | None = None,
    floor_id: int | None = None,
) -> tuple[bool, bool, str | None]:
    """Handle zone entry with campaign notification and database record."""
    zone = _resolve_zone(db, zone_id, zone_name, floor_id)
    if zone is None:
        return False, False, None

    event = Event(user_id=user_id, zone_id=zone.id)
    db.add(event)

    # Upsert current user-zone session (one active session per user)
    session = (
        db.query(UserZoneSession)
        .filter(UserZoneSession.user_id == user_id)
        .first()
    )
    if session is None:
        session = UserZoneSession(user_id=user_id, zone_id=zone.id)
        db.add(session)
    else:
        session.zone_id = zone.id
        session.has_transaction = False
    db.commit()

    campaign = (
        db.query(Campaign)
        .filter(
            Campaign.zone_id == zone.id,
            Campaign.trigger == "zone_entry",
            Campaign.active.is_(True),
        )
        .first()
    )
    if not campaign:
        return True, False, None

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.fcm_token:
        return True, False, None

    # Create notification record first to get ID
    notif = Notification(
        user_id=user_id,
        campaign_id=campaign.id,
        status="failed",
        fcm_message_id=None,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Prepare data payload for FCM
    fcm_data = {
        "campaign_id": str(campaign.id),
        "notification_id": str(notif.id),
        "zone_name": zone.name,
        "offer_name": campaign.name or "",
        "type": "zone_entry"
    }

    status = "failed"
    fcm_message_id = None
    try:
        fcm_message_id = send_fcm_to_token(
            user.fcm_token, "GeoEngage", campaign.message, data=fcm_data
        )
        status = "sent"
    except Exception:
        pass

    # Update notification with FCM result
    notif.status = status
    notif.fcm_message_id = fcm_message_id
    db.commit()
    return True, status == "sent", campaign.message


def handle_zone_exit_and_maybe_notify(
    db: Session,
    user_id: int,
    zone_id: str | None = None,
    zone_name: str | None = None,
    floor_id: int | None = None,
) -> tuple[bool, bool, str | None]:
    """Handle zone exit with optional exit-without-transaction notification."""
    zone = _resolve_zone(db, zone_id, zone_name, floor_id)
    if zone is None:
        return False, False, None

    session = (
        db.query(UserZoneSession)
        .filter(UserZoneSession.user_id == user_id)
        .first()
    )
    if session is None or session.zone_id != zone.id:
        # No active session or different zone: nothing to do
        return True, False, None

    # If a transaction happened in this session, do not notify
    if session.has_transaction:
        db.delete(session)
        db.commit()
        return True, False, None

    # No transaction: try to send exit-without-transaction campaign
    campaign = (
        db.query(Campaign)
        .filter(
            Campaign.zone_id == zone.id,
            Campaign.trigger == "zone_exit_no_txn",
            Campaign.active.is_(True),
        )
        .first()
    )
    if not campaign:
        db.delete(session)
        db.commit()
        return True, False, None

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.fcm_token:
        db.delete(session)
        db.commit()
        return True, False, None

    notif = Notification(
        user_id=user_id,
        campaign_id=campaign.id,
        status="failed",
        fcm_message_id=None,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    fcm_data = {
        "campaign_id": str(campaign.id),
        "notification_id": str(notif.id),
        "zone_name": zone.name,
        "offer_name": campaign.name or "",
        "type": "zone_exit_no_txn",
    }

    status = "failed"
    fcm_message_id = None
    try:
        fcm_message_id = send_fcm_to_token(
            user.fcm_token, "GeoEngage", campaign.message, data=fcm_data
        )
        status = "sent"
    except Exception:
        pass

    notif.status = status
    notif.fcm_message_id = fcm_message_id
    db.delete(session)
    db.commit()
    return True, status == "sent", campaign.message
