from pydantic import BaseModel
from datetime import datetime


class NotificationClickRequest(BaseModel):
    campaign_id: int
