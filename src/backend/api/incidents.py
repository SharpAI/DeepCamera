from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

from backend.db.database import get_db
from backend.models.incident import Incident, IncidentType, SeverityLevel

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentResponse(BaseModel):
    id: UUID
    camera_id: UUID
    incident_type: IncidentType
    severity: SeverityLevel
    description: Optional[str]
    snapshot_url: Optional[str]
    clip_url: Optional[str]
    confidence: Optional[float]
    objects_detected: Optional[dict]
    resolved: str
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ResolvePayload(BaseModel):
    status: str  # resolved / false_alarm
    resolved_by: Optional[str] = None


class IncidentStats(BaseModel):
    total: int
    by_type: dict
    by_severity: dict
    by_camera: dict


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    camera_id: Optional[UUID] = None,
    incident_type: Optional[IncidentType] = None,
    severity: Optional[SeverityLevel] = None,
    resolved: Optional[str] = None,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Incident).order_by(Incident.occurred_at.desc())

    if camera_id:
        q = q.where(Incident.camera_id == camera_id)
    if incident_type:
        q = q.where(Incident.incident_type == incident_type)
    if severity:
        q = q.where(Incident.severity == severity)
    if resolved:
        q = q.where(Incident.resolved == resolved)
    if from_time:
        q = q.where(Incident.occurred_at >= from_time)
    if to_time:
        q = q.where(Incident.occurred_at <= to_time)

    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", response_model=IncidentStats)
async def get_stats(
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Incident)
    if from_time:
        q = q.where(Incident.occurred_at >= from_time)
    if to_time:
        q = q.where(Incident.occurred_at <= to_time)

    result = await db.execute(q)
    incidents = result.scalars().all()

    by_type: dict = {}
    by_severity: dict = {}
    by_camera: dict = {}

    for inc in incidents:
        by_type[inc.incident_type] = by_type.get(inc.incident_type, 0) + 1
        by_severity[inc.severity] = by_severity.get(inc.severity, 0) + 1
        cam_key = str(inc.camera_id)
        by_camera[cam_key] = by_camera.get(cam_key, 0) + 1

    return IncidentStats(
        total=len(incidents),
        by_type=by_type,
        by_severity=by_severity,
        by_camera=by_camera,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    inc = await db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.patch("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: UUID,
    payload: ResolvePayload,
    db: AsyncSession = Depends(get_db),
):
    inc = await db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if payload.status not in ("resolved", "false_alarm"):
        raise HTTPException(status_code=400, detail="status must be 'resolved' or 'false_alarm'")

    inc.resolved = payload.status
    inc.resolved_by = payload.resolved_by
    from datetime import timezone
    inc.resolved_at = datetime.now(timezone.utc)
    return inc
