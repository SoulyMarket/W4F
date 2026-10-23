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

## Web dashboard

Needs the backend running (see above) — the dev server's default
`VITE_API_BASE_URL` points at `http://localhost:8000/api/v1`, and the
backend's default `CORS_ORIGINS` already allows `http://localhost:5173`.

```bash
cd web
npm install
npm run dev
```

Demo accounts (seeded by `python -m app.seed`), all with password
`DemoPass1234`: `admin@w4f.ma`, `manager@w4f.ma`, `expert@w4f.ma`. The
fourth seeded role, `moqaddem@w4f.ma`, is Android-only — the web app shows
it a notice instead of a dashboard (section 1: moqaddem "uses the Android
app only").

## Tests

```bash
cd backend
pytest

cd web
npm test
```

Backend tests that touch the database use `TEST_DATABASE_URL` from `.env`
and roll back each test in a transaction — no fixtures are left behind.

## Repository layout

See section 3 of `W4F_BUILD_PLAN.md`. Short version: `backend/` (FastAPI,
Phase 1), `android/` (Phase 2), `web/` (Phase 3).
