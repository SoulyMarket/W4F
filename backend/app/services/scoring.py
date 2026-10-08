"""Explainable priority scoring (section 7 of the build plan).

A pure function: no I/O, no ORM. The caller builds ReportForScoring from a
persisted report and passes the active scoring_config weights. The score is
decision support only — nothing here changes a report's status.
"""

from dataclasses import dataclass
from typing import Any

DEFAULT_WEIGHTS: dict[str, float] = {
    "people_affected": 25,
    "duration": 15,
    "frequency": 10,
    "no_alternative": 15,
    "distance": 10,
    "severity": 15,
    "water_quality_risk": 10,
}

_FREQUENCY_FACTORS = {
    "permanent": 1.0,
    "daily": 0.8,
    "weekly": 0.5,
    "monthly": 0.25,
    "rare": 0.1,
}

_SEVERITY_FACTORS = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0,
}


@dataclass(frozen=True)
class ReportForScoring:
    affected_people: int
    duration_days: int
    interruption_frequency: str
    has_alternative_source: bool
    alternative_distance_km: float | None
    severity_reported: str
    water_quality_risk: bool


@dataclass(frozen=True)
class ValidationForScoring:
    urgency_opinion: str


@dataclass(frozen=True)
class ScoreBreakdownEntry:
    criterion: str
    value: Any
    weight: float
    points: float
    reason_key: str
    reason_params: dict[str, Any]


@dataclass(frozen=True)
class PriorityResult:
    score: int
    breakdown: list[ScoreBreakdownEntry]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_priority(
    report: ReportForScoring,
    validation: ValidationForScoring | None = None,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> PriorityResult:
    entries: list[ScoreBreakdownEntry] = []

    people_ratio = _clamp01(report.affected_people / 1000)
    entries.append(
        ScoreBreakdownEntry(
            criterion="people_affected",
            value=report.affected_people,
            weight=weights["people_affected"],
            points=people_ratio * weights["people_affected"],
            reason_key="priority.people_affected",
            reason_params={"count": report.affected_people},
        )
    )

    duration_ratio = _clamp01(report.duration_days / 30)
    entries.append(
        ScoreBreakdownEntry(
            criterion="duration",
            value=report.duration_days,
            weight=weights["duration"],
            points=duration_ratio * weights["duration"],
            reason_key="priority.long_duration",
            reason_params={"days": report.duration_days},
        )
    )

    frequency_factor = _FREQUENCY_FACTORS[report.interruption_frequency]
    entries.append(
        ScoreBreakdownEntry(
            criterion="frequency",
            value=report.interruption_frequency,
            weight=weights["frequency"],
            points=frequency_factor * weights["frequency"],
            reason_key="priority.frequency",
            reason_params={"frequency": report.interruption_frequency},
        )
    )

    if report.has_alternative_source:
        entries.append(
            ScoreBreakdownEntry(
                criterion="no_alternative",
                value=False,
                weight=weights["no_alternative"],
                points=0,
                reason_key="priority.has_alternative",
                reason_params={},
            )
        )
        km = report.alternative_distance_km or 0.0
        distance_ratio = _clamp01(km / 5)
        entries.append(
            ScoreBreakdownEntry(
                criterion="distance",
                value=km,
                weight=weights["distance"],
                points=distance_ratio * weights["distance"],
                reason_key="priority.distance",
                reason_params={"km": km},
            )
        )
    else:
        entries.append(
            ScoreBreakdownEntry(
                criterion="no_alternative",
                value=True,
                weight=weights["no_alternative"],
                points=weights["no_alternative"],
                reason_key="priority.no_alternative",
                reason_params={},
            )
        )
        entries.append(
            ScoreBreakdownEntry(
                criterion="distance",
                value=None,
                weight=weights["distance"],
                points=weights["distance"],
                reason_key="priority.distance_no_alternative",
                reason_params={},
            )
        )

    effective_severity = validation.urgency_opinion if validation else report.severity_reported
    severity_factor = _SEVERITY_FACTORS[effective_severity]
    entries.append(
        ScoreBreakdownEntry(
            criterion="severity",
            value=effective_severity,
            weight=weights["severity"],
            points=severity_factor * weights["severity"],
            reason_key="priority.severity",
            reason_params={"severity": effective_severity},
        )
    )

    if validation is not None:
        entries.append(
            ScoreBreakdownEntry(
                criterion="expert_confirmation",
                value=None,
                weight=0,
                points=0,
                reason_key="priority.expert_confirmed",
                reason_params={},
            )
        )

    if report.water_quality_risk:
        entries.append(
            ScoreBreakdownEntry(
                criterion="water_quality_risk",
                value=True,
                weight=weights["water_quality_risk"],
                points=weights["water_quality_risk"],
                reason_key="priority.water_quality_risk",
                reason_params={},
            )
        )
    else:
        entries.append(
            ScoreBreakdownEntry(
                criterion="water_quality_risk",
                value=False,
                weight=weights["water_quality_risk"],
                points=0,
                reason_key="priority.no_quality_risk",
                reason_params={},
            )
        )

    entries.sort(key=lambda e: e.points, reverse=True)
    total = sum(e.points for e in entries)
    score = round(max(0.0, min(100.0, total)))

    return PriorityResult(score=score, breakdown=entries)
