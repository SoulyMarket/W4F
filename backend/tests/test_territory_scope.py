from app.core.security import hash_password
from app.models.enums import TerritoryLevel, UserRole
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.services.territory_scope import get_accessible_territory_ids


def make_user(db_session, email="scope-user@example.com"):
    user = User(
        full_name="Scope User",
        email=email,
        password_hash=hash_password("whatever1234"),
        role=UserRole.EXPERT,
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_territory(db_session, name, level, parent=None):
    territory = Territory(
        name_ar=name, name_fr=name, level=level, parent_id=parent.id if parent else None
    )
    db_session.add(territory)
    db_session.flush()
    return territory


def test_user_with_no_assignment_sees_nothing(db_session):
    user = make_user(db_session)
    assert get_accessible_territory_ids(db_session, user) == set()


def test_user_assigned_directly_to_a_commune_sees_only_that_commune(db_session):
    user = make_user(db_session)
    province = make_territory(db_session, "Province", TerritoryLevel.PROVINCE)
    commune_a = make_territory(db_session, "Commune A", TerritoryLevel.COMMUNE, parent=province)
    commune_b = make_territory(db_session, "Commune B", TerritoryLevel.COMMUNE, parent=province)
    db_session.add(UserTerritory(user_id=user.id, territory_id=commune_a.id))
    db_session.flush()

    accessible = get_accessible_territory_ids(db_session, user)
    assert accessible == {commune_a.id}
    assert commune_b.id not in accessible
    assert province.id not in accessible


def test_user_assigned_to_a_province_sees_all_its_communes(db_session):
    user = make_user(db_session)
    province = make_territory(db_session, "Province", TerritoryLevel.PROVINCE)
    commune_a = make_territory(db_session, "Commune A", TerritoryLevel.COMMUNE, parent=province)
    commune_b = make_territory(db_session, "Commune B", TerritoryLevel.COMMUNE, parent=province)
    other_province = make_territory(db_session, "Other", TerritoryLevel.PROVINCE)
    other_commune = make_territory(
        db_session, "Other Commune", TerritoryLevel.COMMUNE, parent=other_province
    )
    db_session.add(UserTerritory(user_id=user.id, territory_id=province.id))
    db_session.flush()

    accessible = get_accessible_territory_ids(db_session, user)
    assert accessible == {province.id, commune_a.id, commune_b.id}
    assert other_province.id not in accessible
    assert other_commune.id not in accessible


def test_multiple_assignments_are_unioned(db_session):
    user = make_user(db_session)
    province_a = make_territory(db_session, "Province A", TerritoryLevel.PROVINCE)
    commune_a = make_territory(db_session, "Commune A", TerritoryLevel.COMMUNE, parent=province_a)
    province_b = make_territory(db_session, "Province B", TerritoryLevel.PROVINCE)
    commune_b = make_territory(db_session, "Commune B", TerritoryLevel.COMMUNE, parent=province_b)

    db_session.add(UserTerritory(user_id=user.id, territory_id=commune_a.id))
    db_session.add(UserTerritory(user_id=user.id, territory_id=province_b.id))
    db_session.flush()

    accessible = get_accessible_territory_ids(db_session, user)
    assert accessible == {commune_a.id, province_b.id, commune_b.id}
    assert province_a.id not in accessible
