import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.enums import AuditAction


class AuditLogOut(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: AuditAction
    entity_type: str
    entity_id: uuid.UUID | None
    old_value: dict | None
    new_value: dict | None
    ip: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("ip", mode="before")
    @classmethod
    def _stringify_ip(cls, v: object) -> str | None:
        # The ORM column is Postgres INET (`AuditLog.ip`), which
        # SQLAlchemy/psycopg hand back as `ipaddress.IPv4Address` /
        # `IPv6Address`, not `str` — despite the model's own `Mapped[str
        # | None]` hint, which only describes the Python-side intent, not
        # what the driver actually returns. Never caught by the test
        # suite because `TestClient` reports its host as the literal
        # string "testclient" (not a real IP), which `_client_ip()` in
        # `routes/auth.py` already filters down to `None` before it ever
        # reaches the audit log — so no test run has ever exercised this
        # field with a real address. Found live via the browser hitting
        # a real backend with a real client IP.
        return None if v is None else str(v)


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
