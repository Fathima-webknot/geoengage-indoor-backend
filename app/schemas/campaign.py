from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    zone_id: str  # UUID string
    message: str
    name: str | None = Field(
        default=None,
        description="Optional campaign name / offer label (e.g. 'Summer Sale').",
    )
    trigger: str = Field(default="zone_entry", description="When to trigger this campaign (e.g. 'zone_entry', 'zone_exit_no_txn').")


class CampaignUpdate(BaseModel):
    active: bool


class CampaignResponse(BaseModel):
    id: int
    zone_id: str  # UUID string
    message: str
    name: str | None
    active: bool
    trigger: str
    created_at: str
