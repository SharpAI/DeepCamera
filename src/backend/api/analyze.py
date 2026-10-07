from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import httpx
import tempfile
import os

from backend.db.database import get_db
from backend.models.camera import Camera
from backend.models.incident import AnalysisJob
from backend.workers.tasks import analyze_frame_task
from backend.config import settings

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    camera_id: UUID
    custom_prompt: Optional[str] = None


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/trigger", response_model=AnalyzeResponse)
async def trigger_analysis(payload: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """Grab a snapshot from the camera and queue a VLM analysis job."""
    cam = await db.get(Camera, payload.camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not cam.is_active:
        raise HTTPException(status_code=400, detail="Camera is inactive")

    # Capture snapshot from go2rtc
    snap_path = await _capture_snapshot(cam.name)

    # Create job record
    job = AnalysisJob(camera_id=payload.camera_id, frame_path=snap_path, status="pending")
    db.add(job)
    await db.flush()

    # Queue Celery task
    task = analyze_frame_task.delay(
        str(payload.camera_id),
        snap_path,
        str(job.id),
    )
    job.celery_task_id = task.id

    return AnalyzeResponse(
        job_id=str(job.id),
        status="queued",
        message=f"Analysis queued for camera '{cam.name}'",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        result=job.result,
        error=job.error,
    )


async def _capture_snapshot(camera_name: str) -> str:
    """Download a JPEG snapshot from go2rtc and save to a temp file."""
    name = camera_name.replace(" ", "_")
    url = f"{settings.GO2RTC_URL}/snapshot?src={name}"
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            tmp.write(resp.content)
            tmp.flush()
        return tmp.name
    except Exception as exc:
        tmp.close()
        os.unlink(tmp.name)
        raise HTTPException(status_code=502, detail=f"Failed to capture snapshot: {exc}")
