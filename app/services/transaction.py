from sqlalchemy.orm import Session

from app.db.models import Transaction, UserZoneSession, Zone
from app.services.event import _resolve_zone


def record_transaction(
    db: Session,
    user_id: int,
    zone_id: str | None = None,
    zone_name: str | None = None,
    floor_id: int | None = None,
) -> bool:
    """Create a transaction record and mark current user-zone session as having a transaction."""
    zone: Zone | None = _resolve_zone(db, zone_id, zone_name, floor_id)
    if zone is None:
        return False

    txn = Transaction(user_id=user_id, zone_id=zone.id)
    db.add(txn)

    session = (
        db.query(UserZoneSession)
        .filter(UserZoneSession.user_id == user_id)
        .first()
    )
    if session and session.zone_id == zone.id:
        session.has_transaction = True

    db.commit()
    return True

