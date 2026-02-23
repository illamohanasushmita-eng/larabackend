import httpx
import math
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """
    Service to interact with the Google Places API (Nearby Search).
    Replaces the MapplsService for finding nearby places.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    @staticmethod
    def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance in meters between two GPS coordinates."""
        R = 6371000  # Radius of Earth in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    async def search_nearby(keyword: str, lat: float, lng: float, radius: int = 2000) -> List[Dict[str, Any]]:
        """
        Search for places near the given lat/lng using Google Places Nearby Search.
        Returns a list of places with placeName, placeAddress, distance, lat, lng.
        """
        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            logger.error("❌ GOOGLE_MAPS_API_KEY is not configured!")
            return []

        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": keyword,
            "key": api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"🗺️ [Google Maps] Searching '{keyword}' near {lat},{lng} (radius={radius}m)")
                response = await client.get(GoogleMapsService.BASE_URL, params=params)

                if response.status_code != 200:
                    logger.error(f"❌ Google Places API Error {response.status_code}: {response.text}")
                    return []

                data = response.json()
                status = data.get("status")

                if status not in ("OK", "ZERO_RESULTS"):
                    logger.error(f"❌ Google Places API status: {status} | {data.get('error_message', '')}")
                    return []

                results = data.get("results", [])
                places = []

                for place in results[:5]:  # Top 5 results
                    place_lat = place.get("geometry", {}).get("location", {}).get("lat")
                    place_lng = place.get("geometry", {}).get("location", {}).get("lng")

                    distance = (
                        GoogleMapsService._haversine_distance(lat, lng, place_lat, place_lng)
                        if place_lat is not None and place_lng is not None
                        else 0
                    )

                    places.append({
                        "placeName": place.get("name", "Unknown Place"),
                        "placeAddress": place.get("vicinity", "Address not available"),
                        "distance": round(distance),
                        "lat": place_lat,
                        "lng": place_lng,
                        "rating": place.get("rating"),
                        "open_now": place.get("opening_hours", {}).get("open_now"),
                    })

                logger.info(f"✅ Google Maps returned {len(places)} places for '{keyword}'")
                return places

        except Exception as e:
            logger.error(f"❌ Google Maps request failed: {e}")
            return []

    @staticmethod
    def format_places_response(places: List[Dict[str, Any]], keyword: str) -> str:
        """Format places list into a conversational TTS-friendly message."""
        if not places:
            return f"I couldn't find any {keyword} nearby. Please try a different search."

        count = len(places)
        first = places[0]
        name = first.get("placeName", "a place")
        dist = first.get("distance", 0)
        dist_str = f"{dist / 1000:.1f} kilometers" if dist >= 1000 else f"{dist} meters"

        return (
            f"I found {count} {'place' if count == 1 else 'places'} nearby. "
            f"The closest is {name}, {dist_str} away."
        )
