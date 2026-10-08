import uuid
from datetime import UTC, date, datetime

from app.core.geo import point_from_latlon
from app.core.security import hash_password
from app.models.douar import Douar
from app.models.enums import (
    AuditAction,
    InterruptionFrequency,
    NotificationType,
    ProblemType,
    ReportStatus,
    SeverityLevel,
    TerritoryLevel,
    UserRole,
    WaterSource,
)
from app.models.notification import Notification
from app.models.priority import Priority
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.services.scoring import DEFAULT_WEIGHTS

PASSWORD = "correct horse battery staple"


def make_user(db_session, role, email, territory=None):
    user = User(full_name="U", email=email, password_hash=hash_password(PASSWORD), role=role)
    db_session.add(user)
    db_session.flush()
    if territory is not None:
        db_session.add(UserTerritory(user_id=user.id, territory_id=territory.id))
        db_session.flush()
    return user


def make_douar_in_territory(db_session):
    territory = Territory(name_ar="ت", name_fr="T", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = Douar(
        name_ar="د", name_fr="D", commune_id=territory.id, location=point_from_latlon(31, -8)
    )
    db_session.add(douar)
    db_session.flush()
    return douar, territory


def make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED, **overrides):
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
        severity_reported=SeverityLevel.LOW,
        water_quality_risk=False,
        affected_families=4,
        affected_people=20,
        location=point_from_latlon(31, -8),
        collected_at=datetime.now(UTC),
        status=status,
    )
    defaults.update(overrides)
    report = Report(**defaults)
    db_session.add(report)
    db_session.flush()
    return report


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_expert_validates_report_updates_status_and_notifies(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.EXPERT, "expert@example.com", territory=territory)
    manager = make_user(db_session, UserRole.MANAGER, "manager@example.com", territory=territory)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem@example.com", territory=territory)
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "expert@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "validated", "urgency_opinion": "high"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["new_report_status"] == "validated"

    db_session.refresh(report)
    assert report.status == ReportStatus.VALIDATED

    moqaddem_notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert any(n.type == NotificationType.VALIDATED for n in moqaddem_notifs)
    manager_notifs = db_session.query(Notification).filter_by(user_id=manager.id).all()
    assert any(n.type == NotificationType.VALIDATED for n in manager_notifs)


def test_expert_requests_recheck_notifies_only_moqaddem(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin2@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.EXPERT, "expert2@example.com", territory=territory)
    manager = make_user(db_session, UserRole.MANAGER, "manager2@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem2@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "expert2@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "recheck_requested", "comment": "need more photos"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["new_report_status"] == "recheck_requested"

    db_session.refresh(report)
    assert report.status == ReportStatus.RECHECK_REQUESTED

    moqaddem_notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert any(n.type == NotificationType.RECHECK_REQUESTED for n in moqaddem_notifs)
    manager_notifs = db_session.query(Notification).filter_by(user_id=manager.id).all()
    assert manager_notifs == []


def test_modified_decision_also_sets_status_validated(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin3@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.EXPERT, "expert3@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem3@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "expert3@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "modified", "proposed_solution": "repair pump"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["new_report_status"] == "validated"


def test_rejected_decision_sets_status_and_sends_no_notification(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin4@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.EXPERT, "expert4@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem4@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "expert4@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "rejected", "comment": "not credible"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["new_report_status"] == "rejected"

    moqaddem_notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert moqaddem_notifs == []


def test_non_expert_cannot_create_validation(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(db_session, UserRole.MANAGER, "manager5@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem5@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "manager5@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "validated"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_cannot_validate_report_outside_territory(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    other_territory = Territory(name_ar="ب", name_fr="Other", level=TerritoryLevel.COMMUNE)
    db_session.add(other_territory)
    db_session.flush()
    make_user(
        db_session, UserRole.EXPERT, "expert6@example.com", territory=other_territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem6@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "expert6@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "validated"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_cannot_validate_already_rejected_report(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(db_session, UserRole.EXPERT, "expert7@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem7@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem, status=ReportStatus.REJECTED)
    db_session.flush()
    headers = auth_headers(client, "expert7@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "validated"},
        headers=headers,
    )
    assert resp.status_code == 409


def test_validation_triggers_priority_recompute_with_urgency_opinion(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin8@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.EXPERT, "expert8@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem8@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem, severity_reported=SeverityLevel.LOW)
    db_session.flush()
    headers = auth_headers(client, "expert8@example.com")

    client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "validated", "urgency_opinion": "critical"},
        headers=headers,
    )

    priority = (
        db_session.query(Priority)
        .filter_by(report_id=report.id)
        .order_by(Priority.computed_at.desc())
        .first()
    )
    assert priority is not None
    severity_entry = next(e for e in priority.breakdown if e["criterion"] == "severity")
    assert severity_entry["reason_params"]["severity"] == "critical"


def test_validation_writes_audit_log_status_change(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin9@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.EXPERT, "expert9@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem9@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "expert9@example.com")

    client.post(
        f"/api/v1/reports/{report.id}/validations",
        json={"decision": "validated"},
        headers=headers,
    )

    from app.models.audit_log import AuditLog

    entry = (
        db_session.query(AuditLog)
        .filter_by(entity_type="report", entity_id=report.id, action=AuditAction.STATUS_CHANGE)
        .first()
    )
    assert entry is not None
    assert entry.old_value["status"] == "submitted"
    assert entry.new_value["status"] == "validated"
