import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.i18n import t
from app.models.enums import AuditAction, UserRole
from app.models.refresh_token import RefreshToken
from app.models.territory import UserTerritory
from app.models.user import User
from app.schemas.users import (
    ResetPasswordResponse,
    UserCreate,
    UserListOut,
    UserOut,
    UserTerritoriesUpdate,
    UserUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/users", tags=["users"])

_require_admin = require_roles(UserRole.ADMIN)


def _get_user_or_404(db: Session, user_id, lang: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=t("errors.not_found", lang)
        )
    return user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> User:
    lang = get_request_language(request)
    user = User(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(body.password),
        role=body.role,
        preferred_language=body.preferred_language,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=t("errors.validation_error", lang)
        ) from None

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.CREATE,
        entity_type="user",
        entity_id=user.id,
        new_value={"email": user.email, "role": user.role.value, "full_name": user.full_name},
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=UserListOut)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> UserListOut:
    total = db.query(func.count(User.id)).scalar()
    items = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return UserListOut(
        items=[UserOut.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> User:
    return _get_user_or_404(db, user_id, get_request_language(request))


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id,
    body: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> User:
    lang = get_request_language(request)
    user = _get_user_or_404(db, user_id, lang)

    old_value = {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.value,
        "preferred_language": user.preferred_language.value,
    }

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=t("errors.validation_error", lang)
        ) from None

    new_value = {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.value,
        "preferred_language": user.preferred_language.value,
    }
    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="user",
        entity_id=user.id,
        old_value=old_value,
        new_value=new_value,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> User:
    lang = get_request_language(request)
    user = _get_user_or_404(db, user_id, lang)

    was_active = user.is_active
    user.is_active = False
    db.flush()

    now_revoked = (
        db.query(RefreshToken)
        .filter_by(user_id=user.id)
        .filter(RefreshToken.revoked_at.is_(None))
        .all()
    )
    for row in now_revoked:
        row.revoked_at = datetime.now(UTC)

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="user",
        entity_id=user.id,
        old_value={"is_active": was_active},
        new_value={"is_active": False},
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    user_id,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> ResetPasswordResponse:
    lang = get_request_language(request)
    user = _get_user_or_404(db, user_id, lang)

    temporary_password = secrets.token_urlsafe(12)
    user.password_hash = hash_password(temporary_password)
    db.flush()

    active_tokens = (
        db.query(RefreshToken)
        .filter_by(user_id=user.id)
        .filter(RefreshToken.revoked_at.is_(None))
        .all()
    )
    for row in active_tokens:
        row.revoked_at = datetime.now(UTC)

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="user",
        entity_id=user.id,
        new_value={"field": "password", "reason": "admin_reset"},
    )
    db.commit()
    return ResetPasswordResponse(temporary_password=temporary_password)


@router.put("/{user_id}/territories")
def set_user_territories(
    user_id,
    body: UserTerritoriesUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> dict[str, bool]:
    lang = get_request_language(request)
    user = _get_user_or_404(db, user_id, lang)

    old_ids = sorted(
        str(row.territory_id)
        for row in db.query(UserTerritory).filter_by(user_id=user.id).all()
    )
    db.query(UserTerritory).filter_by(user_id=user.id).delete()
    for territory_id in body.territory_ids:
        db.add(UserTerritory(user_id=user.id, territory_id=territory_id))
    db.flush()

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="user_territories",
        entity_id=user.id,
        old_value={"territory_ids": old_ids},
        new_value={"territory_ids": sorted(str(t) for t in body.territory_ids)},
    )
    db.commit()
    return {"ok": True}
