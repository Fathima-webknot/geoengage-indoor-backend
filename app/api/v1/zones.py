from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import Zone

router = APIRouter(tags=["Optional"], prefix="")


@router.get(
    "/zones",
    summary="List zones",
    description="All zones with polygon coordinates. Optional floor_id filter.",
)
def list_zones(
    floor_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Zone)
    if floor_id is not None:
        q = q.filter(Zone.floor_id == floor_id)
    zones = q.all()
    return [
        {
            "id": z.id,
            "floor_id": z.floor_id,
            "name": z.name,
            "polygon_coordinates": z.polygon_coordinates,
        }
        for z in zones
    ]
