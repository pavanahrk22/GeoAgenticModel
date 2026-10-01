import logging
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Trip, Position, Incident, Recommendation, TripStatus
from app.agents.monitoring import MonitoringAgent
from app.agents.traffic_incident import TrafficIncidentAgent
from app.agents.eta import ETAAgent
from app.agents.routing import RoutingAgent
from app.agents.decision import DecisionAgent
from app.agents.explanation import ExplanationAgent

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.monitoring_agents: dict[str, MonitoringAgent] = {}
        self.traffic_agent = TrafficIncidentAgent()
        self.eta_agent = ETAAgent()
        self.routing_agent = RoutingAgent()
        self.decision_agent = DecisionAgent()
        self.explanation_agent = ExplanationAgent()
        self._last_trigger_progress: dict[str, float] = {}  # avoid re-triggering too often

    async def process_gps_ping(self, trip_id: str, lat: float, lng: float, speed: float, heading: float, db: AsyncSession) -> list[dict]:
        """Process a GPS ping through the agent pipeline. Returns list of WS messages to broadcast."""
        messages = []
        
        # 1. Load trip from DB
        result = await db.execute(select(Trip).where(Trip.id == trip_id))
        trip = result.scalar_one_or_none()
        if not trip:
            logger.warning(f"Trip {trip_id} not found")
            return messages
        
        # Extract route coords from planned_route_geojson
        route_coords = self._extract_route_coords(trip.planned_route_geojson)
        if not route_coords:
            logger.warning(f"No route coords for trip {trip_id}")
            return messages
        
        # 2. Save position to DB
        position = Position(
            trip_id=trip_id,
            lat=lat,
            lng=lng,
            speed=speed,
            heading=heading,
            timestamp=datetime.now(timezone.utc),
            on_route=True  # will be updated below
        )
        db.add(position)
        
        # 3. Monitoring Agent
        if trip_id not in self.monitoring_agents:
            self.monitoring_agents[trip_id] = MonitoringAgent()
        monitor = self.monitoring_agents[trip_id]
        mon_status = monitor.process_ping(lat, lng, route_coords)
        
        position.on_route = mon_status["on_route"]
        
        # Send position message
        messages.append({
            "type": "position",
            "data": {
                "lat": lat,
                "lng": lng,
                "speed": speed,
                "heading": heading,
                "on_route": mon_status["on_route"],
                "progress": mon_status["progress"],
                "distance_to_route": round(mon_status["distance_to_route"], 1),
            }
        })
        
        # 4. Get active incidents from DB
        inc_result = await db.execute(select(Incident).where(Incident.active == True))
        db_incidents = inc_result.scalars().all()
        incidents = [
            {"id": i.id, "type": i.type.value, "lat": i.lat, "lng": i.lng, 
             "radius": i.radius_meters, "severity": i.severity.value, "description": i.description}
            for i in db_incidents
        ]
        
        # 5. Traffic/Incident Agent - check if route is affected
        affected_incidents = self.traffic_agent.check_route_incidents(route_coords, incidents)
        affected_segments = self.traffic_agent.get_affected_segments(route_coords, incidents)
        
        # 6. ETA Agent
        congestion_factors = [self.traffic_agent.calculate_segment_congestion(s, incidents) for s in affected_segments] if affected_segments else [1.0]
        segment_speeds = [40.0] * max(1, len(route_coords) - 1)  # base speed 40 km/h
        
        eta_result = self.eta_agent.calculate_eta(
            mon_status["remaining_distance"],
            segment_speeds,
            congestion_factors,
            trip.baseline_eta_seconds or 1200.0
        )
        
        # Update trip ETA
        trip.current_eta_seconds = eta_result["eta_seconds"]
        
        messages.append({
            "type": "eta_update",
            "data": {
                "current_eta_seconds": round(eta_result["eta_seconds"], 1),
                "baseline_eta_seconds": trip.baseline_eta_seconds,
                "delay_percentage": round(eta_result["delay_percentage"], 1),
                "delayed": eta_result["delayed"],
                "remaining_distance": round(mon_status["remaining_distance"], 1),
                "progress": round(mon_status["progress"], 3),
            }
        })
        
        # 7. Check triggers for rerouting
        should_reroute = False
        trigger_type = None
        last_progress = self._last_trigger_progress.get(trip_id, -1.0)
        progress_since_last = mon_status["progress"] - last_progress
        
        if mon_status["deviated"] and progress_since_last > 0.02:
            should_reroute = True
            trigger_type = "deviation"
            messages.append({"type": "alert", "data": {
                "severity": "high", "message": f"Vehicle has deviated from planned route ({round(mon_status['distance_to_route'])}m off-route)",
                "alert_type": "deviation"
            }})
        
        if eta_result["delayed"] and progress_since_last > 0.02:
            should_reroute = True
            trigger_type = trigger_type or "delay"
            messages.append({"type": "alert", "data": {
                "severity": "warning", "message": f"ETA delayed by {round(eta_result['delay_percentage'])}% from baseline",
                "alert_type": "delay"
            }})
        
        if affected_incidents and progress_since_last > 0.02:
            should_reroute = True
            trigger_type = trigger_type or "incident"
            for inc in affected_incidents:
                messages.append({"type": "alert", "data": {
                    "severity": inc.get("severity", "medium"),
                    "message": f"{inc['type'].title()} detected ahead on route: {inc.get('description', 'No details')}",
                    "alert_type": "incident", "incident_id": inc["id"]
                }})
        
        # 8. Rerouting pipeline
        if should_reroute:
            self._last_trigger_progress[trip_id] = mon_status["progress"]
            trip.status = TripStatus.rerouting
            
            try:
                # Get alternatives
                destination = (trip.destination_lat, trip.destination_lng)
                alternatives = await self.routing_agent.get_alternatives(
                    (lat, lng), destination, incidents
                )
                
                if alternatives:
                    # Rank routes
                    ranked = self.decision_agent.rank_routes(
                        alternatives, incidents, trip.baseline_eta_seconds or 1200.0
                    )
                    
                    # Get explanation
                    situation = {
                        "vehicle_position": {"lat": lat, "lng": lng},
                        "destination": {"lat": trip.destination_lat, "lng": trip.destination_lng},
                        "incidents": affected_incidents,
                        "trigger": trigger_type,
                        "current_delay_pct": eta_result["delay_percentage"],
                    }
                    explanation = await self.explanation_agent.explain(situation, ranked)
                    
                    # Store recommendation in DB
                    rec = Recommendation(
                        trip_id=trip_id,
                        trigger_type=trigger_type,
                        routes_json=ranked,
                        explanation=explanation,
                        score_breakdown=ranked[0].get("score_breakdown") if ranked else None
                    )
                    db.add(rec)
                    
                    # Build route_update message with alternatives as [lat, lng] arrays
                    route_alternatives = []
                    colors = ["#f97316", "#22c55e", "#a855f7"]  # orange, green, purple
                    for idx, route in enumerate(ranked[:3]):
                        route_alternatives.append({
                            "index": idx,
                            "geometry": route.get("geometry", []),
                            "distance": round(route.get("distance", 0), 1),
                            "duration": round(route.get("duration", 0), 1),
                            "score": round(route.get("score", 0), 4),
                            "score_breakdown": route.get("score_breakdown", {}),
                            "color": colors[idx % len(colors)],
                        })
                    
                    messages.append({
                        "type": "recommendation",
                        "data": {
                            "trigger": trigger_type,
                            "routes": route_alternatives,
                            "explanation": explanation,
                            "recommendation_id": rec.id if hasattr(rec, 'id') else None,
                        }
                    })
                    
                    messages.append({
                        "type": "route_update",
                        "data": {
                            "alternatives": route_alternatives,
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Rerouting pipeline error: {e}", exc_info=True)
                messages.append({"type": "alert", "data": {
                    "severity": "warning", "message": f"Route recalculation failed: {str(e)}",
                    "alert_type": "system_error"
                }})
            finally:
                trip.status = TripStatus.active
        
        # Commit all DB changes
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"DB commit error: {e}")
            await db.rollback()
        
        return messages
    
    def _extract_route_coords(self, route_geojson: dict | None) -> list[list[float]]:
        """Extract [lat, lng] coordinate list from GeoJSON."""
        if not route_geojson:
            return []
        
        coords = route_geojson.get("coordinates", [])
        if not coords:
            # Might be stored as our internal format
            return route_geojson.get("route_coords", [])
        
        # GeoJSON coordinates are [lng, lat], convert to [lat, lng]
        return [[c[1], c[0]] for c in coords]
    
    def cleanup_trip(self, trip_id: str):
        """Clean up agent state for a completed trip."""
        self.monitoring_agents.pop(trip_id, None)
        self._last_trigger_progress.pop(trip_id, None)

# Global orchestrator instance
orchestrator = Orchestrator()
