from pydantic import BaseModel


class ZoneEntryItem(BaseModel):
    zone: str
    count: int


class TopZoneItem(BaseModel):
    zone_name: str
    ctr: float


class AnalyticsResponse(BaseModel):
    zone_entries: list[ZoneEntryItem]
    notifications_sent: int
    clicks: int
    ctr: float
    top_zones: list[TopZoneItem]
