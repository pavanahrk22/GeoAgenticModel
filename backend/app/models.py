import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Enum, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
import enum

def generate_uuid():
    return str(uuid.uuid4())

class VehicleType(str, enum.Enum):
    ambulance = "ambulance"
    fire_truck = "fire_truck"
    police = "police"

class TripStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    rerouting = "rerouting"
    completed = "completed"
    cancelled = "cancelled"

class IncidentType(str, enum.Enum):
    accident = "accident"
    roadblock = "roadblock"
    construction = "construction"
    flood = "flood"

class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    status = Column(String, default="available")

    trips = relationship("Trip", back_populates="vehicle")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True, default=generate_uuid)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    planned_route_geojson = Column(JSON, nullable=True)
    baseline_eta_seconds = Column(Float, nullable=True)
    current_eta_seconds = Column(Float, nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="trips")
    positions = relationship("Position", back_populates="trip", order_by="Position.timestamp")
    segments = relationship("TrafficSegment", back_populates="trip")
    recommendations = relationship("Recommendation", back_populates="trip")

class Position(Base):
    __tablename__ = "positions"

    id = Column(String, primary_key=True, default=generate_uuid)
    trip_id = Column(String, ForeignKey("trips.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    on_route = Column(Boolean, default=True)

    trip = relationship("Trip", back_populates="positions")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(Enum(IncidentType), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius_meters = Column(Float, default=100.0)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.medium)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrafficSegment(Base):
    __tablename__ = "traffic_segments"

    id = Column(String, primary_key=True, default=generate_uuid)
    trip_id = Column(String, ForeignKey("trips.id"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_lat = Column(Float, nullable=False)
    start_lng = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lng = Column(Float, nullable=False)
    congestion_factor = Column(Float, default=1.0)
    speed_kmh = Column(Float, nullable=True)

    trip = relationship("Trip", back_populates="segments")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    trip_id = Column(String, ForeignKey("trips.id"), nullable=False)
    trigger_type = Column(Text, nullable=False)
    routes_json = Column(JSON, nullable=False)
    chosen_route_index = Column(Integer, nullable=True)
    explanation = Column(Text, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="recommendations")
