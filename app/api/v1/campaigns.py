import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.db.models import Campaign
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.services.campaign import create_campaign, set_campaign_active, list_campaigns, delete_campaign

router = APIRouter(tags=["Admin (Web)"], prefix="/campaigns")


@router.post(
    "",
    response_model=CampaignResponse,
    summary="Create campaign",
    description="Create a new campaign for a zone (zone_id = UUID string).",
)
def create(
    body: CampaignCreate,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        zone_uuid = uuid.UUID(body.zone_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid zone_id UUID")
    c = create_campaign(db, zone_uuid, body.message)
    return CampaignResponse(
        id=c.id,
        zone_id=str(c.zone_id),
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
        zone_id=str(c.zone_id),
        message=c.message,
        active=c.active,
        created_at=c.created_at.isoformat(),
    )


@router.get(
    "",
    response_model=list[CampaignResponse],
    summary="List campaigns",
    description="Optional filter by zone_id (UUID string).",
)
def list_all(
    zone_id: str | None = None,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    zone_uuid = None
    if zone_id is not None and zone_id.strip() != "":
        try:
            zone_uuid = uuid.UUID(zone_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid zone_id UUID")
    campaigns = list_campaigns(db, zone_uuid)
    return [
        CampaignResponse(
            id=c.id,
            zone_id=str(c.zone_id),
            message=c.message,
            active=c.active,
            created_at=c.created_at.isoformat(),
        )
        for c in campaigns
    ]


@router.delete(
    "/{campaign_id}",
    summary="Delete campaign",
    description="Delete a specific campaign by ID.",
)
def delete(
    campaign_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    success = delete_campaign(db, campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"success": True, "message": "Campaign deleted successfully"}
