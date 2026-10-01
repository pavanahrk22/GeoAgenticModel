from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import asyncio
import math
import random
import logging
from datetime import datetime, timezone

from app.db import get_db, AsyncSessionLocal
from app.models import Trip, Incident, TripStatus
from app.schemas import SimulateRequest
from app.api.stream import manager
from app.agents.orchestrator import orchestrator
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class SimulationController:
    def __init__(self):
        self.active_tasks: dict[str, asyncio.Task] = {}

    async def run_simulation(self, trip_id: str):
        """Walk along the planned route, emitting GPS pings processed through the orchestrator."""
        settings = get_settings()
        tick = settings.SIMULATOR_TICK_INTERVAL

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Trip).where(Trip.id == trip_id))
            trip = result.scalar_one_or_none()
            if not trip:
                logger.error(f"Trip {trip_id} not found for simulation")
                return

            route_geojson = trip.planned_route_geojson
            route_coords = route_geojson.get("route_coords", [])
            if not route_coords and route_geojson.get("coordinates"):
                route_coords = [[c[1], c[0]] for c in route_geojson["coordinates"]]

            if len(route_coords) < 2:
                logger.error(f"Not enough route coordinates for trip {trip_id}")
                return

            trip.status = TripStatus.active
            await db.commit()

        logger.info(f"Simulation started for trip {trip_id} with {len(route_coords)} waypoints")

        # Broadcast trip started
        await manager.broadcast_to_trip(trip_id, {
            "type": "alert",
            "data": {"severity": "info", "message": "Simulation started. Vehicle is en route.", "alert_type": "system"}
        })

        try:
            base_speed_kmh = 40.0
            total_points = len(route_coords)

            for i in range(total_points - 1):
                if trip_id not in self.active_tasks:
                    break

                start = route_coords[i]
                end = route_coords[i + 1]

                # Calculate segment distance and steps
                dlat = end[0] - start[0]
                dlng = end[1] - start[1]
                seg_dist_deg = math.sqrt(dlat**2 + dlng**2)
                seg_dist_m = seg_dist_deg * 111320.0  # approximate

                speed_ms = base_speed_kmh * (1000.0 / 3600.0)
                time_needed = seg_dist_m / speed_ms if speed_ms > 0 else 1.0
                steps = max(1, int(time_needed / tick))

                heading = math.degrees(math.atan2(dlng, dlat)) % 360

                for step in range(steps):
                    if trip_id not in self.active_tasks:
                        break

                    frac = step / steps
                    lat = start[0] + dlat * frac + random.uniform(-0.00003, 0.00003)
                    lng = start[1] + dlng * frac + random.uniform(-0.00003, 0.00003)
                    speed = base_speed_kmh + random.uniform(-5, 5)

                    # Process through orchestrator with a fresh DB session
                    async with AsyncSessionLocal() as db:
                        ws_messages = await orchestrator.process_gps_ping(
                            trip_id, lat, lng, speed, heading, db
                        )
                        for msg in ws_messages:
                            await manager.broadcast_to_trip(trip_id, msg)

                    await asyncio.sleep(tick)

            # Trip completed
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Trip).where(Trip.id == trip_id))
                trip = result.scalar_one_or_none()
                if trip:
                    trip.status = TripStatus.completed
                    await db.commit()

            await manager.broadcast_to_trip(trip_id, {
                "type": "alert",
                "data": {"severity": "info", "message": "Vehicle has arrived at destination.", "alert_type": "completed"}
            })
            logger.info(f"Simulation completed for trip {trip_id}")

        except asyncio.CancelledError:
            logger.info(f"Simulation cancelled for trip {trip_id}")
        except Exception as e:
            logger.error(f"Simulation error for trip {trip_id}: {e}", exc_info=True)
        finally:
            self.active_tasks.pop(trip_id, None)
            orchestrator.cleanup_trip(trip_id)

    async def run_demo_scenario(self, trip_id: str):
        """Run a scripted demo: normal trip -> inject incident -> reroute."""
        settings = get_settings()
        tick = settings.SIMULATOR_TICK_INTERVAL

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Trip).where(Trip.id == trip_id))
            trip = result.scalar_one_or_none()
            if not trip:
                logger.error(f"Trip {trip_id} not found")
                return

            route_geojson = trip.planned_route_geojson
            route_coords = route_geojson.get("route_coords", [])
            if not route_coords and route_geojson.get("coordinates"):
                route_coords = [[c[1], c[0]] for c in route_geojson["coordinates"]]

            if len(route_coords) < 2:
                return

            trip.status = TripStatus.active
            await db.commit()

        logger.info(f"Demo scenario started for trip {trip_id}")

        await manager.broadcast_to_trip(trip_id, {
            "type": "alert",
            "data": {"severity": "info", "message": "Demo scenario started: Normal driving phase.", "alert_type": "system"}
        })

        try:
            base_speed_kmh = 40.0
            total_points = len(route_coords)
            # Phase 1: Drive normally for first 30% of route
            phase1_end = int(total_points * 0.3)
            # Phase 2: Inject incident at ~40% of route, continue driving
            incident_point_idx = int(total_points * 0.4)
            incident_injected = False
            incident_id = None

            for i in range(total_points - 1):
                if trip_id not in self.active_tasks:
                    break

                start = route_coords[i]
                end = route_coords[i + 1]
                dlat = end[0] - start[0]
                dlng = end[1] - start[1]
                seg_dist_deg = math.sqrt(dlat**2 + dlng**2)
                seg_dist_m = seg_dist_deg * 111320.0
                speed_ms = base_speed_kmh * (1000.0 / 3600.0)
                time_needed = seg_dist_m / speed_ms if speed_ms > 0 else 1.0
                steps = max(1, int(time_needed / tick))
                heading = math.degrees(math.atan2(dlng, dlat)) % 360

                # Phase 2: Inject incident ahead
                if i >= phase1_end and not incident_injected and incident_point_idx < total_points:
                    inc_point = route_coords[incident_point_idx]
                    async with AsyncSessionLocal() as db:
                        from app.models import Incident as IncidentModel, IncidentType, IncidentSeverity
                        new_incident = IncidentModel(
                            type=IncidentType.accident,
                            lat=inc_point[0],
                            lng=inc_point[1],
                            radius_meters=150.0,
                            severity=IncidentSeverity.high,
                            description="Major accident blocking the road ahead",
                            active=True,
                        )
                        db.add(new_incident)
                        await db.commit()
                        await db.refresh(new_incident)
                        incident_id = new_incident.id

                    await manager.broadcast_to_trip(trip_id, {
                        "type": "alert",
                        "data": {
                            "severity": "critical",
                            "message": f"DEMO: Accident injected at ({inc_point[0]:.4f}, {inc_point[1]:.4f}). System will detect and suggest reroute.",
                            "alert_type": "incident",
                            "incident": {"lat": inc_point[0], "lng": inc_point[1], "radius": 150.0, "type": "accident"}
                        }
                    })
                    incident_injected = True
                    logger.info(f"Demo: Accident injected at waypoint {incident_point_idx}")

                for step in range(steps):
                    if trip_id not in self.active_tasks:
                        break
                    frac = step / steps
                    lat = start[0] + dlat * frac + random.uniform(-0.00003, 0.00003)
                    lng = start[1] + dlng * frac + random.uniform(-0.00003, 0.00003)
                    speed = base_speed_kmh + random.uniform(-5, 5)

                    async with AsyncSessionLocal() as db:
                        ws_messages = await orchestrator.process_gps_ping(
                            trip_id, lat, lng, speed, heading, db
                        )
                        for msg in ws_messages:
                            await manager.broadcast_to_trip(trip_id, msg)

                    await asyncio.sleep(tick)

            # Cleanup: deactivate demo incident
            if incident_id:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Incident).where(Incident.id == incident_id))
                    inc = result.scalar_one_or_none()
                    if inc:
                        inc.active = False
                        await db.commit()

            # Complete trip
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Trip).where(Trip.id == trip_id))
                trip = result.scalar_one_or_none()
                if trip:
                    trip.status = TripStatus.completed
                    await db.commit()

            await manager.broadcast_to_trip(trip_id, {
                "type": "alert",
                "data": {"severity": "info", "message": "Demo scenario completed.", "alert_type": "completed"}
            })

        except asyncio.CancelledError:
            logger.info(f"Demo scenario cancelled for trip {trip_id}")
        except Exception as e:
            logger.error(f"Demo scenario error: {e}", exc_info=True)
        finally:
            self.active_tasks.pop(trip_id, None)
            orchestrator.cleanup_trip(trip_id)

    def stop(self, trip_id: str):
        task = self.active_tasks.pop(trip_id, None)
        if task:
            task.cancel()


sim_controller = SimulationController()


class TripIDRequest(BaseModel):
    trip_id: str


@router.post("/start")
async def start_simulation(req: TripIDRequest):
    if req.trip_id in sim_controller.active_tasks:
        raise HTTPException(status_code=400, detail="Simulation already running for this trip")
    task = asyncio.create_task(sim_controller.run_simulation(req.trip_id))
    sim_controller.active_tasks[req.trip_id] = task
    return {"message": "Simulation started", "trip_id": req.trip_id}


@router.post("/stop")
async def stop_simulation(req: TripIDRequest):
    sim_controller.stop(req.trip_id)
    return {"message": "Simulation stopped", "trip_id": req.trip_id}


@router.post("/scenario")
async def run_scenario(req: TripIDRequest):
    if req.trip_id in sim_controller.active_tasks:
        raise HTTPException(status_code=400, detail="Simulation already running for this trip")
    task = asyncio.create_task(sim_controller.run_demo_scenario(req.trip_id))
    sim_controller.active_tasks[req.trip_id] = task
    return {"message": "Demo scenario started", "trip_id": req.trip_id}
