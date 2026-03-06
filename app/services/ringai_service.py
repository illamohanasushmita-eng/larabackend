import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

RINGGAI_BASE_URL = "https://prod-api.ringg.ai/ca/api/v0"


def _get_headers() -> dict:
    """Return auth headers for ringg.ai API."""
    return {
        "X-API-KEY": settings.RINGGAI_API_KEY or "",
        "Content-Type": "application/json",
    }


async def trigger_outbound_call(
    name: str,
    mobile_number: str,
    task_description: str,
    extra_args: dict = None,
) -> dict:
    """
    Trigger a single outbound AI call via ringg.ai.

    Args:
        name: Recipient's name (user's name)
        mobile_number: Phone number with country code e.g. +91XXXXXXXXXX
        task_description: What the AI agent should accomplish on the call
        extra_args: Optional extra key-value pairs passed as custom_args_values

    Returns:
        dict with call_id, status, message from ringg.ai
    """
    if not settings.RINGGAI_API_KEY:
        logger.error("RINGGAI_API_KEY is not set in .env")
        return {"success": False, "error": "Ringg.ai API key not configured. Please add RINGGAI_API_KEY to .env"}

    if not settings.RINGGAI_NUMBER_ID:
        logger.error("RINGGAI_NUMBER_ID is not set in .env")
        return {"success": False, "error": "Ringg.ai Number ID not configured. Please add RINGGAI_NUMBER_ID to .env"}

    custom_args = {"task": task_description}
    if extra_args:
        custom_args.update(extra_args)

    payload = {
        "name": name,
        "mobile_number": mobile_number,
        "agent_id": settings.RINGGAI_AGENT_ID,
        "from_number_id": settings.RINGGAI_NUMBER_ID,
        "custom_args_values": custom_args,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RINGGAI_BASE_URL}/calling/outbound/individual",
                json=payload,
                headers=_get_headers(),
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ ringg.ai call initiated: {data}")
            return {"success": True, "data": data}

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ ringg.ai API error {e.response.status_code}: {e.response.text}")
        return {"success": False, "error": f"ringg.ai API error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        logger.error(f"❌ ringg.ai call failed: {str(e)}")
        return {"success": False, "error": str(e)}


async def get_call_status(call_id: str) -> dict:
    """
    Fetch the status/details of a specific call from ringg.ai.
    """
    if not settings.RINGGAI_API_KEY:
        return {"success": False, "error": "Ringg.ai API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{RINGGAI_BASE_URL}/calling/{call_id}",
                headers=_get_headers(),
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"📞 ringg.ai call status for {call_id}: {data}")
            return {"success": True, "data": data}

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ ringg.ai status error {e.response.status_code}: {e.response.text}")
        return {"success": False, "error": f"Status fetch failed: {e.response.status_code}"}
    except Exception as e:
        logger.error(f"❌ Failed to get call status: {str(e)}")
        return {"success": False, "error": str(e)}
