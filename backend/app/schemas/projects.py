import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus, SolutionType


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    solution_type: SolutionType
    description: str | None = None
    owner_id: uuid.UUID | None = None
    planned_start: date | None = None
    planned_end: date | None = None


class ProjectUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    solution_type: SolutionType | None = None
    description: str | None = None
    owner_id: uuid.UUID | None = None
    planned_start: date | None = None
    planned_end: date | None = None


class ProjectStatusChangeCreate(BaseModel):
    new_status: ProjectStatus
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    note: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    douar_id: uuid.UUID
    title: str
    solution_type: SolutionType
    description: str | None
    status: ProjectStatus
    owner_id: uuid.UUID
    planned_start: date | None
    planned_end: date | None
    actual_start: date | None
    actual_end: date | None
    progress_percent: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    page_size: int


class ProjectUpdateOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    author_id: uuid.UUID
    old_status: ProjectStatus | None
    new_status: ProjectStatus | None
    progress_percent: int | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailOut(ProjectOut):
    updates: list[ProjectUpdateOut]
