"""Wires the pure compute_priority() function (section 7) to the database:
builds its inputs from a persisted Report (+ latest Validation, if any),
and persists the result as a new Priority row. Recomputed on report change
and on scoring-config change (section 4's priorities table note) — right
now the only report-affecting change is a new Validation (1.8); report
fields themselves aren't editable from the API yet.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.i18n import t
from app.models.enums import ReportStatus
from app.models.priority import Priority
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.validation import Validation
from app.services.scoring import (
    ReportForScoring,
    ValidationForScoring,
    compute_priority,
)

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=t("errors.not_found", lang),
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
    (a single report change vs. a bulk config-change recompute)."""
    validation_input = _latest_validation_for_scoring(db, report.id)
    result = compute_priority(
        _report_for_scoring(report), validation_input, config.weights
    )
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
