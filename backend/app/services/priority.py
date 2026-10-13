"""Wires the pure compute_priority() function (section 7) to the database:
builds its inputs from a persisted Report (+ latest Validation, if any),
and persists the result as a new Priority row. Recomputed on report change
and on scoring-config change (section 4's priorities table note) — right
now the only report-affecting change is a new Validation (1.8); report
fields themselves aren't editable from the API yet.
"""

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.i18n import t
from app.models.douar import Douar
from app.models.enums import NotificationType, ReportStatus
from app.models.priority import Priority
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.validation import Validation
from app.services.notifications import notify_all_managers, notify_user
from app.services.scoring import (
    ReportForScoring,
    ValidationForScoring,
    compute_priority,
)

# section 5 lists "priority changed by >= 10 points" as a notification
# trigger but — unlike every other trigger in that list — doesn't say who
# receives it. Ruling: same audience as the validated/project triggers
# (moqaddem + all managers). See PROGRESS.md.
_PRIORITY_CHANGE_NOTIFICATION_THRESHOLD = 10

# Reports past these statuses are closed; config-change recompute only
# touches reports still actively moving through the pipeline.
_OPEN_STATUSES = {
    ReportStatus.SUBMITTED,
    ReportStatus.UNDER_REVIEW,
    ReportStatus.RECHECK_REQUESTED,
    ReportStatus.VALIDATED,
}


def get_active_scoring_config(db: Session, lang: str = "ar") -> ScoringConfig:
    config = db.query(ScoringConfig).filter_by(is_active=True).one_or_none()
    if config is None:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            key="errors.not_found",
            lang=lang,
        )
    return config


def _report_for_scoring(report: Report) -> ReportForScoring:
    return ReportForScoring(
        affected_people=report.affected_people,
        duration_days=report.duration_days,
        interruption_frequency=report.interruption_frequency.value,
        has_alternative_source=report.has_alternative_source,
        alternative_distance_km=(
            float(report.alternative_distance_km)
            if report.alternative_distance_km is not None
            else None
        ),
        severity_reported=report.severity_reported.value,
        water_quality_risk=report.water_quality_risk,
    )


def _latest_validation_for_scoring(db: Session, report_id) -> ValidationForScoring | None:
    validation = (
        db.query(Validation)
        .filter_by(report_id=report_id)
        .order_by(Validation.created_at.desc())
        .first()
    )
    if validation is None or validation.urgency_opinion is None:
        return None
    return ValidationForScoring(urgency_opinion=validation.urgency_opinion.value)


def recompute_priority(db: Session, report: Report, config: ScoringConfig) -> Priority:
    """Computes and persists a new Priority row for `report` using `config`'s
    weights. Does not commit — the caller controls the transaction boundary
    (a single report change vs. a bulk config-change recompute). Notifies
    moqaddem + managers if the score moved by >= 10 points from the
    previous computation (no-op on a report's first-ever computation,
    since there's nothing to compare against)."""
    previous = (
        db.query(Priority)
        .filter_by(report_id=report.id)
        .order_by(Priority.computed_at.desc())
        .first()
    )

    validation_input = _latest_validation_for_scoring(db, report.id)
    result = compute_priority(_report_for_scoring(report), validation_input, config.weights)
    priority = Priority(
        report_id=report.id,
        score=result.score,
        breakdown=[
            {
                "criterion": e.criterion,
                "value": e.value,
                "weight": e.weight,
                "points": e.points,
                "reason_key": e.reason_key,
                "reason_params": e.reason_params,
            }
            for e in result.breakdown
        ],
        config_id=config.id,
    )
    db.add(priority)
    db.flush()

    if previous is not None and abs(result.score - previous.score) >= (
        _PRIORITY_CHANGE_NOTIFICATION_THRESHOLD
    ):
        douar = db.get(Douar, report.douar_id)
        params = {
            "douar": douar.name_fr,
            "old_score": previous.score,
            "new_score": result.score,
        }
        notify_user(
            db,
            user_id=report.moqaddem_id,
            type=NotificationType.PRIORITY_CHANGED,
            params=params,
            entity_type="report",
            entity_id=report.id,
        )
        notify_all_managers(
            db,
            type=NotificationType.PRIORITY_CHANGED,
            params=params,
            entity_type="report",
            entity_id=report.id,
        )

    return priority


def recompute_all_open_reports(db: Session, config: ScoringConfig) -> int:
    """Used when scoring_config weights change (section 5): every report
    still actively moving through the pipeline gets a fresh Priority row
    under the new weights. Returns how many were recomputed."""
    open_reports = db.query(Report).filter(Report.status.in_(_OPEN_STATUSES)).all()
    for report in open_reports:
        recompute_priority(db, report, config)
    return len(open_reports)


def localize_breakdown(breakdown: list[dict], lang: str) -> list[dict]:
    """Adds a `reason` field (section 2.1: priority reasons are localized
    server-side via Accept-Language) to each stored breakdown entry,
    without mutating the stored reason_key/reason_params — those stay the
    machine form clients can translate themselves if they prefer."""
    return [
        {**entry, "reason": t(entry["reason_key"], lang, **entry["reason_params"])}
        for entry in breakdown
    ]
