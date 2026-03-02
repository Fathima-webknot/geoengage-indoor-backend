from pydantic import BaseModel


class CampaignCreate(BaseModel):
    zone_id: str  # UUID string
    message: str


class CampaignUpdate(BaseModel):
    active: bool


class CampaignResponse(BaseModel):
    id: int
    zone_id: str  # UUID string
    message: str
    active: bool
    created_at: str
