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


def get_accessible_territory_ids(db: Session, user: User) -> set[uuid.UUID]:
    """Every territory `user` is directly assigned to, plus all of their
    descendants (so a province assignment reaches its communes)."""
    assigned = {
        row.territory_id
        for row in db.query(UserTerritory.territory_id).filter_by(user_id=user.id).all()
    }
    if not assigned:
        return set()

    children_by_parent: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for territory_id, parent_id in db.query(Territory.id, Territory.parent_id).all():
        if parent_id is not None:
            children_by_parent[parent_id].append(territory_id)

    accessible: set[uuid.UUID] = set()
    stack = list(assigned)
    while stack:
        territory_id = stack.pop()
        if territory_id in accessible:
            continue
        accessible.add(territory_id)
        stack.extend(children_by_parent.get(territory_id, []))
    return accessible


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
