import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import (
    InterruptionFrequency,
    ProblemType,
    ReportStatus,
    SeverityLevel,
    WaterSource,
)


class ReportMediaOut(BaseModel):
    id: uuid.UUID
    kind: str
    object_key: str
    mime_type: str
    upload_status: str

    model_config = {"from_attributes": True}


class PriorityBreakdownEntryOut(BaseModel):
    criterion: str
    value: Any
    weight: float
    points: float
    reason_key: str
    reason_params: dict
    reason: str  # reason_key/params rendered via app.i18n in the caller's language


class PriorityOut(BaseModel):
    score: int
    breakdown: list[PriorityBreakdownEntryOut]
    computed_at: datetime


class ValidationOut(BaseModel):
    id: uuid.UUID
    expert_id: uuid.UUID
    decision: str
    comment: str | None
    proposed_solution: str | None
    urgency_opinion: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: uuid.UUID
    douar_id: uuid.UUID
    moqaddem_id: uuid.UUID
    water_source: WaterSource
    problem_type: ProblemType
    problem_started_on: date
    duration_days: int
    interruption_frequency: InterruptionFrequency
    has_alternative_source: bool
    alternative_distance_km: float | None
    severity_reported: SeverityLevel
    water_quality_risk: bool
    affected_families: int
    affected_people: int
    observations: str | None
    lat: float | None
    lon: float | None
    location_accuracy_m: float | None
    collected_at: datetime
    synced_at: datetime | None
    status: ReportStatus
    version: int
    score: int | None = None


class ReportListOut(BaseModel):
    items: list[ReportOut]
    total: int
    page: int
    page_size: int


class ReportDetailOut(ReportOut):
    media: list[ReportMediaOut]
    priority: PriorityOut | None
    validations: list[ValidationOut]
