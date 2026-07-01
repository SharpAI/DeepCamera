from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, HttpUrl
from typing import Optional
from uuid import UUID
import httpx

from backend.db.database import get_db
from backend.models.camera import Camera
from backend.config import settings

router = APIRouter(prefix="/cameras", tags=["cameras"])


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    notes: Optional[str] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CameraResponse(BaseModel):
    id: UUID
    name: str
    rtsp_url: str
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    district: Optional[str]
    is_active: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CameraResponse])
async def list_cameras(
    district: Optional[str] = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(Camera)
    if district:
        q = q.where(Camera.district == district)
    if active_only:
        q = q.where(Camera.is_active == True)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(payload: CameraCreate, db: AsyncSession = Depends(get_db)):
    cam = Camera(**payload.model_dump())
    db.add(cam)
    await db.flush()

    # Register stream in go2rtc
    await _register_go2rtc(cam.name, cam.rtsp_url)

    return cam


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: UUID, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: UUID, payload: CameraUpdate, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(cam, field, value)
    return cam


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: UUID, db: AsyncSession = Depends(get_db)):
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    await db.delete(cam)


@router.get("/{camera_id}/stream-url")
async def get_stream_url(camera_id: UUID, db: AsyncSession = Depends(get_db)):
    """Return go2rtc HLS / WebRTC URLs for the camera."""
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    name = cam.name.replace(" ", "_")
    return {
        "hls": f"{settings.GO2RTC_URL}/stream.m3u8?src={name}",
        "webrtc": f"{settings.GO2RTC_URL}/webrtc?src={name}",
        "snapshot": f"{settings.GO2RTC_URL}/snapshot?src={name}",
    }


async def _register_go2rtc(name: str, rtsp_url: str):
    """Push RTSP stream into go2rtc at runtime via its API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.put(
                f"{settings.GO2RTC_URL}/api/streams",
                params={"name": name.replace(" ", "_"), "src": rtsp_url},
            )
    except Exception:
        pass  # go2rtc may not be running in dev; non-fatal
