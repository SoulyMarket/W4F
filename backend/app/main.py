from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    audit,
    auth,
    dashboard,
    douars,
    health,
    media,
    notifications,
    projects,
    reports,
    scoring,
    sync,
    territories,
    users,
    validations,
)
from app.core.config import Settings
from app.core.errors import ApiError, api_error_handler

settings = Settings()

app = FastAPI(
    title="W4F API",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

app.add_exception_handler(ApiError, api_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_store_cache_headers(request: Request, call_next):
    """Every route here is per-user/territory-scoped (section 6's "least
    privilege" rule) and none of them send a `Vary` header covering
    `Authorization` — found live: a browser that cached one user's GET
    response by URL alone (the only thing an HTTP cache keys on by
    default; it never varies by Authorization unless told to) served
    that same cached body back to a *different* signed-in user who later
    requested the identical URL with different credentials. Confirmed
    with `curl -D -` against this API: no `Cache-Control` header at all,
    meaning browsers apply their own heuristic caching. `no-store` on
    every response is the correct fix here, not a per-endpoint one —
    nothing this API returns is ever safe to cache across sessions."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(territories.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(douars.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(scoring.router, prefix="/api/v1")
app.include_router(validations.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
