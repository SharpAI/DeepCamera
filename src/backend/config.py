from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://namucam:namucam@db:5432/namucam"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "namucam-incidents"
    MINIO_SECURE: bool = False

    # VLM (Aegis-compatible OpenAI endpoint)
    VLM_BASE_URL: str = "http://localhost:5405"
    VLM_MODEL: str = "qwen-vl"
    VLM_API_KEY: str = "none"

    # LLM agent
    LLM_BASE_URL: str = "http://localhost:5407"
    LLM_MODEL: str = "qwen3"
    LLM_API_KEY: str = "none"

    # go2rtc
    GO2RTC_URL: str = "http://go2rtc:1984"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # YOLO pre-filter confidence threshold
    YOLO_CONFIDENCE: float = 0.5

    # VLM analysis traffic prompt template
    VLM_SYSTEM_PROMPT: str = (
        "You are a city traffic surveillance AI. Analyze the camera frame and report: "
        "1) Any traffic accidents or near-misses. "
        "2) Suspicious or anomalous pedestrian behavior. "
        "3) Crowd anomalies, fights, or public safety threats. "
        "4) Abandoned objects, wrong-way vehicles, or road obstructions. "
        "Be concise. Output JSON with keys: incident_detected (bool), incident_type, "
        "severity (low/medium/high/critical), description, confidence (0-1)."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
