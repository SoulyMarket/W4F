"""Blocked locally until PostGIS is installed (see PROGRESS.md) — every
Douar row needs the `location` column, which the second migration adds.
Written now so it's ready to run the moment that migration applies.
"""

from app.core.security import hash_password
from app.models.enums import TerritoryLevel, UserRole
from app.models.territory import Territory, UserTerritory
from app.models.user import User

PASSWORD = "correct horse battery staple"


def make_user(db_session, role, email, territory=None):
    user = User(
        full_name="User", email=email, password_hash=hash_password(PASSWORD), role=role
    )
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


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_manager_can_create_douar(client, db_session):
    province, commune = make_province_and_commune(db_session)
    make_user(db_session, UserRole.MANAGER, "manager@example.com", territory=province)
    headers = auth_headers(client, "manager@example.com")

    resp = client.post(
        "/api/v1/douars",
        json={
            "name_ar": "دوار",
            "name_fr": "Douar Test",
            "commune_id": str(commune.id),
            "lat": 31.35,
            "lon": -7.93,
            "population": 500,
            "families_count": 90,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name_fr"] == "Douar Test"
    assert abs(body["lat"] - 31.35) < 0.001
    assert abs(body["lon"] - (-7.93)) < 0.001


def test_moqaddem_cannot_create_douar(client, db_session):
    province, commune = make_province_and_commune(db_session)
    make_user(db_session, UserRole.MOQADDEM, "moqaddem@example.com", territory=province)
    headers = auth_headers(client, "moqaddem@example.com")

    resp = client.post(
        "/api/v1/douars",
        json={
            "name_ar": "دوار",
            "name_fr": "Douar Test",
            "commune_id": str(commune.id),
            "lat": 31.35,
            "lon": -7.93,
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_user_only_sees_douars_in_their_territory(client, db_session):
    province_a, commune_a = make_province_and_commune(db_session)
    from app.models.territory import Territory as T

    province_b = T(name_ar="ب", name_fr="Province B", level=TerritoryLevel.PROVINCE)
    db_session.add(province_b)
    db_session.flush()
    commune_b = T(
        name_ar="ب2", name_fr="Commune B", level=TerritoryLevel.COMMUNE, parent_id=province_b.id
    )
    db_session.add(commune_b)
    db_session.flush()

    # Create both douars directly via the ORM rather than through the write
    # endpoints, so this test doesn't also depend on admin/manager write
    # permissions working correctly.
    from app.core.geo import point_from_latlon
    from app.models.douar import Douar

    douar_a = Douar(
        name_ar="أ", name_fr="Douar A", commune_id=commune_a.id, location=point_from_latlon(31, -8)
    )
    douar_b = Douar(
        name_ar="ب", name_fr="Douar B", commune_id=commune_b.id, location=point_from_latlon(32, -9)
    )
    db_session.add_all([douar_a, douar_b])
    db_session.flush()

    make_user(db_session, UserRole.EXPERT, "expert-a@example.com", territory=province_a)
    headers_a = auth_headers(client, "expert-a@example.com")

    resp = client.get("/api/v1/douars", headers=headers_a)
    assert resp.status_code == 200
    names = {item["name_fr"] for item in resp.json()["items"]}
    assert names == {"Douar A"}

    # Cross-territory detail access returns 404, not 403 (section 6.5).
    detail_resp = client.get(f"/api/v1/douars/{douar_b.id}", headers=headers_a)
    assert detail_resp.status_code == 404


def test_admin_can_update_douar(client, db_session):
    province, commune = make_province_and_commune(db_session)
    make_user(db_session, UserRole.ADMIN, "admin2@example.com", territory=province)
    from app.core.geo import point_from_latlon
    from app.models.douar import Douar

    douar = Douar(
        name_ar="أ", name_fr="Original", commune_id=commune.id, location=point_from_latlon(31, -8)
    )
    db_session.add(douar)
    db_session.flush()
    headers = auth_headers(client, "admin2@example.com")

    resp = client.patch(
        f"/api/v1/douars/{douar.id}", json={"name_fr": "Renamed"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name_fr"] == "Renamed"
