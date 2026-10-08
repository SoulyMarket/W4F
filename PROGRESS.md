# W4F — Progress

Tracks what's built, decisions made, and what's deferred. See `W4F_BUILD_PLAN.md`
for the full spec and section 9 for the build order this follows.

## Environment notes (read this first if resuming)

- **Docker Desktop cannot run on this dev machine** — it reports
  "Virtualization support not detected" and fails to start even after a
  reboot. This looks like the host itself lacks nested virtualization
  rather than a settings issue I can fix from here.
  **Decision:** build and test against natively-installed Python 3.12,
  PostgreSQL 16, and (later) a native MinIO binary instead of
  `docker compose up`. The committed `docker-compose.yml` / `Dockerfile`
  still target Docker for any environment where it works (CI, another
  machine) — they're not being abandoned, just not exercised locally here.
- **PostGIS is not yet installed** on the native PostgreSQL 16 instance.
  I won't download/run a PostGIS installer myself outside of a vetted
  package manager (winget has no PostGIS package). The official path is
  Stack Builder, already installed at
  `Start Menu → PostgreSQL 16 → Application Stack Builder` — pick
  "PostGIS Bundle" for PostgreSQL 16 x64. Until that's done, any test
  that needs `geography` columns or spatial queries is blocked locally
  (code is still written correctly against the spec).
- **Postgres credentials**: the winget silent install set a random,
  unknown `postgres` superuser password, and I won't weaken local auth
  (pg_hba.conf) myself — that's a system/security-settings change my
  own operating rules keep off-limits even with blanket permission.
  A one-time PowerShell snippet to set known dev credentials (`w4f` /
  `devpassword123`, databases `w4f` and `w4f_test`) was handed to the
  user to run themselves. `.env` (once created, git-ignored) will use
  those credentials.

## Decisions / rulings

- Pure, DB-independent pieces were built ahead of their place in the
  section-9 order because they have no dependency on the scaffold being
  runnable end-to-end: the i18n helper (needed everywhere) and the
  priority scoring engine (`services/scoring.py`, section 7 — a pure
  function with no ORM/DB dependency). Both are fully unit-tested now.
  DB-backed steps resume in strict section-9 order once Postgres
  credentials are available.
- `services/scoring.py` breakdown always includes exactly 7 entries (one
  per criterion) plus an optional 8th `expert_confirmation` informational
  entry (0 points) when a validation exists — matches section 7's "one
  entry per criterion" plus the `priority.expert_confirmed` example row.
- Added two i18n keys beyond the plan's example table, needed for the
  zero-point / negative-state sides of binary criteria:
  `priority.has_alternative` (alternative source exists → 0 pts for that
  criterion), `priority.distance_no_alternative` (no alternative source →
  full distance points, nothing to measure), `priority.no_quality_risk`.
- PostgreSQL 16 was installed via winget (`PostgreSQL.PostgreSQL.16`) —
  matches the plan's stack choice exactly, just installed natively
  instead of via the `postgis/postgis:16` Docker image.

## Step status (Phase 1 — Backend)

- [ ] 1.1 Scaffold — in progress: repo layout, `pyproject.toml`,
      `docker-compose.yml`, `.env.example`, `Dockerfile`, i18n helper +
      `ar.json`/`fr.json` + key-parity test done. `/health` endpoint and
      README still to do; `docker compose up` can't be verified locally
      (see environment notes) — will verify `GET /api/v1/health` against
      the native Postgres instead once credentials are set.
- [ ] 1.2 Database — not started (blocked on Postgres credentials + PostGIS
      for the `geography` columns).
- [ ] 1.3 Auth — not started.
- [ ] 1.4 RBAC, territory scope, audit — not started.
- [ ] 1.5 Admin endpoints — not started.
- [ ] 1.6 Douars and reports (read side) — not started.
- [x] 1.7 Scoring — `compute_priority` implemented as a pure function in
      `backend/app/services/scoring.py`, 29 unit tests covering every
      criterion, edge cases (zero people, no alternative source, expert
      override), custom weights, and breakdown sorting. Config
      endpoints + recompute-on-change still need 1.2's DB models.
- [ ] 1.8 Expert validation — not started.
- [ ] 1.9 Projects — not started.
- [ ] 1.10 Dashboard + map + media + notifications — not started.

Phase 2 (Android), Phase 3 (Web), Phase 4 (AI) — not started.
