from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum
from backend.db.database import Base


class SeverityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentType(str, enum.Enum):
    traffic_accident = "traffic_accident"
    suspicious_person = "suspicious_person"
    crowd_anomaly = "crowd_anomaly"
    wrong_way = "wrong_way"
    abandoned_object = "abandoned_object"
    fight = "fight"
    fire_smoke = "fire_smoke"
    other = "other"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False)
    incident_type = Column(Enum(IncidentType), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    description = Column(Text)           # VLM-generated description
    vlm_raw_response = Column(Text)      # full VLM output
    snapshot_url = Column(String(1024))  # MinIO URL
    clip_url = Column(String(1024))      # MinIO video clip URL
    confidence = Column(Float)           # detection confidence
    objects_detected = Column(JSONB)     # YOLO detections JSON
    location_detail = Column(String(512))
    resolved = Column(String(10), default="open")  # open / resolved / false_alarm
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False)
    celery_task_id = Column(String(255))
    status = Column(String(50), default="pending")  # pending/running/done/failed
    frame_path = Column(String(1024))
    result = Column(JSONB)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
