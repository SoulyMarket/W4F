import uuid

from pydantic import BaseModel, Field

from app.models.enums import MediaKind


class MediaUploadUrlRequest(BaseModel):
    report_id: uuid.UUID
    kind: MediaKind
    mime_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)


class MediaUploadUrlOut(BaseModel):
    media_id: uuid.UUID
    upload_url: str
    object_key: str
    expires_in: int


class MediaCompleteRequest(BaseModel):
    sha256: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")


class MediaOut(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    kind: MediaKind
    mime_type: str
    size_bytes: int
    upload_status: str
    download_url: str | None = None

    model_config = {"from_attributes": True}
