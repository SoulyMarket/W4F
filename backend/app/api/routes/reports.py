import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.core.geo import latlon_from_point
from app.db.session import get_db
from app.i18n import t
from app.models.douar import Douar
from app.models.enums import ReportStatus, UserRole
from app.models.priority import Priority
from app.models.report import Report
from app.models.report_media import ReportMedia
from app.models.user import User
from app.models.validation import Validation
from app.schemas.reports import (
    PriorityOut,
    ReportDetailOut,
    ReportListOut,
    ReportMediaOut,
    ReportOut,
    ValidationOut,
)
from app.services.territory_scope import get_descendant_ids, territory_scope_filter

router = APIRouter(prefix="/reports", tags=["reports"])

_require_any = require_roles(*list(UserRole))


def _report_to_out(report: Report, score: int | None = None) -> ReportOut:
    coords = latlon_from_point(report.location)
    return ReportOut(
        id=report.id,
        douar_id=report.douar_id,
        moqaddem_id=report.moqaddem_id,
        water_source=report.water_source,
        problem_type=report.problem_type,
        problem_started_on=report.problem_started_on,
        duration_days=report.duration_days,
        interruption_frequency=report.interruption_frequency,
        has_alternative_source=report.has_alternative_source,
        alternative_distance_km=(
            float(report.alternative_distance_km)
            if report.alternative_distance_km is not None
            else None
        ),
        severity_reported=report.severity_reported,
        water_quality_risk=report.water_quality_risk,
        affected_families=report.affected_families,
        affected_people=report.affected_people,
        observations=report.observations,
        lat=coords[0] if coords else None,
        lon=coords[1] if coords else None,
        location_accuracy_m=(
            float(report.location_accuracy_m) if report.location_accuracy_m is not None else None
        ),
        collected_at=report.collected_at,
        synced_at=report.synced_at,
        status=report.status,
        version=report.version,
        score=score,
    )


def _latest_priority_subquery(db: Session):
    latest = (
        db.query(Priority.report_id, func.max(Priority.computed_at).label("computed_at"))
        .group_by(Priority.report_id)
        .subquery()
    )
    return latest


def _reports_query_with_scope(db: Session, user: User):
    scope = territory_scope_filter(Douar.commune_id, db, user)
    return db.query(Report).join(Douar, Report.douar_id == Douar.id).filter(scope)


@router.get("", response_model=ReportListOut)
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    status_filter: ReportStatus | None = Query(default=None, alias="status"),
    douar_id: uuid.UUID | None = None,
    commune_id: uuid.UUID | None = None,
    province_id: uuid.UUID | None = None,
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by_score: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ReportListOut:
    query = _reports_query_with_scope(db, current_user)

    if status_filter is not None:
        query = query.filter(Report.status == status_filter)
    if douar_id is not None:
        query = query.filter(Report.douar_id == douar_id)
    if commune_id is not None:
        query = query.filter(Douar.commune_id == commune_id)
    if province_id is not None:
        commune_ids = get_descendant_ids(db, {province_id})
        query = query.filter(Douar.commune_id.in_(commune_ids))
    if date_from is not None:
        query = query.filter(Report.problem_started_on >= date_from)
    if date_to is not None:
        query = query.filter(Report.problem_started_on <= date_to)

    latest = _latest_priority_subquery(db)
    query = query.outerjoin(latest, latest.c.report_id == Report.id).outerjoin(
        Priority,
        (Priority.report_id == latest.c.report_id)
        & (Priority.computed_at == latest.c.computed_at),
    )

    if min_score is not None:
        query = query.filter(Priority.score >= min_score)
    if max_score is not None:
        query = query.filter(Priority.score <= max_score)

    total = query.with_entities(func.count(Report.id.distinct())).scalar()

    query = query.add_columns(Priority.score)
    if sort_by_score:
        query = query.order_by(Priority.score.desc().nullslast())
    else:
        query = query.order_by(Report.collected_at.desc())

    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [_report_to_out(report, score) for report, score in rows]
    return ReportListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report(
    report_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
) -> ReportDetailOut:
    lang = get_request_language(request)
    report = _reports_query_with_scope(db, current_user).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=t("errors.not_found", lang)
        )

    media = db.query(ReportMedia).filter_by(report_id=report.id).all()
    validations = (
        db.query(Validation)
        .filter_by(report_id=report.id)
        .order_by(Validation.created_at.desc())
        .all()
    )
    latest_priority = (
        db.query(Priority)
        .filter_by(report_id=report.id)
        .order_by(Priority.computed_at.desc())
        .first()
    )

    base = _report_to_out(report, latest_priority.score if latest_priority else None)
    return ReportDetailOut(
        **base.model_dump(),
        media=[ReportMediaOut.model_validate(m) for m in media],
        priority=(
            PriorityOut(
                score=latest_priority.score,
                breakdown=latest_priority.breakdown,
                computed_at=latest_priority.computed_at,
            )
            if latest_priority
            else None
        ),
        validations=[ValidationOut.model_validate(v) for v in validations],
    )
