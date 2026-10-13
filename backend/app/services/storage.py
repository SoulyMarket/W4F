"""S3-compatible object storage (section 5's Media endpoints, section 6.10:
presigned URLs only, mime/size checks, private bucket — never a public
bucket). Targets MinIO in every real environment (docker-compose.yml);
tests point the same boto3 client at a local moto_server instead, since
Docker can't run on this dev machine and MinIO's winget package is
currently broken — see PROGRESS.md. The S3 API surface used here
(presigned PUT/GET, head_object) is identical either way.
"""

from functools import lru_cache

import boto3
from botocore.client import Config

from app.core.config import Settings

UPLOAD_URL_EXPIRE_SECONDS = 15 * 60
DOWNLOAD_URL_EXPIRE_SECONDS = 15 * 60

ALLOWED_PHOTO_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO_MIME_TYPES = {"video/mp4"}
MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024


@lru_cache
def _build_s3_client(endpoint: str, access_key: str, secret_key: str, secure: bool):
    scheme = "https" if secure else "http"
    return boto3.client(
        "s3",
        endpoint_url=f"{scheme}://{endpoint}",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name="us-east-1",
    )


def get_s3_client(settings: Settings):
    """Cached per distinct (endpoint, keys) tuple so repeated calls within
    one process reuse the same boto3 client/connection pool instead of
    creating a new one per request."""
    return _build_s3_client(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
        settings.minio_secure,
    )


def validate_media_mime_and_size(kind: str, mime_type: str, size_bytes: int) -> str | None:
    """Returns an i18n error key if invalid, else None."""
    if kind == "photo":
        if mime_type not in ALLOWED_PHOTO_MIME_TYPES:
            return "errors.media_invalid_type"
        if size_bytes > MAX_PHOTO_SIZE_BYTES:
            return "errors.media_too_large"
    elif kind == "video":
        if mime_type not in ALLOWED_VIDEO_MIME_TYPES:
            return "errors.media_invalid_type"
        if size_bytes > MAX_VIDEO_SIZE_BYTES:
            return "errors.media_too_large"
    return None


def generate_upload_url(client, bucket: str, key: str, content_type: str) -> str:
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=UPLOAD_URL_EXPIRE_SECONDS,
    )


def generate_download_url(client, bucket: str, key: str) -> str:
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=DOWNLOAD_URL_EXPIRE_SECONDS,
    )
