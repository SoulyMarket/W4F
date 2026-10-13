import uuid

from pydantic import BaseModel


class DouarSummary(BaseModel):
    id: uuid.UUID
    name_ar: str
    name_fr: str
    score: int
    report_count: int


class DashboardSummaryOut(BaseModel):
    total_douars: int
    reports_by_status: dict[str, int]
    priority_douars: list[DouarSummary]  # latest-score >= 70
    projects_by_status: dict[str, int]
    recurring_problem_douars: list[DouarSummary]  # >= 3 reports in the last 12 months
