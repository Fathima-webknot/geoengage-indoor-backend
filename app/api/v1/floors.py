from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import Floor

router = APIRouter(tags=["Optional"], prefix="")


@router.get(
    "/floors",
    summary="List floors",
    description="All floors in venue.",
)
def list_floors(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    floors = db.query(Floor).all()
    return [
        {"id": f.id, "name": f.name, "floor_number": f.floor_number}
        for f in floors
    ]
