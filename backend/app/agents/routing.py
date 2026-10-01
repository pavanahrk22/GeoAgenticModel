from app.services.routing_client import get_route
from app.agents.traffic_incident import TrafficIncidentAgent

class RoutingAgent:
    async def get_alternatives(self, current_pos: tuple[float, float], destination: tuple[float, float], incidents: list[dict]) -> list[dict]:
        avoid_points = [(inc["lat"], inc["lng"]) for inc in incidents]
        
        result = await get_route(current_pos, destination, alternatives=True, avoid_points=avoid_points)
        routes = result.get("routes", [])
        
        # Basic filtering could happen here
        return routes
