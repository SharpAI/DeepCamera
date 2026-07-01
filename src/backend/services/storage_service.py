import io
from minio import Minio
from minio.error import S3Error
from backend.config import settings

_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        try:
            if not _client.bucket_exists(settings.MINIO_BUCKET):
                _client.make_bucket(settings.MINIO_BUCKET)
        except S3Error:
            pass
    return _client


def upload_snapshot(incident_id: str, file_path: str) -> str:
    client = get_client()
    object_name = f"incidents/{incident_id}/snapshot.jpg"
    client.fput_object(settings.MINIO_BUCKET, object_name, file_path)
    return f"/{settings.MINIO_BUCKET}/{object_name}"


def get_presigned_url(object_path: str, expires_seconds: int = 3600) -> str:
    from datetime import timedelta
    client = get_client()
    # object_path format: /bucket/object_name
    parts = object_path.lstrip("/").split("/", 1)
    bucket, obj = parts[0], parts[1]
    return client.presigned_get_object(bucket, obj, expires=timedelta(seconds=expires_seconds))
