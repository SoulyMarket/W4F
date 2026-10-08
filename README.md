# W4F

Platform for collecting, prioritizing, validating and tracking drinking-water
access problems in rural Moroccan douars.

See [`W4F_BUILD_PLAN.md`](W4F_BUILD_PLAN.md) for the full spec and
[`PROGRESS.md`](PROGRESS.md) for build status and decisions made along the way.

## Backend — run with Docker (recommended)

```bash
cp .env.example .env   # edit values if needed
docker compose up --build
```

API at `http://localhost:8000`, docs at `http://localhost:8000/docs` (dev only).
`GET /api/v1/health` checks DB connectivity.

## Backend — run natively (no Docker)

Needed if Docker/virtualization isn't available on your machine.

1. Install Python 3.12+, PostgreSQL 16 with the **PostGIS** extension, and
   MinIO (or any S3-compatible store).
2. Create a database and role, then copy `.env.example` to `.env` and fill
   in `DATABASE_URL` / `TEST_DATABASE_URL` to match.
3. From `backend/`:

   ```bash
   python -m venv .venv
   .venv/Scripts/activate        # Windows; use .venv/bin/activate on Unix
   pip install -e ".[dev]"
   alembic upgrade head
   python -m app.seed            # optional demo data
   uvicorn app.main:app --reload
   ```

## Tests

```bash
cd backend
pytest
```

Tests that touch the database use `TEST_DATABASE_URL` from `.env` and roll
back each test in a transaction — no fixtures are left behind.

## Repository layout

See section 3 of `W4F_BUILD_PLAN.md`. Short version: `backend/` (FastAPI,
Phase 1), `android/` (Phase 2), `web/` (Phase 3).
