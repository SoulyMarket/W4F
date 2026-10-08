import uuid
from datetime import UTC, date, datetime

from app.core.geo import point_from_latlon
from app.core.security import hash_password
from app.models.douar import Douar
from app.models.enums import (
    InterruptionFrequency,
    NotificationType,
    ProblemType,
    ProjectStatus,
    ReportStatus,
    SeverityLevel,
    TerritoryLevel,
    UserRole,
    WaterSource,
)
from app.models.notification import Notification
from app.models.project import Project
from app.models.report import Report
from app.models.territory import Territory, UserTerritory
from app.models.user import User

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


def make_report(db_session, douar, moqaddem, status=ReportStatus.VALIDATED):
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
        severity_reported=SeverityLevel.HIGH,
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


def test_manager_converts_validated_report_to_project(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(db_session, UserRole.MANAGER, "manager@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem, status=ReportStatus.VALIDATED)
    headers = auth_headers(client, "manager@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "Fix the pump", "solution_type": "pump_repair"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Fix the pump"
    assert body["status"] == "new"
    assert body["report_id"] == str(report.id)

    db_session.refresh(report)
    assert report.status == ReportStatus.CONVERTED_TO_PROJECT

    moqaddem_notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert any(n.type == NotificationType.PROJECT_CREATED for n in moqaddem_notifs)


def test_cannot_convert_unvalidated_report_to_project(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager2@example.com", territory=territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem2@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED)
    headers = auth_headers(client, "manager2@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    )
    assert resp.status_code == 409


def test_non_manager_cannot_create_project(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(db_session, UserRole.EXPERT, "expert@example.com", territory=territory)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem3@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem, status=ReportStatus.VALIDATED)
    headers = auth_headers(client, "expert@example.com")

    resp = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_valid_transition_updates_status_and_progress(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager3@example.com", territory=territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem4@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "manager3@example.com")

    create_resp = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/projects/{project_id}/updates",
        json={"new_status": "in_study", "progress_percent": 10, "note": "starting study"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["new_status"] == "in_study"

    project = db_session.get(Project, uuid.UUID(project_id))
    assert project.status == ProjectStatus.IN_STUDY
    assert project.progress_percent == 10


def test_invalid_transition_is_rejected_with_409(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager4@example.com", territory=territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem5@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "manager4@example.com")

    project_id = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    ).json()["id"]

    # new -> approved directly, skipping in_study: not allowed.
    resp = client.post(
        f"/api/v1/projects/{project_id}/updates",
        json={"new_status": "approved"},
        headers=headers,
    )
    assert resp.status_code == 409


def test_any_non_terminal_status_can_move_to_cancelled(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager5@example.com", territory=territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem6@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "manager5@example.com")

    project_id = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    ).json()["id"]

    resp = client.post(
        f"/api/v1/projects/{project_id}/updates",
        json={"new_status": "cancelled"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["new_status"] == "cancelled"


def test_completed_is_terminal_no_further_transitions(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager6@example.com", territory=territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem7@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "manager6@example.com")

    project_id = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    ).json()["id"]

    for target in ("in_study", "approved", "in_preparation", "in_progress", "completed"):
        resp = client.post(
            f"/api/v1/projects/{project_id}/updates",
            json={"new_status": target},
            headers=headers,
        )
        assert resp.status_code == 201, f"transition to {target} failed: {resp.json()}"

    final = client.post(
        f"/api/v1/projects/{project_id}/updates",
        json={"new_status": "cancelled"},
        headers=headers,
    )
    assert final.status_code == 409

    moqaddem_notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert any(n.type == NotificationType.PROJECT_COMPLETED for n in moqaddem_notifs)


def test_project_detail_includes_updates_history(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(
        db_session, UserRole.MANAGER, "manager7@example.com", territory=territory
    )
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem8@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "manager7@example.com")

    project_id = client.post(
        f"/api/v1/reports/{report.id}/project",
        json={"title": "x", "solution_type": "pump_repair"},
        headers=headers,
    ).json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/updates",
        json={"new_status": "in_study"},
        headers=headers,
    )

    resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["updates"]) == 1


def test_list_projects_is_territory_scoped(client, db_session):
    douar_a, territory_a = make_douar_in_territory(db_session)
    territory_b = Territory(name_ar="ب", name_fr="B", level=TerritoryLevel.COMMUNE)
    db_session.add(territory_b)
    db_session.flush()
    douar_b = Douar(
        name_ar="ب2", name_fr="DB", commune_id=territory_b.id, location=point_from_latlon(32, -9)
    )
    db_session.add(douar_b)
    db_session.flush()

    make_user(
        db_session, UserRole.MANAGER, "managera@example.com", territory=territory_a
    )
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem9@example.com")
    report_a = make_report(db_session, douar_a, moqaddem)
    report_b = make_report(db_session, douar_b, moqaddem)

    admin = make_user(db_session, UserRole.ADMIN, "admin@example.com")
    from app.models.project import Project as P

    project_a = P(
        report_id=report_a.id,
        douar_id=douar_a.id,
        title="A",
        solution_type="pump_repair",
        owner_id=admin.id,
    )
    project_b = P(
        report_id=report_b.id,
        douar_id=douar_b.id,
        title="B",
        solution_type="pump_repair",
        owner_id=admin.id,
    )
    db_session.add_all([project_a, project_b])
    db_session.flush()

    headers = auth_headers(client, "managera@example.com")
    resp = client.get("/api/v1/projects", headers=headers)
    assert resp.status_code == 200
    titles = {item["title"] for item in resp.json()["items"]}
    assert titles == {"A"}
