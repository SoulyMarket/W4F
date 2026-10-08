import uuid
from datetime import UTC, date, datetime

from app.core.geo import point_from_latlon
from app.core.security import hash_password
from app.models.douar import Douar
from app.models.enums import (
    InterruptionFrequency,
    ProblemType,
    ReportStatus,
    SeverityLevel,
    TerritoryLevel,
    UserRole,
    ValidationDecision,
    WaterSource,
)
from app.models.priority import Priority
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.territory import Territory
from app.models.user import User
from app.models.validation import Validation
from app.services.priority import (
    get_active_scoring_config,
    localize_breakdown,
    recompute_all_open_reports,
    recompute_priority,
)
from app.services.scoring import DEFAULT_WEIGHTS


def make_user(db_session, email, role=UserRole.ADMIN):
    user = User(full_name="U", email=email, password_hash=hash_password("x" * 10), role=role)
    db_session.add(user)
    db_session.flush()
    return user


def make_douar(db_session):
    territory = Territory(name_ar="ت", name_fr="T", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = Douar(
        name_ar="د", name_fr="D", commune_id=territory.id, location=point_from_latlon(31, -8)
    )
    db_session.add(douar)
    db_session.flush()
    return douar


def make_report(db_session, douar, moqaddem, **overrides):
    defaults = dict(
        id=uuid.uuid4(),
        douar_id=douar.id,
        moqaddem_id=moqaddem.id,
        water_source=WaterSource.WELL,
        problem_type=ProblemType.NO_WATER,
        problem_started_on=date(2026, 1, 1),
        duration_days=10,
        interruption_frequency=InterruptionFrequency.DAILY,
        has_alternative_source=False,
        alternative_distance_km=None,
        severity_reported=SeverityLevel.MEDIUM,
        water_quality_risk=False,
        affected_families=4,
        affected_people=20,
        location=point_from_latlon(31, -8),
        collected_at=datetime.now(UTC),
        status=ReportStatus.SUBMITTED,
    )
    defaults.update(overrides)
    report = Report(**defaults)
    db_session.add(report)
    db_session.flush()
    return report


def make_active_config(db_session, admin, weights=None):
    config = ScoringConfig(
        weights=weights or DEFAULT_WEIGHTS, is_active=True, created_by=admin.id
    )
    db_session.add(config)
    db_session.flush()
    return config


def test_get_active_scoring_config_returns_the_active_one(db_session):
    admin = make_user(db_session, "admin@example.com")
    old = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=False, created_by=admin.id)
    active = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add_all([old, active])
    db_session.flush()

    result = get_active_scoring_config(db_session)
    assert result.id == active.id


def test_recompute_priority_persists_a_matching_priority_row(db_session):
    admin = make_user(db_session, "admin2@example.com")
    moqaddem = make_user(db_session, "moqaddem@example.com", role=UserRole.MOQADDEM)
    douar = make_douar(db_session)
    report = make_report(db_session, douar, moqaddem, affected_people=1000, duration_days=30)
    config = make_active_config(db_session, admin)

    priority = recompute_priority(db_session, report, config)

    assert priority.report_id == report.id
    assert priority.config_id == config.id
    assert priority.score > 0
    assert len(priority.breakdown) >= 7


def test_recompute_priority_uses_latest_validation_urgency(db_session):
    admin = make_user(db_session, "admin3@example.com")
    expert = make_user(db_session, "expert@example.com", role=UserRole.EXPERT)
    moqaddem = make_user(db_session, "moqaddem2@example.com", role=UserRole.MOQADDEM)
    douar = make_douar(db_session)
    report = make_report(db_session, douar, moqaddem, severity_reported=SeverityLevel.LOW)
    config = make_active_config(db_session, admin)

    db_session.add(
        Validation(
            report_id=report.id,
            expert_id=expert.id,
            decision=ValidationDecision.VALIDATED,
            urgency_opinion=SeverityLevel.CRITICAL,
        )
    )
    db_session.flush()

    priority = recompute_priority(db_session, report, config)
    severity_entry = next(e for e in priority.breakdown if e["criterion"] == "severity")
    assert severity_entry["reason_params"]["severity"] == "critical"

    expert_entry = next(
        (e for e in priority.breakdown if e["criterion"] == "expert_confirmation"), None
    )
    assert expert_entry is not None


def test_recompute_all_open_reports_skips_closed_statuses(db_session):
    admin = make_user(db_session, "admin4@example.com")
    moqaddem = make_user(db_session, "moqaddem3@example.com", role=UserRole.MOQADDEM)
    douar = make_douar(db_session)
    open_report = make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED)
    rejected_report = make_report(db_session, douar, moqaddem, status=ReportStatus.REJECTED)
    converted_report = make_report(
        db_session, douar, moqaddem, status=ReportStatus.CONVERTED_TO_PROJECT
    )
    config = make_active_config(db_session, admin)

    count = recompute_all_open_reports(db_session, config)
    assert count == 1

    priorities = db_session.query(Priority).all()
    scored_report_ids = {p.report_id for p in priorities}
    assert scored_report_ids == {open_report.id}
    assert rejected_report.id not in scored_report_ids
    assert converted_report.id not in scored_report_ids


def test_localize_breakdown_adds_reason_without_mutating_keys(db_session):
    breakdown = [
        {
            "criterion": "people_affected",
            "value": 500,
            "weight": 25,
            "points": 12.5,
            "reason_key": "priority.people_affected",
            "reason_params": {"count": 500},
        }
    ]
    localized_ar = localize_breakdown(breakdown, "ar")
    assert localized_ar[0]["reason_key"] == "priority.people_affected"
    assert "500" in localized_ar[0]["reason"]

    localized_fr = localize_breakdown(breakdown, "fr")
    assert "personnes" in localized_fr[0]["reason"]
