from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from app.models import VehicleType, TripStatus, IncidentType, IncidentSeverity

class VehicleBase(BaseModel):
    name: str
    vehicle_type: VehicleType

class VehicleResponse(VehicleBase):
    id: str
    status: str

    class Config:
        from_attributes = True

class TripCreate(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    vehicle_id: Optional[str] = None
    vehicle_name: Optional[str] = "Emergency Vehicle"
    vehicle_type: Optional[VehicleType] = VehicleType.ambulance

class PositionResponse(BaseModel):
    id: str
    trip_id: str
    lat: float
    lng: float
    speed: float
    heading: float
    timestamp: datetime
    on_route: bool

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: str
    trip_id: str
    trigger_type: str
    routes_json: List[Dict[str, Any]]
    chosen_route_index: Optional[int]
    explanation: Optional[str]
    score_breakdown: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class TripResponse(BaseModel):
    id: str
    vehicle_id: str
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    planned_route_geojson: Optional[Dict[str, Any]]
    baseline_eta_seconds: Optional[float]
    current_eta_seconds: Optional[float]
    status: TripStatus
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleResponse] = None
    positions: Optional[List[PositionResponse]] = []
    recommendations: Optional[List[RecommendationResponse]] = []

    class Config:
        from_attributes = True

class IncidentCreate(BaseModel):
    type: IncidentType
    lat: float
    lng: float
    radius_meters: float = 100.0
    severity: IncidentSeverity = IncidentSeverity.medium
    description: Optional[str] = None

class IncidentResponse(IncidentCreate):
    id: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SimulateRequest(BaseModel):
    origin_lat: float = 12.9716
    origin_lng: float = 77.5946
    dest_lat: float = 12.9569
    dest_lng: float = 77.6534

class WSMessageType(str, Enum):
    position = "position"
    alert = "alert"
    recommendation = "recommendation"
    eta_update = "eta_update"
    route_update = "route_update"

class WSMessage(BaseModel):
    type: WSMessageType
    data: Dict[str, Any]
