import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ReportStatus, SeverityLevel, ValidationDecision


class ValidationCreate(BaseModel):
    decision: ValidationDecision
    comment: str | None = None
    proposed_solution: str | None = None
    urgency_opinion: SeverityLevel | None = None


class ValidationCreateOut(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    expert_id: uuid.UUID
    decision: ValidationDecision
    comment: str | None
    proposed_solution: str | None
    urgency_opinion: SeverityLevel | None
    created_at: datetime
    new_report_status: ReportStatus

    model_config = {"from_attributes": True}
