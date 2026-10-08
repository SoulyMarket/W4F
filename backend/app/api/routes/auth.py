import ipaddress
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import ALL_ROLES, get_request_language, get_settings, require_roles
from app.core.config import Settings
from app.core.rate_limit import login_ip_rate_limiter
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.i18n import t
from app.models.enums import AuditAction, UserRole
from app.models.refresh_token import RefreshToken
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    TerritorySummary,
    TokenPair,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])

_FAILED_LOGIN_LOCK_THRESHOLD = 5
_FAILED_LOGIN_LOCK_MINUTES = 15


def _client_ip(request: Request) -> str | None:
    """The `inet` audit/rate-limit columns reject anything that isn't a real
    address — notably Starlette's TestClient, which reports the host as the
    literal string "testclient" rather than an IP."""
    if not request.client:
        return None
    try:
        ipaddress.ip_address(request.client.host)
    except ValueError:
        return None
    return request.client.host


def _issue_token_pair(
    db: Session, user: User, settings: Settings, *, family_id: uuid.UUID | None = None
) -> TokenPair:
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        secret=settings.jwt_secret,
        expire_minutes=settings.access_token_expire_minutes,
    )
    refresh_days = (
        settings.refresh_token_expire_days_moqaddem
        if user.role == UserRole.MOQADDEM
        else settings.refresh_token_expire_days_other
    )
    refresh_token = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            family_id=family_id or uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=refresh_days),
        )
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenPair)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    lang = get_request_language(request)
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    if ip and login_ip_rate_limiter.is_blocked(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=t("errors.account_locked", lang, minutes=_FAILED_LOGIN_LOCK_MINUTES),
        )

    user = db.query(User).filter_by(email=body.email).one_or_none()

    def reject_invalid_credentials() -> None:
        if ip:
            login_ip_rate_limiter.hit(ip)
        write_audit_log(
            db,
            actor_id=user.id if user else None,
            action=AuditAction.LOGIN_FAILED,
            entity_type="user",
            entity_id=user.id if user else None,
            new_value={"email": body.email},
            ip=ip,
            user_agent=user_agent,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.invalid_credentials", lang),
        )

    if user is None:
        reject_invalid_credentials()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=t("errors.account_inactive", lang)
        )

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.account_locked", lang, minutes=_FAILED_LOGIN_LOCK_MINUTES),
        )

    if not verify_password(body.password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= _FAILED_LOGIN_LOCK_THRESHOLD:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=_FAILED_LOGIN_LOCK_MINUTES)
        db.flush()
        reject_invalid_credentials()

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(UTC)
    db.flush()

    tokens = _issue_token_pair(db, user, settings)
    write_audit_log(
        db,
        actor_id=user.id,
        action=AuditAction.LOGIN,
        entity_type="user",
        entity_id=user.id,
        ip=ip,
        user_agent=user_agent,
    )
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(
    body: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    lang = get_request_language(request)
    token_hash = hash_refresh_token(body.refresh_token)
    row = db.query(RefreshToken).filter_by(token_hash=token_hash).one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.refresh_token_invalid", lang),
        )

    if row.revoked_at is not None:
        # Reuse of an already-rotated token: revoke the whole family.
        family_rows = db.query(RefreshToken).filter_by(family_id=row.family_id).all()
        now = datetime.now(UTC)
        for member in family_rows:
            if member.revoked_at is None:
                member.revoked_at = now
        write_audit_log(
            db,
            actor_id=row.user_id,
            action=AuditAction.UPDATE,
            entity_type="refresh_token_family",
            entity_id=row.family_id,
            new_value={"reason": "reuse_detected"},
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.refresh_token_reused", lang),
        )

    if row.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.refresh_token_invalid", lang),
        )

    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.refresh_token_invalid", lang),
        )

    tokens = _issue_token_pair(db, user, settings, family_id=row.family_id)
    db.flush()
    new_row = (
        db.query(RefreshToken)
        .filter_by(token_hash=hash_refresh_token(tokens.refresh_token))
        .one()
    )
    row.revoked_at = datetime.now(UTC)
    row.replaced_by = new_row.id
    db.commit()
    return tokens


@router.post("/logout")
def logout(
    body: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> dict[str, bool]:
    token_hash = hash_refresh_token(body.refresh_token)
    row = (
        db.query(RefreshToken)
        .filter_by(token_hash=token_hash, user_id=current_user.id)
        .one_or_none()
    )
    if row and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.LOGOUT,
        entity_type="user",
        entity_id=current_user.id,
    )
    db.commit()
    return {"ok": True}


@router.post("/logout-all")
def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> dict[str, bool]:
    now = datetime.now(UTC)
    rows = (
        db.query(RefreshToken)
        .filter_by(user_id=current_user.id)
        .filter(RefreshToken.revoked_at.is_(None))
        .all()
    )
    for row in rows:
        row.revoked_at = now
    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.LOGOUT,
        entity_type="user",
        entity_id=current_user.id,
        new_value={"scope": "all_sessions"},
    )
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> MeResponse:
    territories = (
        db.query(Territory)
        .join(UserTerritory, UserTerritory.territory_id == Territory.id)
        .filter(UserTerritory.user_id == current_user.id)
        .all()
    )
    return MeResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        preferred_language=current_user.preferred_language,
        territories=[TerritorySummary.model_validate(t_) for t_ in territories],
    )


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> dict[str, bool]:
    lang = get_request_language(request)
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.invalid_credentials", lang),
        )
    current_user.password_hash = hash_password(body.new_password)
    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="user",
        entity_id=current_user.id,
        new_value={"field": "password"},
    )
    db.commit()
    return {"ok": True}
