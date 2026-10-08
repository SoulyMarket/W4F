"""Territory scoping (section 1 + 6.5): "a user assigned to a province sees
all its communes." Applied in a shared query helper used by every list/
detail endpoint that reads territory-bound data (douars, reports, and
anything reachable from them) — never only in route guards, per section 6.5.

A user with no territory assignment sees nothing (an empty accessible set),
not everything: least privilege (section 1) is the default, not an opt-in.
"""

import uuid
from collections import defaultdict

from sqlalchemy import ColumnElement
from sqlalchemy.orm import Session

from app.models.territory import Territory, UserTerritory
from app.models.user import User


def _children_by_parent(db: Session) -> dict[uuid.UUID, list[uuid.UUID]]:
    children: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for territory_id, parent_id in db.query(Territory.id, Territory.parent_id).all():
        if parent_id is not None:
            children[parent_id].append(territory_id)
    return children


def get_descendant_ids(db: Session, root_ids: set[uuid.UUID]) -> set[uuid.UUID]:
    """`root_ids` plus every territory reachable by following parent_id
    downward from them (a province's communes, transitively)."""
    if not root_ids:
        return set()
    children_by_parent = _children_by_parent(db)
    result: set[uuid.UUID] = set()
    stack = list(root_ids)
    while stack:
        territory_id = stack.pop()
        if territory_id in result:
            continue
        result.add(territory_id)
        stack.extend(children_by_parent.get(territory_id, []))
    return result


def get_accessible_territory_ids(db: Session, user: User) -> set[uuid.UUID]:
    """Every territory `user` is directly assigned to, plus all of their
    descendants (so a province assignment reaches its communes)."""
    assigned = {
        row.territory_id
        for row in db.query(UserTerritory.territory_id).filter_by(user_id=user.id).all()
    }
    return get_descendant_ids(db, assigned)


def territory_scope_filter(
    territory_id_column: ColumnElement, db: Session, user: User
) -> ColumnElement:
    """A boolean SQL expression to AND into any query whose rows are bound
    to a territory via `territory_id_column` (e.g. Douar.commune_id,
    or Report.douar_id joined through Douar). Use this in every
    list/detail endpoint's query rather than checking access after the
    fact — section 6.5 requires scoping in the query itself."""
    accessible = get_accessible_territory_ids(db, user)
    return territory_id_column.in_(accessible)
