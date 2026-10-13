"""Exercises the real presigned-URL / head_object / sha256 flow against a
local moto_server standing in for MinIO (see conftest.py's moto_s3_endpoint
fixture and PROGRESS.md for why)."""

import hashlib
import uuid
from datetime import UTC, date, datetime

import requests

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
from app.models.report import Report
from app.models.report_media import ReportMedia
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


def make_report(db_session, douar, moqaddem):
    report = Report(
        id=uuid.uuid4(),
        douar_id=douar.id,
        moqaddem_id=moqaddem.id,
        water_source=WaterSource.WELL,
        problem_type=ProblemType.NO_WATER,
        problem_started_on=date(2026, 1, 1),
        duration_days=5,
        interruption_frequency=InterruptionFrequency.DAILY,
        has_alternative_source=False,
        alternative_distance_km=None,
        severity_reported=SeverityLevel.HIGH,
        water_quality_risk=False,
        affected_families=3,
        affected_people=15,
        location=point_from_latlon(31, -8),
        collected_at=datetime.now(UTC),
        status=ReportStatus.SUBMITTED,
    )
    db_session.add(report)
    db_session.flush()
    return report


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_upload_url_request_creates_pending_media_row(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "moqaddem@example.com")

    resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "image/jpeg",
            "size_bytes": 1024,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "upload_url" in body
    assert body["object_key"].startswith(f"reports/{report.id}/")

    media = db_session.get(ReportMedia, uuid.UUID(body["media_id"]))
    assert media.upload_status.value == "pending"
    assert media.object_key == body["object_key"]


def test_upload_url_rejects_invalid_mime_type(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem2@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "moqaddem2@example.com")

    resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "application/pdf",
            "size_bytes": 1024,
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_upload_url_rejects_oversized_photo(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem3@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "moqaddem3@example.com")

    resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "image/jpeg",
            "size_bytes": 11 * 1024 * 1024,
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_upload_url_outside_territory_returns_404(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    other_territory = Territory(name_ar="ب", name_fr="Other", level=TerritoryLevel.COMMUNE)
    db_session.add(other_territory)
    db_session.flush()
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem4@example.com", territory=territory
    )
    make_user(db_session, UserRole.EXPERT, "expert@example.com", territory=other_territory)
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "expert@example.com")

    resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "image/jpeg",
            "size_bytes": 1024,
        },
        headers=headers,
    )
    assert resp.status_code == 404


def test_full_upload_and_complete_flow(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem5@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "moqaddem5@example.com")

    content = b"fake jpeg bytes for testing"
    sha256 = hashlib.sha256(content).hexdigest()

    create_resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "image/jpeg",
            "size_bytes": len(content),
        },
        headers=headers,
    )
    assert create_resp.status_code == 200
    body = create_resp.json()

    put_resp = requests.put(
        body["upload_url"], data=content, headers={"Content-Type": "image/jpeg"}
    )
    assert put_resp.status_code == 200

    complete_resp = client.post(
        f"/api/v1/media/{body['media_id']}/complete",
        json={"sha256": sha256},
        headers=headers,
    )
    assert complete_resp.status_code == 200
    complete_body = complete_resp.json()
    assert complete_body["upload_status"] == "uploaded"
    assert complete_body["download_url"] is not None

    # The presigned GET URL actually works and returns the uploaded bytes.
    get_resp = requests.get(complete_body["download_url"])
    assert get_resp.status_code == 200
    assert get_resp.content == content


def test_complete_rejects_sha256_mismatch(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem6@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "moqaddem6@example.com")

    content = b"some real bytes"
    create_resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "image/jpeg",
            "size_bytes": len(content),
        },
        headers=headers,
    )
    body = create_resp.json()
    requests.put(body["upload_url"], data=content, headers={"Content-Type": "image/jpeg"})

    wrong_sha256 = hashlib.sha256(b"different bytes entirely").hexdigest()
    complete_resp = client.post(
        f"/api/v1/media/{body['media_id']}/complete",
        json={"sha256": wrong_sha256},
        headers=headers,
    )
    assert complete_resp.status_code == 422

    media = db_session.get(ReportMedia, uuid.UUID(body["media_id"]))
    assert media.upload_status.value == "pending"


def test_complete_rejects_when_object_not_actually_uploaded(client, db_session, moto_s3_endpoint):
    douar, territory = make_douar_in_territory(db_session)
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem7@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem)
    headers = auth_headers(client, "moqaddem7@example.com")

    create_resp = client.post(
        "/api/v1/media/upload-url",
        json={
            "report_id": str(report.id),
            "kind": "photo",
            "mime_type": "image/jpeg",
            "size_bytes": 100,
        },
        headers=headers,
    )
    media_id = create_resp.json()["media_id"]

    # Never actually PUT the bytes.
    complete_resp = client.post(
        f"/api/v1/media/{media_id}/complete",
        json={"sha256": "a" * 64},
        headers=headers,
    )
    assert complete_resp.status_code == 422
