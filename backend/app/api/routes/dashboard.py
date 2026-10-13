from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from geoalchemy2.shape import to_shape
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.douar import Douar
from app.models.enums import UserRole
from app.models.project import Project
from app.models.report import Report
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryOut, DouarSummary
from app.services.dashboard import (
    latest_project_status_by_douar,
    latest_score_by_report,
    reports_by_douar,
)
from app.services.territory_scope import territory_scope_filter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# section 1: dashboard/map access is manager's explicit role ("dashboard and
# map"); no other role lists it.
_require_manager = require_roles(UserRole.MANAGER)

_PRIORITY_DOUAR_THRESHOLD = 70
_RECURRING_PROBLEM_MIN_REPORTS = 3
_RECURRING_PROBLEM_WINDOW_DAYS = 365


@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager),
) -> DashboardSummaryOut:
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    scoped_douars = db.query(Douar).filter(scope).all()
    scoped_douar_ids = [d.id for d in scoped_douars]
    douar_by_id = {d.id: d for d in scoped_douars}

    reports_by_status: dict[str, int] = defaultdict(int)
    projects_by_status: dict[str, int] = defaultdict(int)
    priority_douars: list[DouarSummary] = []
    recurring_problem_douars: list[DouarSummary] = []

    if scoped_douar_ids:
        for report_status, count in (
            db.query(Report.status, func.count(Report.id))
            .filter(Report.douar_id.in_(scoped_douar_ids))
            .group_by(Report.status)
            .all()
        ):
            reports_by_status[report_status.value] = count

        for project_status, count in (
            db.query(Project.status, func.count(Project.id))
            .filter(Project.douar_id.in_(scoped_douar_ids))
            .group_by(Project.status)
            .all()
        ):
            projects_by_status[project_status.value] = count

        by_douar = reports_by_douar(db, scoped_douar_ids)
        report_ids = [rid for rows in by_douar.values() for rid, _ in rows]
        scores = latest_score_by_report(db, report_ids)
        cutoff = datetime.now(UTC) - timedelta(days=_RECURRING_PROBLEM_WINDOW_DAYS)

        for douar_id, reports in by_douar.items():
            douar = douar_by_id[douar_id]
            most_recent_report_id, _ = max(reports, key=lambda r: r[1])
            latest_score = scores.get(most_recent_report_id)

            if latest_score is not None and latest_score >= _PRIORITY_DOUAR_THRESHOLD:
                priority_douars.append(
                    DouarSummary(
                        id=douar_id,
                        name_ar=douar.name_ar,
                        name_fr=douar.name_fr,
                        score=latest_score,
                        report_count=len(reports),
                    )
                )

            recent_count = sum(1 for _, collected_at in reports if collected_at >= cutoff)
            if recent_count >= _RECURRING_PROBLEM_MIN_REPORTS:
                recurring_problem_douars.append(
                    DouarSummary(
                        id=douar_id,
                        name_ar=douar.name_ar,
                        name_fr=douar.name_fr,
                        score=latest_score or 0,
                        report_count=recent_count,
                    )
                )

    return DashboardSummaryOut(
        total_douars=len(scoped_douar_ids),
        reports_by_status=dict(reports_by_status),
        priority_douars=priority_douars,
        projects_by_status=dict(projects_by_status),
        recurring_problem_douars=recurring_problem_douars,
    )


@router.get("/map")
def get_dashboard_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager),
) -> dict:
    """GeoJSON FeatureCollection of douars with latest score, report count,
    and latest project status (section 5)."""
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    douars = db.query(Douar).filter(scope).all()
    douar_ids = [d.id for d in douars]

    report_counts = dict(
        db.query(Report.douar_id, func.count(Report.id))
        .filter(Report.douar_id.in_(douar_ids))
        .group_by(Report.douar_id)
        .all()
    )
    project_status_by_douar = latest_project_status_by_douar(db, douar_ids)
    by_douar = reports_by_douar(db, douar_ids)
    report_ids = [rid for rows in by_douar.values() for rid, _ in rows]
    scores = latest_score_by_report(db, report_ids)

    features = []
    for douar in douars:
        if douar.location is None:
            continue
        point = to_shape(douar.location)
        reports = by_douar.get(douar.id, [])
        latest_score = None
        if reports:
            most_recent_report_id, _ = max(reports, key=lambda r: r[1])
            latest_score = scores.get(most_recent_report_id)

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [point.x, point.y]},
                "properties": {
                    "id": str(douar.id),
                    "name_ar": douar.name_ar,
                    "name_fr": douar.name_fr,
                    "latest_score": latest_score,
                    "report_count": report_counts.get(douar.id, 0),
                    "project_status": project_status_by_douar.get(douar.id),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
