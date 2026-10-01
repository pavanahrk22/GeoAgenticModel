import logging
from app.services.geo import route_segments_near_point, haversine_distance

logger = logging.getLogger(__name__)


class DecisionAgent:
    """Deterministic scoring of alternative routes. Never says 'safest'; uses 'suitable/optimized'."""

    WEIGHTS = {
        "eta": 0.4,
        "distance": 0.3,
        "congestion": 0.2,
        "incident_proximity": 0.1,
    }

    def rank_routes(
        self,
        routes: list[dict],
        incidents: list[dict],
        baseline_eta: float,
    ) -> list[dict]:
        if not routes:
            return []

        # Collect raw values for normalization
        durations = [r.get("duration", 0) for r in routes]
        distances = [r.get("distance", 0) for r in routes]

        max_duration = max(durations) if durations else 1
        min_duration = min(durations) if durations else 0
        max_distance = max(distances) if distances else 1
        min_distance = min(distances) if distances else 0

        duration_range = max_duration - min_duration or 1
        distance_range = max_distance - min_distance or 1

        scored = []
        for route in routes:
            duration = route.get("duration", 0)
            distance = route.get("distance", 0)
            geometry = route.get("geometry", [])

            # Normalize ETA score (lower is better, so invert)
            eta_norm = 1.0 - ((duration - min_duration) / duration_range)

            # Normalize distance score (lower is better)
            dist_norm = 1.0 - ((distance - min_distance) / distance_range)

            # Congestion exposure: count how many route segments are near incidents
            congestion_score = 1.0
            if geometry and incidents:
                total_segments = max(len(geometry) - 1, 1)
                affected_count = 0
                for inc in incidents:
                    affected = route_segments_near_point(
                        geometry,
                        inc.get("lat", 0),
                        inc.get("lng", 0),
                        inc.get("radius", 100) * 2,  # wider check for congestion zone
                    )
                    affected_count += len(affected)
                congestion_score = max(0.0, 1.0 - (affected_count / total_segments))

            # Incident proximity: min distance from route to any incident
            proximity_score = 1.0
            if geometry and incidents:
                min_inc_dist = float("inf")
                for inc in incidents:
                    for coord in geometry[::max(1, len(geometry) // 20)]:
                        d = haversine_distance(
                            coord[0], coord[1],
                            inc.get("lat", 0), inc.get("lng", 0),
                        )
                        min_inc_dist = min(min_inc_dist, d)
                # Normalize: >1000m is perfect, 0m is worst
                proximity_score = min(1.0, min_inc_dist / 1000.0) if min_inc_dist != float("inf") else 1.0

            # Weighted composite score (higher is better)
            total_score = (
                self.WEIGHTS["eta"] * eta_norm
                + self.WEIGHTS["distance"] * dist_norm
                + self.WEIGHTS["congestion"] * congestion_score
                + self.WEIGHTS["incident_proximity"] * proximity_score
            )

            route_copy = route.copy()
            route_copy["score"] = round(total_score, 4)
            route_copy["score_breakdown"] = {
                "eta": round(eta_norm, 3),
                "distance": round(dist_norm, 3),
                "congestion_exposure": round(congestion_score, 3),
                "incident_proximity": round(proximity_score, 3),
            }
            route_copy["label"] = "Most suitable" if total_score > 0.7 else "Suitable alternative"
            scored.append(route_copy)

        scored.sort(key=lambda x: x["score"], reverse=True)  # Higher is better
        return scored
