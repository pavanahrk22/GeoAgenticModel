from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import logging
from app.db import get_db
from app.models import Trip, Vehicle, VehicleType, TripStatus
from app.schemas import TripCreate, TripResponse, SelectRouteRequest
from app.services.routing_client import get_route
from app.api.stream import manager
from app.api.simulate import sim_controller
from app.agents.orchestrator import orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(trip_data: TripCreate, db: AsyncSession = Depends(get_db)):
    # Create or reuse vehicle
    vehicle_id = trip_data.vehicle_id
    if not vehicle_id:
        new_vehicle = Vehicle(
            name=trip_data.vehicle_name or "Emergency Unit",
            vehicle_type=trip_data.vehicle_type or VehicleType.ambulance,
            status="active"
        )
        db.add(new_vehicle)
        await db.commit()
        await db.refresh(new_vehicle)
        vehicle_id = new_vehicle.id

    # Fetch real route from routing service
    origin = (trip_data.origin_lat, trip_data.origin_lng)
    destination = (trip_data.destination_lat, trip_data.destination_lng)
    
    try:
        route_data = await get_route(origin, destination, alternatives=False)
        routes = route_data.get("routes", [])
    except Exception as e:
        logger.error(f"Failed to fetch route: {e}")
        routes = []
    
    if routes:
        best_route = routes[0]
        # Store as GeoJSON LineString with internal [lat,lng] in a custom field
        route_coords = best_route["geometry"]  # Already [lat, lng] from routing_client
        planned_route = {
            "type": "LineString",
            "coordinates": [[c[1], c[0]] for c in route_coords],  # GeoJSON is [lng, lat]
            "route_coords": route_coords,  # Keep [lat, lng] for internal use
        }
        baseline_eta = best_route.get("duration", 1200.0)
        distance = best_route.get("distance", 0)
        logger.info(f"Route fetched: {distance}m, ETA: {baseline_eta}s")
    else:
        # Fallback: straight line
        planned_route = {
            "type": "LineString",
            "coordinates": [
                [trip_data.origin_lng, trip_data.origin_lat],
                [trip_data.destination_lng, trip_data.destination_lat]
            ],
            "route_coords": [
                [trip_data.origin_lat, trip_data.origin_lng],
                [trip_data.destination_lat, trip_data.destination_lng]
            ],
        }
        baseline_eta = 1200.0
        logger.warning("Using fallback straight-line route")

    new_trip = Trip(
        vehicle_id=vehicle_id,
        origin_lat=trip_data.origin_lat,
        origin_lng=trip_data.origin_lng,
        destination_lat=trip_data.destination_lat,
        destination_lng=trip_data.destination_lng,
        planned_route_geojson=planned_route,
        baseline_eta_seconds=baseline_eta,
        current_eta_seconds=baseline_eta,
    )
    db.add(new_trip)
    await db.commit()
    await db.refresh(new_trip)

    # Reload with relationships
    result = await db.execute(
        select(Trip)
        .options(selectinload(Trip.vehicle), selectinload(Trip.positions), selectinload(Trip.recommendations))
        .where(Trip.id == new_trip.id)
    )
    trip = result.scalar_one()
    return trip

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Trip)
        .options(selectinload(Trip.vehicle), selectinload(Trip.positions), selectinload(Trip.recommendations))
        .where(Trip.id == trip_id)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.post("/{trip_id}/select-route")
async def select_route(trip_id: str, req: SelectRouteRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Update trip's planned_route_geojson
    planned_route = {
        "type": "LineString",
        "coordinates": [[c[1], c[0]] for c in req.geometry],
        "route_coords": req.geometry,
    }
    trip.planned_route_geojson = planned_route
    trip.baseline_eta_seconds = req.duration
    trip.current_eta_seconds = req.duration
    trip.status = TripStatus.active

    await db.commit()
    await db.refresh(trip)

    # Signal running simulation to switch path
    sim_controller.set_pending_route(trip_id, req.geometry)
    orchestrator._last_trigger_progress.pop(trip_id, None)

    # Broadcast route_update with selected: True
    await manager.broadcast_to_trip(trip_id, {
        "type": "route_update",
        "data": {
            "selected": True,
            "geometry": req.geometry,
            "distance": req.distance,
            "duration": req.duration,
            "alternatives": [],
        }
    })

    return {
        "status": "success",
        "message": "Route selected successfully",
        "trip_id": trip_id,
        "distance": req.distance,
        "duration": req.duration,
    }
