from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    audit,
    auth,
    douars,
    health,
    projects,
    reports,
    scoring,
    territories,
    users,
    validations,
)
from app.core.config import Settings

settings = Settings()

app = FastAPI(
    title="W4F API",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
