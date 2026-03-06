from pydantic import BaseModel, model_validator


class EventRequest(BaseModel):
    # Supported values:
    # - "floor"
    # - "zone" (treated as "zone_entry" for backward compatibility)
    # - "zone_entry"
    # - "zone_exit"
    event_type: str = "zone"
    zone_id: str | None = None
    zone_name: str | None = None
    floor_id: int | None = None

    @model_validator(mode="after")
    def check_identifier(self):
        # Floor entry: only floor_id is required
        if self.event_type == "floor":
            if self.floor_id is None:
                raise ValueError("floor_id is required for floor events")
            return self

        # Normalize legacy "zone" to "zone_entry" semantics for validation purposes
        normalized_type = (
            "zone_entry" if self.event_type == "zone" else self.event_type
        )

        # Zone entry / exit: needs zone_id OR (zone_name + floor_id)
        if normalized_type in ("zone_entry", "zone_exit"):
            if self.zone_id is not None and self.zone_id != "":
                return self
            if self.zone_name is not None and self.floor_id is not None:
                return self
            raise ValueError(
                "For zone events: provide zone_id OR (zone_name + floor_id)"
            )

        raise ValueError(
            "event_type must be one of: 'floor', 'zone', 'zone_entry', 'zone_exit'"
        )
