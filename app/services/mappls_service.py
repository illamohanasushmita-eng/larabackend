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
    _access_token: Optional[str] = None
    
    @classmethod
    async def get_token(cls) -> Optional[str]:
        """
        Generates or returns a valid Mappls OAuth 2.0 token.
        POST https://outpost.mappls.com/api/security/oauth/token
        """
        # If we have a static token in .env (and no client creds), use it as fallback
        if settings.MAPPLS_ACCESS_TOKEN and not (settings.MAPPLS_CLIENT_ID and settings.MAPPLS_CLIENT_SECRET):
            return settings.MAPPLS_ACCESS_TOKEN

        if not (settings.MAPPLS_CLIENT_ID and settings.MAPPLS_CLIENT_SECRET):
            logger.error("❌ Mappls Client ID/Secret missing!")
            return None

        # TODO: Add expiration check logic here if needed (Mappls tokens last 24h)
        if cls._access_token:
            return cls._access_token

        url = "https://outpost.mappls.com/api/security/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.MAPPLS_CLIENT_ID,
            "client_secret": settings.MAPPLS_CLIENT_SECRET
        }

        try:
            async with httpx.AsyncClient() as client:
                logger.info("🔄 Generating new Mappls Token...")
                response = await client.post(url, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    cls._access_token = token_data.get("access_token")
                    logger.info("✅ Mappls Token Generated Successfully")
                    return cls._access_token
                else:
                    logger.error(f"❌ Token Gen Error {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Token Gen Failed: {e}")
            return None

    @staticmethod
    async def search_nearby(query: str, lat: float, lng: float, radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for places nearby using Mappls Nearby Search API.
        GET https://atlas.mappls.com/api/places/nearby/json
        """
        token = await MapplsService.get_token()
        if not token:
            return []

        # Atlas API (OAuth 2.0)
        url = f"{MapplsService.BASE_URL_ATLAS}/nearby/json"
        
        # Mappls expects "keywords" for category search (e.g. "restaurants") 
        # but treats simple keyword searches better with specific params
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
                logger.info(f"🗺️ Calling Mappls: {query} at {lat},{lng}")
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
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
        Text Search API for specific places.
        GET https://atlas.mappls.com/api/places/search/json
        """
        token = await MapplsService.get_token()
        if not token:
            return []

        url = f"{MapplsService.BASE_URL_ATLAS}/search/json"
        params = {
            "query": query,
            "location": f"{lat},{lng}"
        }
        headers = {
            "Authorization": f"Bearer {token}"
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

