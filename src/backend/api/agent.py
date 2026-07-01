from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone

from backend.db.database import get_db
from backend.models.incident import Incident
from backend.models.camera import Camera
from backend.services.agent_service import query_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class QueryRequest(BaseModel):
    question: str
    # Optional time window — defaults to last 24 hours
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    incidents_in_context: int


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Natural language query over incident data."""
    now = datetime.now(timezone.utc)
    from_time = payload.from_time or (now - timedelta(hours=24))
    to_time = payload.to_time or now

    # Build context from DB
    incidents_result = await db.execute(
        select(Incident)
        .where(Incident.occurred_at >= from_time, Incident.occurred_at <= to_time)
        .order_by(Incident.occurred_at.desc())
        .limit(100)
    )
    incidents = incidents_result.scalars().all()

    cameras_result = await db.execute(select(Camera))
    cameras = {str(c.id): c.name for c in cameras_result.scalars().all()}

    context = {
        "query_window": {"from": from_time.isoformat(), "to": to_time.isoformat()},
        "total_incidents": len(incidents),
        "incidents": [
            {
                "id": str(inc.id),
                "camera": cameras.get(str(inc.camera_id), str(inc.camera_id)),
                "type": inc.incident_type,
                "severity": inc.severity,
                "description": inc.description,
                "occurred_at": inc.occurred_at.isoformat(),
                "resolved": inc.resolved,
                "confidence": inc.confidence,
            }
            for inc in incidents
        ],
    }

    answer = await query_agent(payload.question, context)

    return QueryResponse(
        question=payload.question,
        answer=answer,
        incidents_in_context=len(incidents),
    )


@router.post("/report")
async def generate_report(
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    district: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a structured shift/daily report using the LLM agent."""
    now = datetime.now(timezone.utc)
    from_time = from_time or (now - timedelta(hours=8))
    to_time = to_time or now

    q = select(Incident).where(
        Incident.occurred_at >= from_time,
        Incident.occurred_at <= to_time,
    )
    result = await db.execute(q)
    incidents = result.scalars().all()

    cam_q = select(Camera)
    if district:
        cam_q = cam_q.where(Camera.district == district)
    cam_result = await db.execute(cam_q)
    cameras = {str(c.id): {"name": c.name, "location": c.location} for c in cam_result.scalars().all()}

    context = {
        "report_period": {"from": from_time.isoformat(), "to": to_time.isoformat()},
        "district": district or "all",
        "cameras": cameras,
        "incidents": [
            {
                "camera": cameras.get(str(inc.camera_id), {}).get("name", "unknown"),
                "type": inc.incident_type,
                "severity": inc.severity,
                "description": inc.description,
                "occurred_at": inc.occurred_at.isoformat(),
                "resolved": inc.resolved,
            }
            for inc in incidents
            if str(inc.camera_id) in cameras
        ],
    }

    prompt = (
        "Generate a formal shift surveillance report based on the provided incident data. "
        "Include: executive summary, incident breakdown by type and severity, "
        "notable events, unresolved incidents requiring attention, and recommendations."
    )

    report_text = await query_agent(prompt, context)

    return {
        "period": {"from": from_time.isoformat(), "to": to_time.isoformat()},
        "district": district or "all",
        "total_incidents": len(context["incidents"]),
        "report": report_text,
    }
