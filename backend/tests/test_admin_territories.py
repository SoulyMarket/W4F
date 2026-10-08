from app.core.security import hash_password
from app.models.enums import TerritoryLevel, UserRole
from app.models.territory import Territory, UserTerritory
from app.models.user import User

PASSWORD = "correct horse battery staple"


def make_user(db_session, role=UserRole.ADMIN, email="admin@example.com"):
    user = User(
        full_name="Admin", email=email, password_hash=hash_password(PASSWORD), role=role
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_territory(db_session, name="Province", level=TerritoryLevel.PROVINCE, parent=None):
    territory = Territory(
        name_ar=name, name_fr=name, level=level, parent_id=parent.id if parent else None
    )
    db_session.add(territory)
    db_session.flush()
    return territory


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_can_create_territory(client, db_session):
    make_user(db_session)
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(
        "/api/v1/territories",
        json={"name_ar": "إقليم", "name_fr": "Province Test", "level": "province"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name_fr"] == "Province Test"


def test_admin_can_create_commune_under_province(client, db_session):
    make_user(db_session)
    province = make_territory(db_session)
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(
        "/api/v1/territories",
        json={
            "name_ar": "جماعة",
            "name_fr": "Commune Test",
            "level": "commune",
            "parent_id": str(province.id),
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["parent_id"] == str(province.id)


def test_admin_can_list_territories(client, db_session):
    make_user(db_session)
    make_territory(db_session, name="P1")
    make_territory(db_session, name="P2")
    headers = auth_headers(client, "admin@example.com")

    resp = client.get("/api/v1/territories", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_admin_can_update_territory(client, db_session):
    make_user(db_session)
    territory = make_territory(db_session)
    headers = auth_headers(client, "admin@example.com")

    resp = client.patch(
        f"/api/v1/territories/{territory.id}",
        json={"name_fr": "Renamed"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name_fr"] == "Renamed"


def test_non_admin_cannot_create_territory(client, db_session):
    make_user(db_session, role=UserRole.MANAGER, email="manager@example.com")
    headers = auth_headers(client, "manager@example.com")

    resp = client.post(
        "/api/v1/territories",
        json={"name_ar": "x", "name_fr": "x", "level": "province"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_admin_can_assign_territories_to_user(client, db_session):
    make_user(db_session)
    target = User(
        full_name="Expert",
        email="expert@example.com",
        password_hash=hash_password(PASSWORD),
        role=UserRole.EXPERT,
    )
    db_session.add(target)
    db_session.flush()
    t1 = make_territory(db_session, name="T1")
    t2 = make_territory(db_session, name="T2")
    headers = auth_headers(client, "admin@example.com")

    resp = client.put(
        f"/api/v1/users/{target.id}/territories",
        json={"territory_ids": [str(t1.id), str(t2.id)]},
        headers=headers,
    )
    assert resp.status_code == 200

    assigned = db_session.query(UserTerritory).filter_by(user_id=target.id).all()
    assert {row.territory_id for row in assigned} == {t1.id, t2.id}


def test_assigning_territories_replaces_previous_assignment(client, db_session):
    make_user(db_session)
    target = User(
        full_name="Expert",
        email="expert2@example.com",
        password_hash=hash_password(PASSWORD),
        role=UserRole.EXPERT,
    )
    db_session.add(target)
    db_session.flush()
    t1 = make_territory(db_session, name="T1")
    t2 = make_territory(db_session, name="T2")
    db_session.add(UserTerritory(user_id=target.id, territory_id=t1.id))
    db_session.flush()
    headers = auth_headers(client, "admin@example.com")

    resp = client.put(
        f"/api/v1/users/{target.id}/territories",
        json={"territory_ids": [str(t2.id)]},
        headers=headers,
    )
    assert resp.status_code == 200

    assigned = db_session.query(UserTerritory).filter_by(user_id=target.id).all()
    assert {row.territory_id for row in assigned} == {t2.id}


def test_non_admin_cannot_assign_territories(client, db_session):
    make_user(db_session, role=UserRole.MANAGER, email="manager2@example.com")
    target = User(
        full_name="Expert",
        email="expert3@example.com",
        password_hash=hash_password(PASSWORD),
        role=UserRole.EXPERT,
    )
    db_session.add(target)
    db_session.flush()
    headers = auth_headers(client, "manager2@example.com")

    resp = client.put(
        f"/api/v1/users/{target.id}/territories",
        json={"territory_ids": []},
        headers=headers,
    )
    assert resp.status_code == 403
