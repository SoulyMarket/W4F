import uuid
from datetime import UTC, datetime, timedelta

from app.core.security import hash_password
from app.models.douar import Douar
from app.models.enums import NotificationType, ReportStatus, TerritoryLevel, UserRole
from app.models.notification import Notification
from app.models.priority import Priority
from app.models.report import Report
from app.models.report_media import ReportMedia
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


def make_douar_in_territory(db_session, name="D"):
    territory = Territory(name_ar=name, name_fr=name, level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()
    douar = Douar(name_ar=name, name_fr=name, commune_id=territory.id)
    db_session.add(douar)
    db_session.flush()
    return douar, territory


def make_active_config(db_session, admin):
    db_session.add(ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id))
    db_session.flush()


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def report_payload(douar, **overrides):
    payload = {
        "id": str(uuid.uuid4()),
        "douar_id": str(douar.id),
        "water_source": "well",
        "problem_type": "no_water",
        "problem_started_on": "2026-01-01",
        "duration_days": 10,
        "interruption_frequency": "daily",
        "has_alternative_source": False,
        "alternative_distance_km": None,
        "severity_reported": "high",
        "water_quality_risk": False,
        "affected_families": 4,
        "affected_people": 20,
        "observations": None,
        "lat": 31.355,
        "lon": -7.667,
        "location_accuracy_m": 5.0,
        "collected_at": datetime.now(UTC).isoformat(),
        "media": [],
    }
    payload.update(overrides)
    return payload


def test_push_creates_report_scores_it_and_notifies_territory_experts(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin1@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.EXPERT, "expert1@example.com", territory=territory)
    other_expert = make_user(db_session, UserRole.EXPERT, "expert1b@example.com")
    make_user(db_session, UserRole.MOQADDEM, "moqaddem1@example.com", territory=territory)
    headers = auth_headers(client, "moqaddem1@example.com")

    payload = report_payload(douar)
    resp = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == [
        {"id": payload["id"], "status": "created", "error": None, "version": 1, "media": []}
    ]

    report = db_session.get(Report, uuid.UUID(payload["id"]))
    assert report is not None
    assert report.status == ReportStatus.SUBMITTED
    assert report.synced_at is not None

    priority = db_session.query(Priority).filter_by(report_id=report.id).first()
    assert priority is not None

    expert_notifs = (
        db_session.query(Notification)
        .join(User, Notification.user_id == User.id)
        .filter(User.email == "expert1@example.com")
        .all()
    )
    assert any(n.type == NotificationType.NEW_REPORT for n in expert_notifs)

    other_expert_notifs = db_session.query(Notification).filter_by(user_id=other_expert.id).all()
    assert other_expert_notifs == []


def test_pushing_identical_batch_twice_is_idempotent(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin2@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem2@example.com", territory=territory)
    headers = auth_headers(client, "moqaddem2@example.com")
    payload = report_payload(douar)

    first = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    assert first.json()["results"][0]["status"] == "created"

    second = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    assert second.json()["results"][0]["status"] == "unchanged"

    assert db_session.query(Report).filter_by(id=uuid.UUID(payload["id"])).count() == 1
    assert db_session.query(Priority).filter_by(report_id=uuid.UUID(payload["id"])).count() == 1


def test_push_with_changed_fields_updates_and_bumps_version(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin3@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem3@example.com", territory=territory)
    headers = auth_headers(client, "moqaddem3@example.com")
    payload = report_payload(douar)

    client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)

    payload["affected_people"] = 99
    resp = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    result = resp.json()["results"][0]
    assert result["status"] == "updated"
    assert result["version"] == 2

    report = db_session.get(Report, uuid.UUID(payload["id"]))
    assert report.affected_people == 99
    assert report.version == 2

    priorities = db_session.query(Priority).filter_by(report_id=report.id).all()
    assert len(priorities) == 2


def test_push_rejected_with_sync_conflict_once_report_is_reviewed(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin4@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem4@example.com", territory=territory)
    headers = auth_headers(client, "moqaddem4@example.com")
    payload = report_payload(douar)

    client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    report = db_session.get(Report, uuid.UUID(payload["id"]))
    report.status = ReportStatus.VALIDATED
    db_session.flush()

    payload["affected_people"] = 500
    resp = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    result = resp.json()["results"][0]
    assert result["status"] == "rejected"
    assert result["error"] == "errors.sync_conflict"

    db_session.refresh(report)
    assert report.affected_people != 500


def test_push_rejected_for_douar_outside_moqaddem_territory(client, db_session):
    douar, _territory = make_douar_in_territory(db_session, "Outside")
    other_douar, other_territory = make_douar_in_territory(db_session, "Mine")
    admin = make_user(db_session, UserRole.ADMIN, "admin5@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem5@example.com", territory=other_territory)
    headers = auth_headers(client, "moqaddem5@example.com")

    payload = report_payload(douar)
    resp = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    result = resp.json()["results"][0]
    assert result["status"] == "rejected"
    assert result["error"] == "errors.not_found"
    assert db_session.query(Report).filter_by(id=uuid.UUID(payload["id"])).count() == 0


def test_non_moqaddem_cannot_push(client, db_session):
    douar, territory = make_douar_in_territory(db_session)
    make_user(db_session, UserRole.MANAGER, "manager6@example.com", territory=territory)
    headers = auth_headers(client, "manager6@example.com")

    resp = client.post(
        "/api/v1/sync/push",
        json={"reports": [report_payload(douar)]},
        headers=headers,
    )
    assert resp.status_code == 403


def test_push_registers_media_metadata_idempotently(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin7@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem7@example.com", territory=territory)
    headers = auth_headers(client, "moqaddem7@example.com")

    captured_at = datetime.now(UTC).isoformat()
    payload = report_payload(
        douar,
        media=[
            {
                "kind": "photo",
                "mime_type": "image/jpeg",
                "size_bytes": 2048,
                "captured_at": captured_at,
            }
        ],
    )

    first = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    first_media = first.json()["results"][0]["media"]
    assert len(first_media) == 1
    assert first_media[0]["already_uploaded"] is False
    assert first_media[0]["upload_url"] is not None

    second = client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)
    second_media = second.json()["results"][0]["media"]
    assert len(second_media) == 1
    assert second_media[0]["media_id"] == first_media[0]["media_id"]

    assert db_session.query(ReportMedia).filter_by(report_id=uuid.UUID(payload["id"])).count() == 1


def test_pull_returns_own_territory_data_and_respects_cursor(client, db_session):
    douar, territory = make_douar_in_territory(db_session, "Mine")
    other_douar, other_territory = make_douar_in_territory(db_session, "Theirs")
    admin = make_user(db_session, UserRole.ADMIN, "admin8@example.com")
    make_active_config(db_session, admin)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem8@example.com", territory=territory)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem8b@example.com", territory=other_territory)
    headers = auth_headers(client, "moqaddem8@example.com")

    payload = report_payload(douar)
    client.post("/api/v1/sync/push", json={"reports": [payload]}, headers=headers)

    other_headers = auth_headers(client, "moqaddem8b@example.com")
    other_payload = report_payload(other_douar)
    client.post("/api/v1/sync/push", json={"reports": [other_payload]}, headers=other_headers)

    resp = client.get("/api/v1/sync/pull", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    report_ids = {r["id"] for r in body["reports"]}
    assert payload["id"] in report_ids
    assert other_payload["id"] not in report_ids
    douar_ids = {d["id"] for d in body["douars"]}
    assert str(douar.id) in douar_ids
    assert str(other_douar.id) not in douar_ids
    assert len(body["priorities"]) == 1
    assert "cursor" in body

    future_cursor = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    empty_resp = client.get("/api/v1/sync/pull", params={"since": future_cursor}, headers=headers)
    empty_body = empty_resp.json()
    assert empty_body["reports"] == []
    assert empty_body["douars"] == []
