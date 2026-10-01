import math
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _latlng_to_meters(lat_dist: float, lng_dist: float, lat: float) -> float:
    # 1 degree lat ~= 111320 meters. 1 degree lng ~= 111320 * cos(lat)
    lat_m = lat_dist * 111320.0
    lng_m = lng_dist * 111320.0 * math.cos(math.radians(lat))
    return math.sqrt(lat_m**2 + lng_m**2)

def point_to_line_distance(lat: float, lng: float, route_coords: list[list[float]]) -> float:
    if not route_coords:
        return 0.0
    point = Point(lng, lat)
    line = LineString([(c[1], c[0]) for c in route_coords])
    nearest_p = nearest_points(point, line)[1]
    
    # Distance in degrees approx to meters
    return _latlng_to_meters(abs(point.y - nearest_p.y), abs(point.x - nearest_p.x), lat)

def progress_along_route(lat: float, lng: float, route_coords: list[list[float]]) -> float:
    if not route_coords or len(route_coords) < 2:
        return 0.0
    point = Point(lng, lat)
    line = LineString([(c[1], c[0]) for c in route_coords])
    projected = line.project(point)
    return max(0.0, min(1.0, projected / line.length))

def remaining_distance(lat: float, lng: float, route_coords: list[list[float]]) -> float:
    if not route_coords or len(route_coords) < 2:
        return 0.0
    prog = progress_along_route(lat, lng, route_coords)
    total_dist = 0.0
    for i in range(len(route_coords) - 1):
        total_dist += haversine_distance(
            route_coords[i][0], route_coords[i][1],
            route_coords[i+1][0], route_coords[i+1][1]
        )
    return total_dist * (1.0 - prog)

def is_point_in_radius(lat: float, lng: float, center_lat: float, center_lng: float, radius_meters: float) -> bool:
    dist = haversine_distance(lat, lng, center_lat, center_lng)
    return dist <= radius_meters

def route_segments_near_point(route_coords: list[list[float]], center_lat: float, center_lng: float, radius_meters: float) -> list[int]:
    affected = []
    if not route_coords:
        return affected
        
    for i in range(len(route_coords) - 1):
        # A simple check if any end of segment is within radius, or if the segment crosses the radius
        # For a full check, we compute distance from center to segment
        p_c = Point(center_lng, center_lat)
        seg = LineString([(route_coords[i][1], route_coords[i][0]), (route_coords[i+1][1], route_coords[i+1][0])])
        nearest = nearest_points(p_c, seg)[1]
        dist = _latlng_to_meters(abs(p_c.y - nearest.y), abs(p_c.x - nearest.x), center_lat)
        if dist <= radius_meters:
            affected.append(i)
    return affected
