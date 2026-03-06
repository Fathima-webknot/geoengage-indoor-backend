import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.models import Campaign


def create_campaign(
    db: Session,
    zone_id: uuid.UUID,
    message: str,
    trigger: str = "zone_entry",
    name: str | None = None,
) -> Campaign:
    c = Campaign(zone_id=zone_id, message=message, trigger=trigger, name=name)
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
            update(Campaign)
            .where(
                Campaign.zone_id == c.zone_id,
                Campaign.trigger == c.trigger,
            )
            .values(active=False)
        )
    c.active = active
    db.commit()
    db.refresh(c)
    return c


def list_campaigns(
    db: Session,
    zone_id: uuid.UUID | None = None,
    trigger: str | None = None,
) -> list[Campaign]:
    q = db.query(Campaign)
    if zone_id is not None:
        q = q.filter(Campaign.zone_id == zone_id)
    if trigger is not None and trigger.strip() != "":
        q = q.filter(Campaign.trigger == trigger)
    return list(q.all())


def delete_campaign(db: Session, campaign_id: int) -> bool:
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        return False
    db.delete(c)
    db.commit()
    return True
