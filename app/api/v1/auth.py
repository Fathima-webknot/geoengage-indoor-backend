from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import MeResponse, RegisterDeviceRequest
from app.services.user import update_fcm_token

router = APIRouter(tags=["User (Android)"], prefix="")
admin_router = APIRouter(tags=["Admin (Web)"], prefix="")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user profile",
    description="Returns current user from Firebase token.",
)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        firebase_uid=current_user.firebase_uid,
    )


@router.post(
    "/register-device",
    summary="Register FCM token",
    description="Store or update FCM token for push notifications.",
)
def register_device(
    body: RegisterDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_fcm_token(db, current_user.id, body.fcm_token)
    return {"success": True, "message": "Device registered successfully"}


@admin_router.get(
    "/verify-admin",
    summary="Verify admin access (Web only)",
    description="Check if current user has admin role. Returns 403 if not admin.",
)
def verify_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not an admin user")
    return {
        "success": True,
        "message": "Admin verified",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
        },
    }
