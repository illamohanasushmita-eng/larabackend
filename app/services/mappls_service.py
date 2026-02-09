import httpx
import logging
from app.core.config import settings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MapplsService:
    BASE_URL_ATLAS = "https://atlas.mappls.com/api/places"
    BASE_URL_OUTPOST = "https://outpost.mappls.com/api" 
    # Note: Mappls APIs have various base URLs depending on the specific service (Atlas, Routing, etc.)
    # We will use flexible URL construction.

    @staticmethod
    async def search_nearby(query: str, lat: float, lng: float, radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for places nearby using Mappls Nearby Search API.
        GET https://atlas.mappls.com/api/places/nearby/json
        """
        if not settings.MAPPLS_ACCESS_TOKEN:
            logger.warning("⚠️ MAPPLS_ACCESS_TOKEN is missing in settings.")
            return []

        # Detect Token Type
        token = settings.MAPPLS_ACCESS_TOKEN
        is_legacy_key = len(token) < 100 # REST Keys are ~32-36 chars; JWTs are much longer
        
        if is_legacy_key:
            # Legacy REST API Endpoint
            # https://apis.mapmyindia.com/advancedmaps/v1/<key>/nearby_search/json
            url = f"https://apis.mapmyindia.com/advancedmaps/v1/{token}/nearby_search/json"
            params = {
                "keywords": query,
                "refLocation": f"{lat},{lng}"
            }
            headers = {}
        else:
            # Atlas API (OAuth 2.0)
            url = f"{MapplsService.BASE_URL_ATLAS}/nearby/json"
            params = {
                "keywords": query,
                "refLocation": f"{lat},{lng}",
                "radius": radius
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"🗺️ Calling Mappls ({'REST' if is_legacy_key else 'Atlas'}): {query} at {lat},{lng}")
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Response structure:
                    # Atlas: {"suggestedLocations": [...]}
                    # REST: {"suggestedLocations": [...]} (Usually similar, but let's be safe)
                    return data.get("suggestedLocations", [])
                else:
                    logger.error(f"❌ Mappls API Error {response.status_code}: {response.text}")
                    return []
        except Exception as e:
            logger.error(f"❌ Mappls Request Failed: {e}")
            return []

    @staticmethod
    async def search_places(query: str, lat: float, lng: float) -> List[Dict[str, Any]]:
        """
        Text Search API for specific places (not just categories).
        GET https://atlas.mappls.com/api/places/search/json
        """
        if not settings.MAPPLS_ACCESS_TOKEN:
            return []

        url = f"{MapplsService.BASE_URL_ATLAS}/search/json"
        params = {
            "query": query,
            "location": f"{lat},{lng}"
            # "pod": "City" # optional
        }
        headers = {
            "Authorization": f"Bearer {settings.MAPPLS_ACCESS_TOKEN}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("suggestedLocations", [])
                else:
                    logger.error(f"❌ Mappls Search Error {response.status_code}: {response.text}")
                    return []
        except Exception as e:
            logger.error(f"❌ Mappls Search Failed: {e}")
            return []

    # Helper to format response into natural language
    @staticmethod
    def format_places_response(places: List[Dict[str, Any]], intent_category: str) -> str:
        if not places:
            return f"I couldn't find any {intent_category} nearby."
        
        top_places = places[:3]
        response_parts = [f"I found a few {intent_category} nearby:"]
        
        for p in top_places:
             name = p.get("placeName", "Unknown Place")
             address = p.get("placeAddress", "")
             dist_meters = p.get("distance", 0)
             
             # Convert dist to km if > 1000
             if dist_meters >= 1000:
                 dist_str = f"{dist_meters/1000:.1f} km"
             else:
                 dist_str = f"{dist_meters} meters"
                 
             response_parts.append(f"• {name} ({dist_str} away).")
             
        return " ".join(response_parts)

