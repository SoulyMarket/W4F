"""Model smoke tests for everything created by the initial (non-spatial)
migration. douars.location / reports.location are covered separately once
PostGIS is installed locally — see PROGRESS.md."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import (
    Language,
    ReportStatus,
    TerritoryLevel,
    UserRole,
)
from app.models.territory import Territory, UserTerritory
from app.models.user import User


def make_user(db_session, **overrides):
    defaults = dict(
        full_name="Test User",
        email=f"user-{id(overrides)}@example.com",
        password_hash="hashed",
        role=UserRole.MOQADDEM,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.flush()
    return user


def test_create_user_with_defaults(db_session):
    user = User(
        full_name="Fatima Zahra",
        email="fatima@example.com",
        password_hash="argon2-hash",
        role=UserRole.MOQADDEM,
    )
    db_session.add(user)
    db_session.flush()

    db_session.refresh(user)
    assert user.id is not None
    assert user.preferred_language == Language.AR
    assert user.is_active is True
    assert user.failed_login_count == 0
    assert user.created_at is not None


def test_user_email_must_be_unique(db_session):
    db_session.add(
        User(full_name="A", email="dup@example.com", password_hash="h", role=UserRole.ADMIN)
    )
    db_session.flush()
    db_session.add(
        User(full_name="B", email="dup@example.com", password_hash="h", role=UserRole.ADMIN)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_role_enum_round_trips(db_session):
    user = User(
        full_name="Expert", email="expert@example.com", password_hash="h", role=UserRole.EXPERT
    )
    db_session.add(user)
    db_session.flush()
    db_session.expire(user)
    assert user.role == UserRole.EXPERT
    assert user.role.value == "expert"


def test_territory_hierarchy(db_session):
    province = Territory(name_ar="الحوز", name_fr="Al Haouz", level=TerritoryLevel.PROVINCE)
    db_session.add(province)
    db_session.flush()

    commune = Territory(
        name_ar="تحناوت",
        name_fr="Tahanaout",
        level=TerritoryLevel.COMMUNE,
        parent_id=province.id,
    )
    db_session.add(commune)
    db_session.flush()
    db_session.refresh(commune)

    assert commune.parent_id == province.id


def test_user_territory_assignment(db_session):
    user = make_user(db_session, email="territory-user@example.com")
    territory = Territory(name_ar="إقليم", name_fr="Province", level=TerritoryLevel.PROVINCE)
    db_session.add(territory)
    db_session.flush()

    db_session.add(UserTerritory(user_id=user.id, territory_id=territory.id))
    db_session.flush()

    rows = (
        db_session.query(UserTerritory)
        .filter_by(user_id=user.id, territory_id=territory.id)
        .all()
    )
    assert len(rows) == 1


def test_user_territory_composite_pk_prevents_duplicates(db_session):
    user = make_user(db_session, email="dup-territory@example.com")
    territory = Territory(name_ar="إقليم2", name_fr="Province2", level=TerritoryLevel.PROVINCE)
    db_session.add(territory)
    db_session.flush()

    db_session.add(UserTerritory(user_id=user.id, territory_id=territory.id))
    db_session.flush()
    db_session.add(UserTerritory(user_id=user.id, territory_id=territory.id))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_report_status_defaults_to_submitted(db_session):
    import uuid

    from app.models.douar import Douar
    from app.models.enums import InterruptionFrequency, ProblemType, SeverityLevel, WaterSource
    from app.models.report import Report

    territory = Territory(name_ar="ت", name_fr="T", level=TerritoryLevel.COMMUNE)
    db_session.add(territory)
    db_session.flush()

    douar = Douar(name_ar="دوار", name_fr="Douar", commune_id=territory.id)
    db_session.add(douar)
    db_session.flush()

    moqaddem = make_user(db_session, email="moqaddem@example.com")

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
        collected_at=datetime.now(UTC),
    )
    db_session.add(report)
    db_session.flush()
    db_session.refresh(report)

    assert report.status == ReportStatus.SUBMITTED
    assert report.version == 1
