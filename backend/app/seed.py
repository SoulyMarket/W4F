"""Demo data for Al Haouz province (section 9, step 1.2).

Idempotent: re-running does not create duplicates — every row is looked up
by a natural key (email for users, name_fr for territories/douars, a fixed
tuple of (douar, moqaddem, problem_started_on) for reports) before insert.

Needs the postgis migration applied (douars/reports have a `location`
geography column) — see PROGRESS.md for why that's a separate migration
from the rest of the schema.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.douar import Douar
from app.models.enums import (
    InterruptionFrequency,
    ProblemType,
    SeverityLevel,
    TerritoryLevel,
    UserRole,
    WaterSource,
)
from app.models.report import Report
from app.models.scoring_config import ScoringConfig
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.services.scoring import DEFAULT_WEIGHTS

# name_fr -> (lat, lon) roughly within Al Haouz province, Morocco.
COMMUNES = {
    "Tahanaout": (31.3500, -7.9333),
    "Asni": (31.2667, -7.9833),
    "Ouirgane": (31.1833, -8.1000),
}

DOUARS: list[tuple[str, str, str, float, float, int, int]] = [
    # name_ar, name_fr, commune_name_fr, lat, lon, population, families
    ("أيت أورير", "Ait Ourir", "Tahanaout", 31.3550, -7.6670, 1200, 220),
    ("تنسيفت", "Tansift", "Tahanaout", 31.3610, -7.9100, 650, 110),
    ("إغرم", "Ighrem", "Tahanaout", 31.3300, -7.9500, 430, 80),
    ("إيمليل", "Imlil", "Asni", 31.1378, -7.9178, 900, 160),
    ("أرمد", "Armed", "Asni", 31.1500, -7.8900, 540, 95),
    ("تاكاترت", "Tacheddirt", "Asni", 31.1900, -7.8300, 310, 60),
    ("أسكاون", "Asgaour", "Asni", 31.2200, -7.9700, 470, 85),
    ("أويرغان", "Ouirgane village", "Ouirgane", 31.1700, -8.0800, 380, 70),
    ("تيزي ن تست", "Tizi n'Test", "Ouirgane", 31.1000, -8.1500, 260, 50),
    ("إجوكاك", "Ijoukak", "Ouirgane", 31.0800, -8.1700, 600, 115),
]

DEMO_USERS: list[tuple[str, str, UserRole]] = [
    ("Admin Demo", "admin@w4f.ma", UserRole.ADMIN),
    ("Responsable Demo", "manager@w4f.ma", UserRole.MANAGER),
    ("Expert Demo", "expert@w4f.ma", UserRole.EXPERT),
    ("Moqaddem Demo", "moqaddem@w4f.ma", UserRole.MOQADDEM),
]

DEMO_PASSWORD = "DemoPass1234"


def _point(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def get_or_create_territory(db: Session, name_fr: str, **kwargs) -> Territory:
    existing = db.query(Territory).filter_by(name_fr=name_fr).one_or_none()
    if existing:
        return existing
    territory = Territory(name_fr=name_fr, **kwargs)
    db.add(territory)
    db.flush()
    return territory


def get_or_create_douar(db: Session, name_fr: str, **kwargs) -> Douar:
    existing = db.query(Douar).filter_by(name_fr=name_fr).one_or_none()
    if existing:
        return existing
    douar = Douar(name_fr=name_fr, **kwargs)
    db.add(douar)
    db.flush()
    return douar


def get_or_create_user(db: Session, email: str, **kwargs) -> User:
    existing = db.query(User).filter_by(email=email).one_or_none()
    if existing:
        return existing
    user = User(email=email, **kwargs)
    db.add(user)
    db.flush()
    return user


def seed(db: Session) -> None:
    province = get_or_create_territory(
        db, name_fr="Al Haouz", name_ar="الحوز", level=TerritoryLevel.PROVINCE
    )

    commune_by_name: dict[str, Territory] = {}
    for name_fr in COMMUNES:
        commune_by_name[name_fr] = get_or_create_territory(
            db,
            name_fr=name_fr,
            name_ar=name_fr,  # demo data only; real communes get proper Arabic names
            level=TerritoryLevel.COMMUNE,
            parent_id=province.id,
        )

    douars: list[Douar] = []
    for name_ar, name_fr, commune_name, lat, lon, population, families in DOUARS:
        commune = commune_by_name[commune_name]
        douar = get_or_create_douar(
            db,
            name_fr=name_fr,
            name_ar=name_ar,
            commune_id=commune.id,
            location=_point(lat, lon),
            population=population,
            families_count=families,
        )
        douars.append(douar)

    users_by_role: dict[UserRole, User] = {}
    for full_name, email, role in DEMO_USERS:
        user = get_or_create_user(
            db,
            email=email,
            full_name=full_name,
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
        )
        users_by_role[role] = user
        if role != UserRole.ADMIN:
            already_assigned = (
                db.query(UserTerritory)
                .filter_by(user_id=user.id, territory_id=province.id)
                .one_or_none()
            )
            if not already_assigned:
                db.add(UserTerritory(user_id=user.id, territory_id=province.id))

    if not db.query(ScoringConfig).filter_by(is_active=True).one_or_none():
        db.add(
            ScoringConfig(
                weights=DEFAULT_WEIGHTS,
                is_active=True,
                created_by=users_by_role[UserRole.ADMIN].id,
            )
        )

    moqaddem = users_by_role[UserRole.MOQADDEM]
    water_sources = list(WaterSource)
    problem_types = list(ProblemType)
    frequencies = list(InterruptionFrequency)
    severities = list(SeverityLevel)

    for i in range(15):
        douar = douars[i % len(douars)]
        _, _, _, douar_lat, douar_lon, _, _ = DOUARS[i % len(DOUARS)]
        started_on = date(2026, 1, 1) + timedelta(days=i * 5)
        existing = (
            db.query(Report)
            .filter_by(douar_id=douar.id, moqaddem_id=moqaddem.id, problem_started_on=started_on)
            .one_or_none()
        )
        if existing:
            continue
        db.add(
            Report(
                id=uuid.uuid4(),
                douar_id=douar.id,
                moqaddem_id=moqaddem.id,
                water_source=water_sources[i % len(water_sources)],
                problem_type=problem_types[i % len(problem_types)],
                problem_started_on=started_on,
                duration_days=(i + 1) * 3,
                interruption_frequency=frequencies[i % len(frequencies)],
                has_alternative_source=i % 2 == 0,
                alternative_distance_km=None if i % 2 == 0 else float(1 + i % 5),
                severity_reported=severities[i % len(severities)],
                water_quality_risk=i % 4 == 0,
                affected_families=5 + i,
                affected_people=20 + i * 3,
                observations=f"Demo report #{i + 1}",
                location=_point(douar_lat, douar_lon),
                location_accuracy_m=10.0,
                collected_at=datetime.now(UTC) - timedelta(days=i),
            )
        )

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
