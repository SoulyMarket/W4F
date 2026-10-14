import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import (
    InterruptionFrequency,
    MediaKind,
    ProblemType,
    ProjectStatus,
    SeverityLevel,
    SolutionType,
    ValidationDecision,
    WaterSource,
)
from app.schemas.notifications import NotificationOut
from app.schemas.reports import ReportOut


class SyncMediaPush(BaseModel):
    kind: MediaKind
    mime_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    captured_at: datetime | None = None


class SyncReportPush(BaseModel):
    # Client-generated (section 4) — the id idempotent push is keyed on.
    id: uuid.UUID
    douar_id: uuid.UUID
    water_source: WaterSource
    problem_type: ProblemType
    problem_started_on: date
    duration_days: int = Field(ge=0)
    interruption_frequency: InterruptionFrequency
    has_alternative_source: bool
    alternative_distance_km: float | None = None
    severity_reported: SeverityLevel
    water_quality_risk: bool
    affected_families: int = Field(ge=0)
    affected_people: int = Field(ge=0)
    observations: str | None = None
    lat: float | None = None
    lon: float | None = None
    location_accuracy_m: float | None = None
    collected_at: datetime
    media: list[SyncMediaPush] = []


class SyncPushRequest(BaseModel):
    reports: list[SyncReportPush]


class SyncMediaResultOut(BaseModel):
    media_id: uuid.UUID
    kind: MediaKind
    mime_type: str
    already_uploaded: bool
    upload_url: str | None = None
    object_key: str | None = None
    expires_in: int | None = None


class SyncReportResultOut(BaseModel):
    id: uuid.UUID
    status: Literal["created", "updated", "unchanged", "rejected"]
    error: str | None = None
    version: int | None = None
    media: list[SyncMediaResultOut] = []


class SyncPushOut(BaseModel):
    results: list[SyncReportResultOut]


class SyncDouarOut(BaseModel):
    id: uuid.UUID
    name_ar: str
    name_fr: str
    commune_id: uuid.UUID
    lat: float | None
    lon: float | None
    population: int | None
    families_count: int | None


class SyncValidationOut(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    expert_id: uuid.UUID
    decision: ValidationDecision
    comment: str | None
    proposed_solution: str | None
    urgency_opinion: SeverityLevel | None
    created_at: datetime


class SyncPriorityOut(BaseModel):
    report_id: uuid.UUID
    score: int
    computed_at: datetime


class SyncProjectOut(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    title: str
    solution_type: SolutionType
    status: ProjectStatus
    progress_percent: int
    planned_start: date | None
    planned_end: date | None
    actual_start: date | None
    actual_end: date | None


class SyncProjectUpdateOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    old_status: ProjectStatus | None
    new_status: ProjectStatus | None
    progress_percent: int | None
    note: str | None
    created_at: datetime


class SyncPullOut(BaseModel):
    cursor: datetime
    douars: list[SyncDouarOut]
    reports: list[ReportOut]
    priorities: list[SyncPriorityOut]
    validations: list[SyncValidationOut]
    projects: list[SyncProjectOut]
    project_updates: list[SyncProjectUpdateOut]
    notifications: list[NotificationOut]
