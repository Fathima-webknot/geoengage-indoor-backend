from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.db.models import Campaign
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.services.campaign import create_campaign, set_campaign_active, list_campaigns

router = APIRouter(tags=["Admin (Web)"], prefix="/campaigns")


@router.post(
    "",
    response_model=CampaignResponse,
    summary="Create campaign",
    description="Create a new campaign for a zone.",
)
def create(
    body: CampaignCreate,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    c = create_campaign(db, body.zone_id, body.message)
    return CampaignResponse(
        id=c.id,
        zone_id=c.zone_id,
        message=c.message,
        active=c.active,
        created_at=c.created_at.isoformat(),
    )


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Activate/deactivate campaign",
    description="Only one active campaign per zone. Activating deactivates others.",
)
def update(
    campaign_id: int,
    body: CampaignUpdate,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    c = set_campaign_active(db, campaign_id, body.active)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse(
        id=c.id,
        zone_id=c.zone_id,
        message=c.message,
        active=c.active,
        created_at=c.created_at.isoformat(),
    )


@router.get(
    "",
    response_model=list[CampaignResponse],
    summary="List campaigns",
    description="Optional filter by zone_id.",
)
def list_all(
    zone_id: int | None = None,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    campaigns = list_campaigns(db, zone_id)
    return [
        CampaignResponse(
            id=c.id,
            zone_id=c.zone_id,
            message=c.message,
            active=c.active,
            created_at=c.created_at.isoformat(),
        )
        for c in campaigns
    ]
