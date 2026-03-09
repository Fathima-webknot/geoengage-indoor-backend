from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.schemas.event import EventRequest
from app.services.event import (
    record_event_and_maybe_notify,
    send_floor_entry_notification,
    handle_zone_exit_and_maybe_notify,
)

router = APIRouter(tags=["User (Android)"], prefix="")
logger = logging.getLogger(__name__)


@router.post(
    "/event",
    response_model=dict,
    summary="Floor or Zone entry/exit event",
    description=(
        "Log floor entry (informational) or zone entry/exit (with campaigns). "
        "Use event_type='floor' for floor entry, 'zone' or 'zone_entry' for zone entry, "
        "and 'zone_exit' for zone exit."
    ),
)
def post_event(
    body: EventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Log received data
    logger.info(f"📥 Event received - User: {current_user.id}, Type: {body.event_type}, Floor: {body.floor_id}, Zone: {body.zone_id or body.zone_name}")
    
    try:
        # Handle floor entry separately (no database record, just notification)
        if body.event_type == "floor":
            logger.info(f"🏢 Processing floor entry for floor_id: {body.floor_id}")
            success, notification_sent, message = send_floor_entry_notification(
                db, current_user.id, body.floor_id
            )
            if not success:
                logger.error(f"❌ Floor not found: {body.floor_id}")
                raise HTTPException(status_code=404, detail="Floor not found")
            logger.info(f"✅ Floor notification sent: {notification_sent}")
            return {
                "success": True,
                "notification_sent": notification_sent,
                "message": message or "Floor entry processed",
            }
        # Normalize legacy "zone" to "zone_entry" semantics
        event_type = "zone_entry" if body.event_type == "zone" else body.event_type

        if event_type == "zone_entry":
            # Handle zone entry (with campaign and database record)
            logger.info(f"🎯 Processing zone entry - zone_id: {body.zone_id}, zone_name: {body.zone_name}")
            success, notification_sent, message = record_event_and_maybe_notify(
                db,
                current_user.id,
                zone_id=body.zone_id,
                zone_name=body.zone_name,
                floor_id=body.floor_id,
            )
            if not success:
                logger.error("❌ Zone not found")
                raise HTTPException(status_code=404, detail="Zone not found")
            if notification_sent and message:
                logger.info(f"✅ Campaign notification sent: {message}")
                return {
                    "success": True,
                    "notification_sent": True,
                    "campaign_message": message,
                }
            logger.info("ℹ️ Event logged, no active entry campaign")
            return {
                "success": True,
                "notification_sent": False,
                "message": "Event logged, no active entry campaign",
            }

        if event_type == "zone_exit":
            logger.info(f"🚪 Processing zone exit - zone_id: {body.zone_id}, zone_name: {body.zone_name}")
            success, notification_sent, message = handle_zone_exit_and_maybe_notify(
                db,
                current_user.id,
                zone_id=body.zone_id,
                zone_name=body.zone_name,
                floor_id=body.floor_id,
            )
            if not success:
                logger.error("❌ Zone not found on exit")
                raise HTTPException(status_code=404, detail="Zone not found")
            if notification_sent and message:
                logger.info(f"✅ Exit-without-transaction notification sent: {message}")
                return {
                    "success": True,
                    "notification_sent": True,
                    "campaign_message": message,
                }
            logger.info("ℹ️ Exit processed with no exit campaign triggered")
            return {
                "success": True,
                "notification_sent": False,
                "message": "Exit processed",
            }

        logger.error(f"❌ Unsupported event_type: {body.event_type}")
        raise HTTPException(status_code=400, detail="Unsupported event_type")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error processing event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")
