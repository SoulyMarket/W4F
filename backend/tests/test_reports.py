"""Blocked locally until PostGIS is installed (see PROGRESS.md) — every
Report row needs the `location` column. Written now so it's ready to run
the moment the postgis migration applies.
"""

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
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.models.validation import Validation
from app.services.scoring import DEFAULT_WEIGHTS

PASSWORD = "correct horse battery staple"


def make_user(db_session, role, email, territory=None):
    user = User(full_name="User", email=email, password_hash=hash_password(PASSWORD), role=role)
    db_session.add(user)
    db_session.flush()
    if territory is not None:
        db_session.add(UserTerritory(user_id=user.id, territory_id=territory.id))
        db_session.flush()
    return user


def make_province_and_commune(db_session):
    province = Territory(name_ar="إقليم", name_fr="Province", level=TerritoryLevel.PROVINCE)
    db_session.add(province)
    db_session.flush()
    commune = Territory(
        name_ar="جماعة", name_fr="Commune", level=TerritoryLevel.COMMUNE, parent_id=province.id
    )
    db_session.add(commune)
    db_session.flush()
    return province, commune


def make_douar(db_session, commune, name="Douar"):
    douar = Douar(
        name_ar=name, name_fr=name, commune_id=commune.id, location=point_from_latlon(31, -8)
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
    )
    defaults.update(overrides)
    report = Report(**defaults)
    db_session.add(report)
    db_session.flush()
    return report


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_user_only_sees_reports_in_their_territory(client, db_session):
    province_a, commune_a = make_province_and_commune(db_session)
    province_b = Territory(name_ar="ب", name_fr="Province B", level=TerritoryLevel.PROVINCE)
    db_session.add(province_b)
    db_session.flush()
    commune_b = Territory(
        name_ar="ب2", name_fr="Commune B", level=TerritoryLevel.COMMUNE, parent_id=province_b.id
    )
    db_session.add(commune_b)
    db_session.flush()

    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem@example.com", territory=province_a
    )
    douar_a = make_douar(db_session, commune_a, "Douar A")
    douar_b = make_douar(db_session, commune_b, "Douar B")
    report_a = make_report(db_session, douar_a, moqaddem)
    report_b = make_report(db_session, douar_b, moqaddem)

    make_user(db_session, UserRole.EXPERT, "expert-a@example.com", territory=province_a)
    headers = auth_headers(client, "expert-a@example.com")

    resp = client.get("/api/v1/reports", headers=headers)
    assert resp.status_code == 200
    ids = {item["id"] for item in resp.json()["items"]}
    assert ids == {str(report_a.id)}

    cross_territory = client.get(f"/api/v1/reports/{report_b.id}", headers=headers)
    assert cross_territory.status_code == 404


def test_filter_by_status(client, db_session):
    province, commune = make_province_and_commune(db_session)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem2@example.com", territory=province)
    douar = make_douar(db_session, commune)
    make_report(db_session, douar, moqaddem, status=ReportStatus.SUBMITTED)
    make_report(db_session, douar, moqaddem, status=ReportStatus.VALIDATED)

    make_user(db_session, UserRole.EXPERT, "expert2@example.com", territory=province)
    headers = auth_headers(client, "expert2@example.com")

    resp = client.get("/api/v1/reports?status=validated", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "validated"


def test_sort_by_score(client, db_session):
    province, commune = make_province_and_commune(db_session)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem3@example.com", territory=province)
    douar = make_douar(db_session, commune)
    low_report = make_report(db_session, douar, moqaddem)
    high_report = make_report(db_session, douar, moqaddem)

    admin = make_user(db_session, UserRole.ADMIN, "admin3@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()

    db_session.add(
        Priority(report_id=low_report.id, score=10, breakdown=[], config_id=config.id)
    )
    db_session.add(
        Priority(report_id=high_report.id, score=90, breakdown=[], config_id=config.id)
    )
    db_session.flush()

    make_user(db_session, UserRole.EXPERT, "expert3@example.com", territory=province)
    headers = auth_headers(client, "expert3@example.com")

    resp = client.get("/api/v1/reports?sort_by_score=true", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["id"] == str(high_report.id)
    assert items[1]["id"] == str(low_report.id)


def test_report_detail_includes_media_priority_and_validations(client, db_session):
    province, commune = make_province_and_commune(db_session)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem4@example.com", territory=province)
    douar = make_douar(db_session, commune)
    report = make_report(db_session, douar, moqaddem)

    from app.models.enums import MediaKind, UploadStatus
    from app.models.report_media import ReportMedia

    db_session.add(
        ReportMedia(
            report_id=report.id,
            kind=MediaKind.PHOTO,
            object_key="reports/photo1.jpg",
            mime_type="image/jpeg",
            size_bytes=1000,
            upload_status=UploadStatus.UPLOADED,
        )
    )

    admin = make_user(db_session, UserRole.ADMIN, "admin4@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()
    breakdown = [
        {
            "criterion": "severity",
            "value": "high",
            "weight": 15,
            "points": 11.25,
            "reason_key": "priority.severity",
            "reason_params": {"severity": "high"},
        }
    ]
    db_session.add(
        Priority(report_id=report.id, score=55, breakdown=breakdown, config_id=config.id)
    )

    expert = make_user(db_session, UserRole.EXPERT, "expert4@example.com", territory=province)
    db_session.add(
        Validation(
            report_id=report.id,
            expert_id=expert.id,
            decision="validated",
            urgency_opinion="high",
        )
    )
    db_session.flush()
    headers = auth_headers(client, "expert4@example.com")

    resp = client.get(f"/api/v1/reports/{report.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["media"]) == 1
    assert body["media"][0]["object_key"] == "reports/photo1.jpg"
    assert body["priority"]["score"] == 55
    assert len(body["validations"]) == 1
    assert body["validations"][0]["decision"] == "validated"


def test_report_with_no_priority_has_null_priority_and_score(client, db_session):
    province, commune = make_province_and_commune(db_session)
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem5@example.com", territory=province)
    douar = make_douar(db_session, commune)
    report = make_report(db_session, douar, moqaddem)

    make_user(db_session, UserRole.EXPERT, "expert5@example.com", territory=province)
    headers = auth_headers(client, "expert5@example.com")

    resp = client.get(f"/api/v1/reports/{report.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["priority"] is None
    assert body["score"] is None
