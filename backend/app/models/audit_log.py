import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AUDIT_ACTION_ENUM, AuditAction
from app.models.mixins import UUIDPKMixin


class AuditLog(UUIDPKMixin, Base):
    """Append-only. A DB migration revokes UPDATE/DELETE on this table for
    the application role and adds a trigger that rejects both, so even a
    bug or a compromised app role cannot rewrite history (section 6.6)."""

    __tablename__ = "audit_log"

    # Nullable: a failed login against an email that doesn't exist has no
    # actor to attribute it to, but the attempt is still logged.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(AUDIT_ACTION_ENUM, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
