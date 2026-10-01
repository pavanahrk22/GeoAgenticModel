import httpx
import hashlib
import json
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

_route_cache: dict[str, dict] = {}

async def get_route(
    origin: tuple[float, float],  # (lat, lng)
    destination: tuple[float, float],
    alternatives: bool = False,
    avoid_points: list[tuple[float, float]] | None = None,
) -> dict:
    settings = get_settings()
    
    # Build cache key
    params = {
        "origin": origin,
        "destination": destination,
        "alternatives": alternatives,
        "avoid_points": avoid_points
    }
    cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
    
    if cache_key in _route_cache:
        logger.debug(f"Route cache hit for key {cache_key}")
        return _route_cache[cache_key]
        
    provider = getattr(settings, "ROUTING_PROVIDER", "osrm").lower()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "ors":
                result = await _get_route_ors(client, origin, destination, alternatives, avoid_points, settings)
            else:
                result = await _get_route_osrm(client, origin, destination, alternatives, avoid_points, settings)
                
            _route_cache[cache_key] = result
            return result
    except Exception as e:
        logger.warning(f"Routing request failed: {e}")
        return {"routes": []}

async def _get_route_osrm(client, origin, destination, alternatives, avoid_points, settings):
    base_url = getattr(settings, "OSRM_BASE_URL", "http://router.project-osrm.org")
    # OSRM expects {lng},{lat}
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    url = f"{base_url}/route/v1/driving/{coords}"
    
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "true" if alternatives else "false",
        "steps": "true"
    }
    
    response = await client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    routes = []
    for r in data.get("routes", []):
        geometry = [[coord[1], coord[0]] for coord in r["geometry"]["coordinates"]] # Convert back to [lat, lng]
        routes.append({
            "geometry": geometry,
            "distance": r.get("distance", 0),
            "duration": r.get("duration", 0),
            "segments": r.get("legs", [])
        })
    return {"routes": routes}

async def _get_route_ors(client, origin, destination, alternatives, avoid_points, settings):
    base_url = getattr(settings, "ORS_BASE_URL", "https://api.openrouteservice.org")
    api_key = getattr(settings, "ORS_API_KEY", "")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # ORS expects [lng, lat]
    body = {
        "coordinates": [[origin[1], origin[0]], [destination[1], destination[0]]],
        "alternative_routes": {"target_count": 3} if alternatives else {}
    }
    
    url = f"{base_url}/v2/directions/driving-car/geojson"
    response = await client.post(url, headers=headers, json=body)
    response.raise_for_status()
    data = response.json()
    
    routes = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geometry = [[coord[1], coord[0]] for coord in feature["geometry"]["coordinates"]]
        routes.append({
            "geometry": geometry,
            "distance": props.get("summary", {}).get("distance", 0),
            "duration": props.get("summary", {}).get("duration", 0),
            "segments": props.get("segments", [])
        })
    return {"routes": routes}
