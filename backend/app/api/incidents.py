from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db import get_db
from app.models import Incident
from app.schemas import IncidentCreate, IncidentResponse
from app.api.stream import manager

router = APIRouter()

@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(incident_data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    new_incident = Incident(
        type=incident_data.type,
        lat=incident_data.lat,
        lng=incident_data.lng,
        radius_meters=incident_data.radius_meters,
        severity=incident_data.severity,
        description=incident_data.description,
        active=True
    )
    db.add(new_incident)
    await db.commit()
    await db.refresh(new_incident)
    
    # Broadcast to all active websockets
    await manager.broadcast_all({
        "type": "alert",
        "data": {
            "incident_id": new_incident.id,
            "type": new_incident.type.value,
            "severity": new_incident.severity.value,
            "lat": new_incident.lat,
            "lng": new_incident.lng,
            "description": new_incident.description
        }
    })
    
    return new_incident

@router.get("/", response_model=List[IncidentResponse])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.active == True))
    return result.scalars().all()

@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.active = False
    await db.commit()
    return None
