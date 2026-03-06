from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_user
from app.models.user import User
from app.services import ringai_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request Schemas ──────────────────────────────────────────────────────────

class TriggerCallRequest(BaseModel):
    """Payload to trigger a ringg.ai outbound call."""
    mobile_number: str          # e.g. "+919876543210"
    task_description: str       # e.g. "Book a hotel room in Chennai for tomorrow"
    location: Optional[str] = None
    date: Optional[str] = None
    extra_args: Optional[dict] = None


class CallStatusRequest(BaseModel):
    call_id: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/trigger-call")
async def trigger_call(
    payload: TriggerCallRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an outbound AI call via ringg.ai.
    LARA voice assistant calls this after detecting a BookHotel / BookAppointment intent.
    """
    logger.info(f"📞 [ringg.ai] Triggering call for user {current_user.id} → {payload.mobile_number}")

    # Build extra args (location/date are passed as custom variables to the AI agent)
    extra = payload.extra_args or {}
    if payload.location:
        extra["location"] = payload.location
    if payload.date:
        extra["date"] = payload.date

    result = await ringai_service.trigger_outbound_call(
        name=current_user.full_name or current_user.email,
        mobile_number=payload.mobile_number,
        task_description=payload.task_description,
        extra_args=extra,
    )

    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "ringg.ai call failed"))

    return {
        "status": "initiated",
        "message": "AI call has been started. You will receive a notification once the call completes.",
        "call_data": result.get("data"),
    }


@router.get("/call-status/{call_id}")
async def get_call_status(
    call_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get the status of a specific ringg.ai call by call_id.
    """
    logger.info(f"📋 [ringg.ai] Fetching status for call {call_id}")

    result = await ringai_service.get_call_status(call_id)

    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Failed to fetch call status"))

    return {
        "status": "ok",
        "call_id": call_id,
        "call_data": result.get("data"),
    }


@router.post("/webhook")
async def ringgai_webhook(request: Request):
    """
    Webhook endpoint — ringg.ai calls this URL when a call completes/fails.
    Configure this URL in your ringg.ai dashboard:
      https://your-lara-server.com/api/v1/ringai/webhook

    ringg.ai sends events like:
      call_completed, call_failed, recording_completed
    """
    try:
        payload = await request.json()
        event = payload.get("event", "unknown")
        call_id = payload.get("call_id", "unknown")

        logger.info(f"🔔 [ringg.ai Webhook] Event: {event} | Call ID: {call_id}")
        logger.info(f"🔔 [ringg.ai Webhook] Full payload: {payload}")

        # ── Handle specific events ────────────────────────────────────────────
        if event == "call_completed":
            outcome = payload.get("outcome") or payload.get("summary", "Call completed")
            logger.info(f"✅ [ringg.ai] Call {call_id} completed. Outcome: {outcome}")
            # TODO: Save as Task or update booking record in DB if needed

        elif event == "call_failed":
            reason = payload.get("reason", "Unknown reason")
            logger.warning(f"❌ [ringg.ai] Call {call_id} failed. Reason: {reason}")

        elif event == "recording_completed":
            recording_url = payload.get("recording_url")
            logger.info(f"🎙️ [ringg.ai] Recording ready for call {call_id}: {recording_url}")

        # Always return 200 to acknowledge receipt
        return {"status": "received", "event": event, "call_id": call_id}

    except Exception as e:
        logger.error(f"❌ [ringg.ai Webhook] Error processing event: {str(e)}")
        # Still return 200 to prevent ringg.ai from retrying indefinitely
        return {"status": "error", "detail": str(e)}
