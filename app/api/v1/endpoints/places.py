from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.models.user import User
from app.services import google_maps_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/nearby")
async def get_nearby_places(
    keyword: str = Query(..., description="Search keyword, e.g. ATM, restaurant, hospital"),
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius: int = Query(2000, description="Search radius in meters"),
    current_user: User = Depends(get_current_user)
):
    """
    Directly search for nearby places using Google Maps.
    Does NOT go through AI re-processing.
    """
    logger.info(f"🗺️ [Places API] Searching '{keyword}' at {lat},{lng} radius={radius}m")
    
    places = await google_maps_service.GoogleMapsService.search_nearby(
        keyword=keyword,
        lat=lat,
        lng=lng,
        radius=radius
    )

    message = google_maps_service.GoogleMapsService.format_places_response(places, keyword)

    return {
        "status": "ok",
        "keyword": keyword,
        "count": len(places),
        "message": message,
        "places": places
    }
