from pydantic import BaseModel


class CampaignCreate(BaseModel):
    zone_id: int
    message: str


class CampaignUpdate(BaseModel):
    active: bool


class CampaignResponse(BaseModel):
    id: int
    zone_id: int
    message: str
    active: bool
    created_at: str
