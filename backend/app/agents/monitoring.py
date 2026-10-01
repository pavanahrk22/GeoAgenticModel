import logging
from dataclasses import dataclass
from app.services.geo import point_to_line_distance, progress_along_route, remaining_distance

logger = logging.getLogger(__name__)

@dataclass
class MonitoringState:
    consecutive_off_route: int = 0
    is_deviated: bool = False
    progress: float = 0.0
    remaining_dist: float = 0.0

class MonitoringAgent:
    DEVIATION_THRESHOLD_METERS = 50.0
    CONSECUTIVE_PINGS_FOR_DEVIATION = 3
    
    def __init__(self):
        self.state = MonitoringState()

    def process_ping(self, lat: float, lng: float, route_coords: list[list[float]]) -> dict:
        dist_to_route = point_to_line_distance(lat, lng, route_coords)
        prog = progress_along_route(lat, lng, route_coords)
        rem_dist = remaining_distance(lat, lng, route_coords)
        
        on_route = dist_to_route <= self.DEVIATION_THRESHOLD_METERS
        
        if not on_route:
            self.state.consecutive_off_route += 1
        else:
            self.state.consecutive_off_route = 0
            self.state.is_deviated = False
            
        if self.state.consecutive_off_route >= self.CONSECUTIVE_PINGS_FOR_DEVIATION:
            self.state.is_deviated = True
            
        self.state.progress = prog
        self.state.remaining_dist = rem_dist
        
        return {
            "distance_to_route": dist_to_route,
            "on_route": on_route,
            "deviated": self.state.is_deviated,
            "progress": prog,
            "remaining_distance": rem_dist
        }
