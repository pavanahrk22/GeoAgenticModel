import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Optional
from app.services.geo import haversine_distance
from app.services.routing_client import get_route

logger = logging.getLogger(__name__)

DEFAULT_ORIGIN = (12.9716, 77.5946)
DEFAULT_DESTINATION = (12.9352, 77.6245)
SIMULATOR_TICK_INTERVAL = 2.0

class SimulatorState:
    def __init__(self):
        self.active_simulations: dict[str, asyncio.Task] = {}
        self.congestion_factors: dict[str, float] = {}

simulator_state = SimulatorState()

async def start_simulation(trip_id: str, route_coords: list[list[float]], on_position_callback, on_complete_callback):
    async def run_sim():
        try:
            total_points = len(route_coords)
            for i in range(total_points - 1):
                start = route_coords[i]
                end = route_coords[i+1]
                
                dist = haversine_distance(start[0], start[1], end[0], end[1])
                speed_kmh = 40.0
                speed_ms = speed_kmh * (1000.0 / 3600.0)
                
                segment_key = f"{trip_id}_{i}"
                congestion = simulator_state.congestion_factors.get(segment_key, 1.0)
                actual_speed = speed_ms * (1.0 / max(0.1, congestion))
                
                time_needed = dist / actual_speed if actual_speed > 0 else 0
                steps = max(1, int(time_needed / SIMULATOR_TICK_INTERVAL))
                
                for step in range(steps):
                    frac = step / steps
                    lat = start[0] + (end[0] - start[0]) * frac + random.uniform(-0.00005, 0.00005)
                    lng = start[1] + (end[1] - start[1]) * frac + random.uniform(-0.00005, 0.00005)
                    await on_position_callback(lat, lng)
                    await asyncio.sleep(SIMULATOR_TICK_INTERVAL)
                    
            if on_complete_callback:
                await on_complete_callback()
        except asyncio.CancelledError:
            logger.info(f"Simulation {trip_id} cancelled.")
            
    task = asyncio.create_task(run_sim())
    simulator_state.active_simulations[trip_id] = task

def stop_simulation(trip_id: str):
    if trip_id in simulator_state.active_simulations:
        simulator_state.active_simulations[trip_id].cancel()
        del simulator_state.active_simulations[trip_id]

def inject_congestion(segment_index: int, factor: float, trip_id: str = "demo"):
    segment_key = f"{trip_id}_{segment_index}"
    simulator_state.congestion_factors[segment_key] = factor

async def run_demo_scenario(trip_id: str, route_coords: list[list[float]], on_position, on_complete):
    await start_simulation(trip_id, route_coords, on_position, on_complete)
