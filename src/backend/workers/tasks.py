import asyncio
import json
from datetime import datetime, timezone
from backend.workers.celery_app import celery_app
from backend.config import settings


@celery_app.task(bind=True, name="analyze_frame")
def analyze_frame_task(self, camera_id: str, frame_path: str, job_id: str):
    """Celery task: run VLM analysis on a frame and save incident if detected."""
    return asyncio.get_event_loop().run_until_complete(
        _analyze_and_store(self, camera_id, frame_path, job_id)
    )


async def _analyze_and_store(task, camera_id: str, frame_path: str, job_id: str):
    from backend.services.vlm_service import analyze_frame
    from backend.db.database import AsyncSessionLocal
    from backend.models.incident import Incident, AnalysisJob, IncidentType, SeverityLevel
    from sqlalchemy import update
    import uuid

    async with AsyncSessionLocal() as session:
        # Mark job as running
        await session.execute(
            update(AnalysisJob).where(AnalysisJob.id == job_id).values(status="running")
        )
        await session.commit()

        try:
            result = await analyze_frame(frame_path, camera_id)

            if result.get("incident_detected"):
                incident = Incident(
                    camera_id=camera_id,
                    incident_type=result.get("incident_type", "other"),
                    severity=result.get("severity", "low"),
                    description=result.get("description", ""),
                    vlm_raw_response=json.dumps(result),
                    confidence=result.get("confidence", 0.0),
                    occurred_at=datetime.now(timezone.utc),
                )
                session.add(incident)

                # Publish real-time alert via Redis pub/sub
                import redis as redis_lib
                r = redis_lib.from_url(settings.REDIS_URL)
                r.publish("namucam:alerts", json.dumps({
                    "type": "incident",
                    "camera_id": camera_id,
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                    "description": incident.description,
                    "occurred_at": incident.occurred_at.isoformat(),
                }))

            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id).values(
                    status="done",
                    result=result,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
            return result

        except Exception as exc:
            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id).values(
                    status="failed", error=str(exc)
                )
            )
            await session.commit()
            raise
