import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import MEDIA_KIND_ENUM, UPLOAD_STATUS_ENUM, MediaKind, UploadStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class ReportMedia(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "report_media"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[MediaKind] = mapped_column(MEDIA_KIND_ENUM, nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    upload_status: Mapped[UploadStatus] = mapped_column(
        UPLOAD_STATUS_ENUM,
        nullable=False,
        default=UploadStatus.PENDING,
        server_default=UploadStatus.PENDING.value,
    )
