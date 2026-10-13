"""The 'priority changed by >= 10 points' notification trigger (section 5)
— no recipient is specified there for this one trigger, unlike the others;
ruling: moqaddem + all managers, same audience as validated/project
triggers. See PROGRESS.md.
"""

import uuid
from datetime import UTC, date, datetime

from app.core.geo import point_from_latlon
from app.core.security import hash_password
from app.models.douar import Douar
from app.models.enums import (
    InterruptionFrequency,
    NotificationType,
    ProblemType,
    SeverityLevel,
    TerritoryLevel,
    UserRole,
    WaterSource,
)
from app.models.notification import Notification
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.services.priority import recompute_priority
from app.services.scoring import DEFAULT_WEIGHTS

PASSWORD = "x" * 10


def make_user(db_session, role, email, territory=None):
    user = User(full_name="U", email=email, password_hash=hash_password(PASSWORD), role=role)
    db_session.add(user)
    db_session.flush()
    if territory is not None:
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


def make_report(db_session, douar, moqaddem, **overrides):
    defaults = dict(
        id=uuid.uuid4(),
        douar_id=douar.id,
        moqaddem_id=moqaddem.id,
        water_source=WaterSource.WELL,
        problem_type=ProblemType.NO_WATER,
        problem_started_on=date(2026, 1, 1),
        duration_days=5,
        interruption_frequency=InterruptionFrequency.RARE,
        has_alternative_source=True,
        alternative_distance_km=0.0,
        severity_reported=SeverityLevel.LOW,
        water_quality_risk=False,
        affected_families=1,
        affected_people=0,
        location=point_from_latlon(31, -8),
        collected_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    report = Report(**defaults)
    db_session.add(report)
    db_session.flush()
    return report


def test_no_notification_on_first_ever_priority_computation(db_session):
    douar, territory = make_douar(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()
    moqaddem = make_user(db_session, UserRole.MOQADDEM, "moqaddem@example.com", territory=territory)
    report = make_report(db_session, douar, moqaddem)

    recompute_priority(db_session, report, config)
    db_session.flush()

    notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert notifs == []


def test_notification_sent_when_score_changes_by_10_or_more(db_session):
    douar, territory = make_douar(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin2@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem2@example.com", territory=territory
    )
    manager = make_user(db_session, UserRole.MANAGER, "manager2@example.com", territory=territory)
    report = make_report(db_session, douar, moqaddem, severity_reported=SeverityLevel.LOW)

    recompute_priority(db_session, report, config)
    db_session.flush()

    # Mutate the report to guarantee a >=10 point swing (low -> critical
    # severity alone is 0.75 * 15 = 11.25 points), then recompute again.
    report.severity_reported = SeverityLevel.CRITICAL
    db_session.flush()
    recompute_priority(db_session, report, config)
    db_session.flush()

    moqaddem_notifs = db_session.query(Notification).filter_by(user_id=moqaddem.id).all()
    assert any(n.type == NotificationType.PRIORITY_CHANGED for n in moqaddem_notifs)
    manager_notifs = db_session.query(Notification).filter_by(user_id=manager.id).all()
    assert any(n.type == NotificationType.PRIORITY_CHANGED for n in manager_notifs)


def test_no_notification_when_score_change_is_small(db_session):
    douar, territory = make_douar(db_session)
    admin = make_user(db_session, UserRole.ADMIN, "admin3@example.com")
    config = ScoringConfig(weights=DEFAULT_WEIGHTS, is_active=True, created_by=admin.id)
    db_session.add(config)
    db_session.flush()
    moqaddem = make_user(
        db_session, UserRole.MOQADDEM, "moqaddem3@example.com", territory=territory
    )
    report = make_report(db_session, douar, moqaddem, duration_days=5)

    recompute_priority(db_session, report, config)
    db_session.flush()

    # duration 5 -> 6 days changes the "duration" criterion by
    # (1/30)*15 = 0.5 points — well under the 10-point threshold.
    report.duration_days = 6
    db_session.flush()
    recompute_priority(db_session, report, config)
    db_session.flush()

    notifs = db_session.query(Notification).filter_by(
        user_id=moqaddem.id, type=NotificationType.PRIORITY_CHANGED
    ).all()
    assert notifs == []
