import uuid
from datetime import date, datetime

from geoalchemy2 import Geography
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import (
    INTERRUPTION_FREQUENCY_ENUM,
    PROBLEM_TYPE_ENUM,
    REPORT_STATUS_ENUM,
    SEVERITY_LEVEL_ENUM,
    WATER_SOURCE_ENUM,
    InterruptionFrequency,
    ProblemType,
    ReportStatus,
    SeverityLevel,
    WaterSource,
)
from app.models.mixins import TimestampMixin


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    # Generated on the phone (offline-first, idempotent sync) — never a
    # server-side default.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    douar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("douars.id"), nullable=False, index=True
    )
    moqaddem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    water_source: Mapped[WaterSource] = mapped_column(WATER_SOURCE_ENUM, nullable=False)
    problem_type: Mapped[ProblemType] = mapped_column(PROBLEM_TYPE_ENUM, nullable=False)
    problem_started_on: Mapped[date] = mapped_column(Date, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    interruption_frequency: Mapped[InterruptionFrequency] = mapped_column(
        INTERRUPTION_FREQUENCY_ENUM, nullable=False
    )
    has_alternative_source: Mapped[bool] = mapped_column(Boolean, nullable=False)
    alternative_distance_km: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    severity_reported: Mapped[SeverityLevel] = mapped_column(SEVERITY_LEVEL_ENUM, nullable=False)
    water_quality_risk: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    affected_families: Mapped[int] = mapped_column(Integer, nullable=False)
    affected_people: Mapped[int] = mapped_column(Integer, nullable=False)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Added by a later migration once PostGIS is available.
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    location_accuracy_m: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[ReportStatus] = mapped_column(
        REPORT_STATUS_ENUM,
        nullable=False,
        default=ReportStatus.SUBMITTED,
        server_default=ReportStatus.SUBMITTED.value,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
