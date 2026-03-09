from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.schemas.transaction import TransactionCreate
from app.services.transaction import record_transaction


router = APIRouter(tags=["User (Android)"], prefix="")


@router.post(
    "/transactions",
    response_model=dict,
    summary="Record transaction in a zone",
    description="Record a transaction for the current user in a given zone.",
)
def create_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = record_transaction(
        db,
        current_user.id,
        zone_id=body.zone_id,
        zone_name=body.zone_name,
        floor_id=body.floor_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"success": True}

