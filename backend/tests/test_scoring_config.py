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
    WaterSource,
)
from app.models.priority import Priority
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.territory import Territory
from app.models.user import User
from app.services.scoring import DEFAULT_WEIGHTS

PASSWORD = "correct horse battery staple"


def make_user(db_session, role, email, territory=None):
    user = User(full_name="U", email=email, password_hash=hash_password(PASSWORD), role=role)
    db_session.add(user)
    db_session.flush()
    if territory is not None:
        from app.models.territory import UserTerritory

        db_session.add(UserTerritory(user_id=user.id, territory_id=territory.id))
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
    return douar, territory


def make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED):
    report = Report(
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
        status=status,
    )
    db_session.add(report)
    db_session.flush()
    return report


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_get_scoring_config_returns_active_weights(client, db_session):
    admin = make_user(db_session, UserRole.ADMIN, "admin@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    db_session.flush()
    headers = auth_headers(client, "admin@example.com")

    resp = client.get("/api/v1/scoring-config", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["weights"]["people_affected"] == DEFAULT_WEIGHTS["people_affected"]


def test_manager_can_update_scoring_config_and_recompute(client, db_session):
    admin = make_user(db_session, UserRole.ADMIN, "admin2@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    douar, territory = make_douar(db_session)
    make_user(db_session, UserRole.MANAGER, "manager@example.com", territory=territory)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem@example.com")
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "manager@example.com")

    new_weights = dict(DEFAULT_WEIGHTS)
    new_weights["people_affected"] = 50

    resp = client.put("/api/v1/scoring-config", json={"weights": new_weights}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["config"]["weights"]["people_affected"] == 50
    assert body["reports_recomputed"] == 1

    priority = db_session.query(Priority).filter_by(report_id=report.id).one()
    assert priority.config_id == uuid.UUID(body["config"]["id"])


def test_update_scoring_config_rejects_missing_criterion(client, db_session):
    admin = make_user(db_session, UserRole.ADMIN, "admin3@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    make_user(db_session, UserRole.MANAGER, "manager2@example.com")
    db_session.flush()
    headers = auth_headers(client, "manager2@example.com")

    incomplete = dict(DEFAULT_WEIGHTS)
    del incomplete["people_affected"]

    resp = client.put("/api/v1/scoring-config", json={"weights": incomplete}, headers=headers)
    assert resp.status_code == 422


def test_non_manager_cannot_update_scoring_config(client, db_session):
    admin = make_user(db_session, UserRole.ADMIN, "admin4@example.com")
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    db_session.flush()
    headers = auth_headers(client, "admin4@example.com")

    resp = client.put("/api/v1/scoring-config", json={"weights": DEFAULT_WEIGHTS}, headers=headers)
    assert resp.status_code == 403


def test_get_report_priority_returns_localized_breakdown(client, db_session):
    admin = make_user(db_session, UserRole.ADMIN, "admin5@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()

    douar, territory = make_douar(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager3@example.com", territory=territory
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem2@example.com")
    report = make_report(db_session, douar, moqaddem)

    from app.services.priority import recompute_priority

    recompute_priority(db_session, report, config)
    db_session.flush()
    headers = auth_headers(client, "manager3@example.com")

    resp = client.get(f"/api/v1/reports/{report.id}/priority", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] >= 0
    assert all("reason" in entry for entry in body["breakdown"])
    assert all(entry["reason"] for entry in body["breakdown"])


def test_get_report_priority_404_when_not_yet_computed(client, db_session):
    make_user(db_session, UserRole.ADMIN, "admin6@example.com")
    douar, territory = make_douar(db_session)
    make_user(db_session, UserRole.MANAGER, "manager4@example.com", territory=territory)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem3@example.com")
    report = make_report(db_session, douar, moqaddem)
    db_session.flush()
    headers = auth_headers(client, "manager4@example.com")

    resp = client.get(f"/api/v1/reports/{report.id}/priority", headers=headers)
    assert resp.status_code == 404
