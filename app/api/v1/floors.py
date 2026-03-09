from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import Floor

router = APIRouter(tags=["Optional"], prefix="")


@router.get(
    "/floors",
    summary="List floors",
    description="All floors in venue (floor_id = floor number, floor_name).",
)
def list_floors(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    floors = db.query(Floor).all()
    return [
        {"floor_id": f.floor_id, "floor_name": f.floor_name}
        for f in floors
    ]
