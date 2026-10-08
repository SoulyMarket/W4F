from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.core.geo import latlon_from_point, point_from_latlon
from app.db.session import get_db
from app.i18n import t
from app.models.douar import Douar
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.douars import DouarCreate, DouarListOut, DouarOut, DouarUpdate
from app.services.audit import write_audit_log
from app.services.territory_scope import territory_scope_filter

router = APIRouter(prefix="/douars", tags=["douars"])

_require_any = require_roles(*list(UserRole))
_require_write = require_roles(UserRole.ADMIN, UserRole.MANAGER)


def _to_out(douar: Douar) -> DouarOut:
    coords = latlon_from_point(douar.location)
    return DouarOut(
        id=douar.id,
        name_ar=douar.name_ar,
        name_fr=douar.name_fr,
        commune_id=douar.commune_id,
        lat=coords[0] if coords else None,
        lon=coords[1] if coords else None,
        population=douar.population,
        families_count=douar.families_count,
        notes=douar.notes,
    )


def _get_douar_or_404(db: Session, douar_id, user: User, lang: str) -> Douar:
    """404, never 403, for a douar outside the caller's territory scope —
    section 6.5 explicitly requires this (a cross-territory probe must not
    even reveal that the resource exists)."""
    scope = territory_scope_filter(Douar.commune_id, db, user)
    douar = db.query(Douar).filter(Douar.id == douar_id, scope).first()
    if douar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=t("errors.not_found", lang)
        )
    return douar


@router.post("", response_model=DouarOut, status_code=status.HTTP_201_CREATED)
def create_douar(
    body: DouarCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_write),
) -> DouarOut:
    lang = get_request_language(request)
    douar = Douar(
        name_ar=body.name_ar,
        name_fr=body.name_fr,
        commune_id=body.commune_id,
        location=point_from_latlon(body.lat, body.lon),
        population=body.population,
        families_count=body.families_count,
        notes=body.notes,
    )
    db.add(douar)
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
        entity_type="douar",
        entity_id=douar.id,
        new_value={"name_fr": douar.name_fr, "commune_id": str(douar.commune_id)},
    )
    db.commit()
    db.refresh(douar)
    return _to_out(douar)


@router.get("", response_model=DouarListOut)
def list_douars(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DouarListOut:
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    query = db.query(Douar).filter(scope)
    if search:
        like = f"%{search}%"
        query = query.filter((Douar.name_ar.ilike(like)) | (Douar.name_fr.ilike(like)))

    total = query.with_entities(func.count(Douar.id)).scalar()
    items = (
        query.order_by(Douar.name_fr).offset((page - 1) * page_size).limit(page_size).all()
    )
    return DouarListOut(
        items=[_to_out(d) for d in items], total=total, page=page, page_size=page_size
    )


@router.get("/{douar_id}", response_model=DouarOut)
def get_douar(
    douar_id,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
) -> DouarOut:
    douar = _get_douar_or_404(db, douar_id, current_user, get_request_language(request))
    return _to_out(douar)


@router.patch("/{douar_id}", response_model=DouarOut)
def update_douar(
    douar_id,
    body: DouarUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_write),
) -> DouarOut:
    lang = get_request_language(request)
    douar = _get_douar_or_404(db, douar_id, current_user, lang)

    old_value = {"name_ar": douar.name_ar, "name_fr": douar.name_fr}
    updates = body.model_dump(exclude_unset=True)
    lat = updates.pop("lat", None)
    lon = updates.pop("lon", None)
    for field, value in updates.items():
        setattr(douar, field, value)
    if lat is not None or lon is not None:
        current = latlon_from_point(douar.location)
        new_lat = lat if lat is not None else (current[0] if current else None)
        new_lon = lon if lon is not None else (current[1] if current else None)
        if new_lat is not None and new_lon is not None:
            douar.location = point_from_latlon(new_lat, new_lon)

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
        action=AuditAction.UPDATE,
        entity_type="douar",
        entity_id=douar.id,
        old_value=old_value,
        new_value={"name_ar": douar.name_ar, "name_fr": douar.name_fr},
    )
    db.commit()
    db.refresh(douar)
    return _to_out(douar)
