from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import Zone

router = APIRouter(tags=["Optional"], prefix="")


@router.get(
    "/zones",
    summary="List zones",
    description="All zones. Optional floor_id (floor number) filter.",
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
            "id": str(z.id),
            "floor_id": z.floor_id,
            "name": z.name,
        }
        for z in zones
    ]
