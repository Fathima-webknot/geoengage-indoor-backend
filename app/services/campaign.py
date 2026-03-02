import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.models import Campaign


def create_campaign(db: Session, zone_id: uuid.UUID, message: str) -> Campaign:
    c = Campaign(zone_id=zone_id, message=message)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def set_campaign_active(db: Session, campaign_id: int, active: bool) -> Campaign | None:
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        return None
    if active:
        db.execute(
            update(Campaign).where(Campaign.zone_id == c.zone_id).values(active=False)
        )
    c.active = active
    db.commit()
    db.refresh(c)
    return c


def list_campaigns(
    db: Session, zone_id: uuid.UUID | None = None
) -> list[Campaign]:
    q = db.query(Campaign)
    if zone_id is not None:
        q = q.filter(Campaign.zone_id == zone_id)
    return list(q.all())
