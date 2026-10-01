from app.services.geo import is_point_in_radius, route_segments_near_point

class TrafficIncidentAgent:
    def __init__(self):
        self.active_incidents = []
        
    def check_route_incidents(self, route_coords: list[list[float]], incidents: list[dict]) -> list[dict]:
        affected_incidents = []
        for inc in incidents:
            lat = inc.get("lat")
            lng = inc.get("lng")
            radius = inc.get("radius", 100.0)
            
            # Check if any segment is within radius
            affected_segs = route_segments_near_point(route_coords, lat, lng, radius)
            if affected_segs:
                affected_incidents.append(inc)
                
        return affected_incidents
        
    def get_affected_segments(self, route_coords: list[list[float]], incidents: list[dict]) -> list[int]:
        segments = set()
        for inc in incidents:
            lat = inc.get("lat")
            lng = inc.get("lng")
            radius = inc.get("radius", 100.0)
            segs = route_segments_near_point(route_coords, lat, lng, radius)
            segments.update(segs)
        return list(segments)
        
    def calculate_segment_congestion(self, segment_index: int, incidents: list[dict]) -> float:
        # Simplistic logic: if affected by severe incident, high congestion
        return 2.0  # Base logic to be expanded
