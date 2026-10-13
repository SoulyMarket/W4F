import uuid
from datetime import UTC, date, datetime, timedelta

from app.core.geo import point_from_latlon
from app.core.security import hash_password
from app.models.douar import Douar
from app.models.enums import (
    InterruptionFrequency,
    ProblemType,
    ProjectStatus,
    ReportStatus,
    SeverityLevel,
    TerritoryLevel,
    UserRole,
    WaterSource,
)
from app.models.priority import Priority
from app.models.project import Project
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


def make_douar(db_session, territory, name="D"):
    douar = Douar(
        name_ar=name, name_fr=name, commune_id=territory.id, location=point_from_latlon(31, -8)
    )
    db_session.add(douar)
    db_session.flush()
    return douar


def make_report(db_session, douar, moqaddem, collected_at=None, **overrides):
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
        collected_at=collected_at or datetime.now(UTC),
        status=ReportStatus.SUBMITTED,
    )
    defaults.update(overrides)
    report = Report(**defaults)
    db_session.add(report)
    db_session.flush()
    return report


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_summary_counts_reports_by_status(client, db_session):
    territory = Territory(name_ar="ت", name_fr="T", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = make_douar(db_session, territory)
    make_user(db_session, UserRole.MANAGER, "manager@example.com", territory=territory)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem@example.com")
    make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED)
    make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED)
    make_report(db_session, douar, moqaddem, status=ReportStatus.VALIDATED)
    headers = auth_headers(client, "manager@example.com")

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_douars"] == 1
    assert body["reports_by_status"]["submitted"] == 2
    assert body["reports_by_status"]["validated"] == 1


def test_summary_identifies_priority_douars_above_threshold(client, db_session):
    territory = Territory(name_ar="ت2", name_fr="T2", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = make_douar(db_session, territory, "HighPriorityDouar")
    make_user(
        db_session, UserRole.MANAGER, "manager2@example.com", territory=territory
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem2@example.com")
    report = make_report(db_session, douar, moqaddem)

    admin = make_user(db_session, UserRole.ADMIN, "admin2@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()
    db_session.add(
        Priority(report_id=report.id, score=85, breakdown=[], config_id=config.id)
    )
    db_session.flush()
    headers = auth_headers(client, "manager2@example.com")

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    priority_douar_ids = {d["id"] for d in resp.json()["priority_douars"]}
    assert str(douar.id) in priority_douar_ids


def test_summary_identifies_recurring_problem_douars(client, db_session):
    territory = Territory(name_ar="ت3", name_fr="T3", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = make_douar(db_session, territory, "RecurringDouar")
    make_user(
        db_session, UserRole.MANAGER, "manager3@example.com", territory=territory
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem3@example.com")
    now = datetime.now(UTC)
    for i in range(3):
        make_report(db_session, douar, moqaddem, collected_at=now - timedelta(days=i * 10))
    headers = auth_headers(client, "manager3@example.com")

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    recurring_ids = {d["id"] for d in resp.json()["recurring_problem_douars"]}
    assert str(douar.id) in recurring_ids


def test_summary_counts_projects_by_status(client, db_session):
    territory = Territory(name_ar="ت4", name_fr="T4", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = make_douar(db_session, territory)
    manager = make_user(
        db_session, UserRole.MANAGER, "manager4@example.com", territory=territory
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem4@example.com")
    report = make_report(db_session, douar, moqaddem, status=ReportStatus.CONVERTED_TO_PROJECT)
    db_session.add(
        Project(
            report_id=report.id,
            douar_id=douar.id,
            title="x",
            solution_type="pump_repair",
            owner_id=manager.id,
            status=ProjectStatus.IN_PROGRESS,
        )
    )
    db_session.flush()
    headers = auth_headers(client, "manager4@example.com")

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["projects_by_status"]["in_progress"] == 1


def test_non_manager_cannot_access_dashboard(client, db_session):
    territory = Territory(name_ar="ت5", name_fr="T5", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    make_user(db_session, UserRole.ADMIN, "admin5@example.com")
    headers = auth_headers(client, "admin5@example.com")

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 403


def test_map_returns_valid_geojson_with_properties(client, db_session):
    territory = Territory(name_ar="ت6", name_fr="T6", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = make_douar(db_session, territory, "MapDouar")
    make_user(
        db_session, UserRole.MANAGER, "manager6@example.com", territory=territory
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem6@example.com")
    report = make_report(db_session, douar, moqaddem)

    admin = make_user(db_session, UserRole.ADMIN, "admin6@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()
    db_session.add(Priority(report_id=report.id, score=42, breakdown=[], config_id=config.id))
    db_session.flush()
    headers = auth_headers(client, "manager6@example.com")

    resp = client.get("/api/v1/dashboard/map", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    feature = next(f for f in body["features"] if f["properties"]["id"] == str(douar.id))
    assert feature["geometry"]["type"] == "Point"
    assert feature["properties"]["latest_score"] == 42
    assert feature["properties"]["report_count"] == 1


def test_dashboard_is_territory_scoped(client, db_session):
    territory_a = Territory(name_ar="أ", name_fr="A", level=TerritoryLevel.COMMUNE)
    territory_b = Territory(name_ar="ب", name_fr="B", level=TerritoryLevel.COMMUNE)
    db_session.add_all([territory_a, territory_b])
    db_session.flush()
    douar_a = make_douar(db_session, territory_a, "DouarA")
    douar_b = make_douar(db_session, territory_b, "DouarB")
    make_user(
        db_session, UserRole.MANAGER, "manager7@example.com", territory=territory_a
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem7@example.com")
    make_report(db_session, douar_a, moqaddem)
    make_report(db_session, douar_b, moqaddem)
    headers = auth_headers(client, "manager7@example.com")

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.json()["total_douars"] == 1
