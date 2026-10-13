"""Aggregation helpers shared by GET /dashboard/summary and GET /dashboard/map
(section 5). Kept out of the route module so both endpoints compute "latest
priority score per report" and "latest project status per douar" the same
way instead of drifting."""

import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.priority import Priority
from app.models.project import Project
from app.models.report import Report


def latest_score_by_report(db: Session, report_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    """For each report id, its most recently computed Priority score."""
    if not report_ids:
        return {}
    latest: dict[uuid.UUID, int] = {}
    rows = (
        db.query(Priority.report_id, Priority.score, Priority.computed_at)
        .filter(Priority.report_id.in_(report_ids))
        .order_by(Priority.report_id, Priority.computed_at.desc())
        .all()
    )
    for report_id, score, _computed_at in rows:
        if report_id not in latest:  # first row per report_id, thanks to the ORDER BY
            latest[report_id] = score
    return latest


def reports_by_douar(
    db: Session, douar_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[tuple[uuid.UUID, object]]]:
    """douar_id -> [(report_id, collected_at), ...] for the given douars."""
    grouped: dict[uuid.UUID, list[tuple[uuid.UUID, object]]] = defaultdict(list)
    if not douar_ids:
        return grouped
    for report_id, douar_id, collected_at in (
        db.query(Report.id, Report.douar_id, Report.collected_at)
        .filter(Report.douar_id.in_(douar_ids))
        .all()
    ):
        grouped[douar_id].append((report_id, collected_at))
    return grouped


def latest_project_status_by_douar(
    db: Session, douar_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """douar_id -> most recently created project's status, for douars that
    have at least one project."""
    latest: dict[uuid.UUID, str] = {}
    if not douar_ids:
        return latest
    rows = (
        db.query(Project.douar_id, Project.status, Project.created_at)
        .filter(Project.douar_id.in_(douar_ids))
        .order_by(Project.douar_id, Project.created_at.desc())
        .all()
    )
    for douar_id, project_status, _created_at in rows:
        if douar_id not in latest:
            latest[douar_id] = project_status.value
    return latest
