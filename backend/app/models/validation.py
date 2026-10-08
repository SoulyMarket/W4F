import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import (
    SEVERITY_LEVEL_ENUM,
    VALIDATION_DECISION_ENUM,
    SeverityLevel,
    ValidationDecision,
)
from app.models.mixins import UUIDPKMixin


class Validation(UUIDPKMixin, Base):
    __tablename__ = "validations"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    decision: Mapped[ValidationDecision] = mapped_column(VALIDATION_DECISION_ENUM, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency_opinion: Mapped[SeverityLevel | None] = mapped_column(
        SEVERITY_LEVEL_ENUM, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
