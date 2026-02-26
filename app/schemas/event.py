from pydantic import BaseModel, model_validator


class EventRequest(BaseModel):
    zone_id: int | None = None
    zone_name: str | None = None
    floor_id: int | None = None

    @model_validator(mode="after")
    def check_identifier(self):
        if self.zone_id is not None:
            return self
        if self.zone_name is not None and self.floor_id is not None:
            return self
        raise ValueError("Either zone_id or (zone_name and floor_id) must be provided")
