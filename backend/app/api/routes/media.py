import hashlib
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, get_settings, require_roles
from app.core.config import Settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.douar import Douar
from app.models.enums import UploadStatus, UserRole
from app.models.report import Report
from app.models.report_media import ReportMedia
from app.models.user import User
from app.schemas.media import (
    MediaCompleteRequest,
    MediaOut,
    MediaUploadUrlOut,
    MediaUploadUrlRequest,
)
from app.services.storage import (
    UPLOAD_URL_EXPIRE_SECONDS,
    generate_download_url,
    generate_upload_url,
    get_s3_client,
    validate_media_mime_and_size,
)
from app.services.territory_scope import territory_scope_filter

router = APIRouter(prefix="/media", tags=["media"])

_require_any = require_roles(*list(UserRole))

_EXTENSION_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}


@router.post("/upload-url", response_model=MediaUploadUrlOut)
def create_upload_url(
    body: MediaUploadUrlRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    settings: Settings = Depends(get_settings),
) -> MediaUploadUrlOut:
    lang = get_request_language(request)
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    report = (
        db.query(Report)
        .join(Douar, Report.douar_id == Douar.id)
        .filter(Report.id == body.report_id, scope)
        .first()
    )
    if report is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            key="errors.not_found",
            lang=lang,
        )

    error_key = validate_media_mime_and_size(body.kind.value, body.mime_type, body.size_bytes)
    if error_key:
        raise ApiError(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, key=error_key, lang=lang)

    extension = _EXTENSION_BY_MIME.get(body.mime_type, "")
    object_key = f"reports/{report.id}/{uuid.uuid4()}{extension}"

    media = ReportMedia(
        report_id=report.id,
        kind=body.kind,
        object_key=object_key,
        mime_type=body.mime_type,
        size_bytes=body.size_bytes,
        upload_status=UploadStatus.PENDING,
    )
    db.add(media)
    db.commit()
    db.refresh(media)

    client = get_s3_client(settings)
    upload_url = generate_upload_url(client, settings.minio_bucket, object_key, body.mime_type)

    return MediaUploadUrlOut(
        media_id=media.id,
        upload_url=upload_url,
        object_key=object_key,
        expires_in=UPLOAD_URL_EXPIRE_SECONDS,
    )


@router.post("/{media_id}/refresh-upload-url", response_model=MediaUploadUrlOut)
def refresh_upload_url(
    media_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    settings: Settings = Depends(get_settings),
) -> MediaUploadUrlOut:
    """A presigned PUT URL expires in `UPLOAD_URL_EXPIRE_SECONDS` (15 min) —
    short enough that the phone's Wi-Fi-only upload constraint (section 8)
    can easily outlast it. Re-signs the *same* `object_key` a pending media
    row already has rather than registering a new row, so a deferred
    upload never has to go through `/upload-url` again (which would create
    a duplicate `report_media` row)."""
    lang = get_request_language(request)
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    media = (
        db.query(ReportMedia)
        .join(Report, ReportMedia.report_id == Report.id)
        .join(Douar, Report.douar_id == Douar.id)
        .filter(ReportMedia.id == media_id, scope)
        .first()
    )
    if media is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            key="errors.not_found",
            lang=lang,
        )
    if media.upload_status != UploadStatus.PENDING:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            key="errors.invalid_status_transition",
            lang=lang,
        )

    client = get_s3_client(settings)
    upload_url = generate_upload_url(
        client, settings.minio_bucket, media.object_key, media.mime_type
    )

    return MediaUploadUrlOut(
        media_id=media.id,
        upload_url=upload_url,
        object_key=media.object_key,
        expires_in=UPLOAD_URL_EXPIRE_SECONDS,
    )


@router.post("/{media_id}/complete", response_model=MediaOut)
def complete_upload(
    media_id: uuid.UUID,
    body: MediaCompleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    settings: Settings = Depends(get_settings),
) -> MediaOut:
    lang = get_request_language(request)
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    media = (
        db.query(ReportMedia)
        .join(Report, ReportMedia.report_id == Report.id)
        .join(Douar, Report.douar_id == Douar.id)
        .filter(ReportMedia.id == media_id, scope)
        .first()
    )
    if media is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            key="errors.not_found",
            lang=lang,
        )

    client = get_s3_client(settings)
    try:
        head = client.head_object(Bucket=settings.minio_bucket, Key=media.object_key)
    except client.exceptions.ClientError:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            key="errors.not_found",
            lang=lang,
        ) from None

    if head["ContentLength"] != media.size_bytes:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            key="errors.media_too_large",
            lang=lang,
        )

    obj = client.get_object(Bucket=settings.minio_bucket, Key=media.object_key)
    actual_sha256 = hashlib.sha256(obj["Body"].read()).hexdigest()
    if actual_sha256 != body.sha256:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            key="errors.validation_error",
            lang=lang,
        )

    media.sha256 = body.sha256
    media.upload_status = UploadStatus.UPLOADED
    db.commit()
    db.refresh(media)

    download_url = generate_download_url(client, settings.minio_bucket, media.object_key)
    return MediaOut(
        id=media.id,
        report_id=media.report_id,
        kind=media.kind,
        mime_type=media.mime_type,
        size_bytes=media.size_bytes,
        upload_status=media.upload_status.value,
        download_url=download_url,
    )
