import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import PROJECT_STATUS_ENUM, SOLUTION_TYPE_ENUM, ProjectStatus, SolutionType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Project(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, unique=True
    )
    douar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("douars.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    solution_type: Mapped[SolutionType] = mapped_column(SOLUTION_TYPE_ENUM, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        PROJECT_STATUS_ENUM,
        nullable=False,
        default=ProjectStatus.NEW,
        server_default=ProjectStatus.NEW.value,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    planned_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
