from collections.abc import Callable

import jwt
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    return Settings()


def get_request_language(request: Request) -> str:
    header = request.headers.get("accept-language", "")
    primary = header.split(",")[0].strip().split("-")[0].lower()
    return primary if primary in ("ar", "fr") else "ar"


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    lang = get_request_language(request)
    if credentials is None:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            key="errors.unauthorized",
            lang=lang,
        )
    try:
        payload = decode_access_token(credentials.credentials, settings.jwt_secret)
    except jwt.InvalidTokenError:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            key="errors.unauthorized",
            lang=lang,
        ) from None

    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            key="errors.unauthorized",
            lang=lang,
        )
    return user


#: Every role — used by routes that require *some* authenticated user but
#: don't restrict by role (e.g. /auth/me). Declaring this explicitly rather
#: than depending on bare get_current_user keeps the route-coverage test
#: (section 6.4) simple: every route either declares required roles via
#: require_roles(...), or is on the hand-checked exemption list
#: (login/refresh/health).
ALL_ROLES: tuple[UserRole, ...] = tuple(UserRole)


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """Dependency factory: raises 403 unless the current user's role is one
    of `roles`. Every route except login/refresh/health must declare this
    explicitly (section 6.4) — enforced by a route-coverage test."""

    def dependency(request: Request, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            lang = get_request_language(request)
            raise ApiError(
                status_code=status.HTTP_403_FORBIDDEN,
                key="errors.forbidden",
                lang=lang,
            )
        return current_user

    dependency.__w4f_required_roles__ = roles
    return dependency
