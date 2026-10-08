from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.db.session import get_db
from app.i18n import t
from app.models.enums import AuditAction, UserRole
from app.models.territory import Territory
from app.models.user import User
from app.schemas.territories import TerritoryCreate, TerritoryOut, TerritoryUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/territories", tags=["territories"])

_require_admin = require_roles(UserRole.ADMIN)


def _get_territory_or_404(db: Session, territory_id, lang: str) -> Territory:
    territory = db.get(Territory, territory_id)
    if territory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=t("errors.not_found", lang)
        )
    return territory


@router.post("", response_model=TerritoryOut, status_code=status.HTTP_201_CREATED)
def create_territory(
    body: TerritoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> Territory:
    lang = get_request_language(request)
    territory = Territory(
        name_ar=body.name_ar, name_fr=body.name_fr, level=body.level, parent_id=body.parent_id
    )
    db.add(territory)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t("errors.validation_error", lang),
        ) from None

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.CREATE,
        entity_type="territory",
        entity_id=territory.id,
        new_value={
            "name_fr": territory.name_fr,
            "level": territory.level.value,
            "parent_id": str(territory.parent_id) if territory.parent_id else None,
        },
    )
    db.commit()
    db.refresh(territory)
    return territory


@router.get("", response_model=list[TerritoryOut])
def list_territories(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> list[Territory]:
    return db.query(Territory).order_by(Territory.name_fr).all()


@router.get("/{territory_id}", response_model=TerritoryOut)
def get_territory(
    territory_id,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> Territory:
    return _get_territory_or_404(db, territory_id, get_request_language(request))


@router.patch("/{territory_id}", response_model=TerritoryOut)
def update_territory(
    territory_id,
    body: TerritoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> Territory:
    lang = get_request_language(request)
    territory = _get_territory_or_404(db, territory_id, lang)

    old_value = {
        "name_ar": territory.name_ar,
        "name_fr": territory.name_fr,
        "parent_id": str(territory.parent_id) if territory.parent_id else None,
    }
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(territory, field, value)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t("errors.validation_error", lang),
        ) from None

    new_value = {
        "name_ar": territory.name_ar,
        "name_fr": territory.name_fr,
        "parent_id": str(territory.parent_id) if territory.parent_id else None,
    }
    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="territory",
        entity_id=territory.id,
        old_value=old_value,
        new_value=new_value,
    )
    db.commit()
    db.refresh(territory)
    return territory
