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
- **PostGIS**: installed via Application Stack Builder (PostGIS 3.6.2) —
  **done**. One extra step was needed afterward: the `w4f` role doesn't
  have `CREATE EXTENSION` privilege (expected — it's not a superuser),
  so `CREATE EXTENSION postgis` had to run once per database as the
  `postgres` superuser before `alembic upgrade head` could proceed; after
  that, `w4f` uses postgis freely with no special privileges needed.
  Both `w4f` and `w4f_test` are now fully migrated (all 3 revisions) and
  verified — see the ruling below about the GIST-index double-creation
  bug this surfaced.
- **Postgres credentials**: the winget silent install set a random,
  unknown `postgres` superuser password, and I won't weaken local auth
  (pg_hba.conf) myself — that's a system/security-settings change my
  own operating rules keep off-limits even with blanket permission.
  The user ran a one-time PowerShell snippet to set known dev
  credentials (`w4f` / `devpassword123`, databases `w4f` and
  `w4f_test`) and restore secure auth afterward — **done**, confirmed
  reachable. `.env` at the repo root (git-ignored) uses these
  credentials; `backend/app/core/config.py` looks for it at `.env` or
  `../.env` so it's found whether you run tools from the repo root or
  from `backend/`.

## Decisions / rulings

- **GeoAlchemy2 double-creates spatial indexes if you also create them
  manually.** The postgis migration's `op.add_column(douars, Column(
  "location", Geography(...)))` kept failing with
  `relation "idx_douars_location" already exists` — but only through
  Alembic/SQLAlchemy; the identical raw SQL run directly via `psql`
  worked with no error. Root cause: `Geography(...)` defaults to
  `spatial_index=True`, and GeoAlchemy2's Alembic integration hooks
  `op.add_column`/`op.drop_column` to automatically create/drop the GIST
  index itself — my migration's explicit `op.create_index(...)` right
  after was racing that same automatic creation. Fixed by deleting the
  manual `op.create_index`/`op.drop_index` calls entirely and trusting
  GeoAlchemy2 to manage the index — confirmed afterward via `\d douars`
  that `idx_douars_location` exists correctly as a GIST index. Found by
  isolating the exact same SQL outside the ORM/migration layer (worked
  fine), which pointed straight at something ORM-side doing extra work
  rather than a real Postgres-level naming collision.
- The `w4f` database role needs `CREATE EXTENSION` run once per database
  by a superuser (`postgres`) before `alembic upgrade head` can proceed
  past the postgis migration — a non-superuser app role can use postgis
  freely afterward, it just can't install the extension itself. This is
  normal Postgres behavior, not a W4F-specific workaround; noted here
  only because `docker-compose.yml`'s `postgis/postgis` image handles
  this automatically on container init (that image's entrypoint already
  runs `CREATE EXTENSION` as its own superuser), so this manual step is
  purely an artifact of the native-Postgres dev setup, not something a
  Docker-based deployment needs to replicate.
- FastAPI resolved to version 0.143.0 (pinned only `>=0.115` in
  `pyproject.toml`), which turned out to have substantially reworked
  routing internals: `app.routes` no longer holds a flat list of
  `APIRoute` — an included router shows up as an internal `_IncludedRouter`
  wrapper one level up, and `APIRoute.path` doesn't include the router's
  `prefix` (that's resolved via `app.url_path_for(name)` instead). Found
  by actually inspecting `app.routes` at a Python prompt while writing the
  route-coverage test, not from documentation. `tests/test_route_coverage.
  py`'s `_iter_api_routes()` walks recursively and handles both shapes so
  it isn't quietly broken by the next FastAPI release either.
- `logout`, `logout-all`, `me`, and `change-password` were switched from a
  bare `Depends(get_current_user)` to `Depends(require_roles(*ALL_ROLES))`
  so the route-coverage test's exemption list stays exactly
  {health, login, refresh} per the plan's own wording in step 1.3's
  security requirement — any route needing "some authenticated user,
  any role" declares that explicitly rather than being a second kind of
  implicit exemption the coverage test would need to special-case.

- **Regenerated the initial migration a second time** after finding that
  `users.locked_until`/`last_login_at` were missing `timezone=True` (caught
  by an actual test comparing a DB-round-tripped value against
  `datetime.now(UTC)` — `TypeError: can't compare offset-naive and
  offset-aware datetimes`). Rather than layering an `ALTER COLUMN`
  migration on top for a schema with zero real data, downgraded both
  databases to base and regenerated. That surfaced a second real bug:
  Alembic's autogenerated `downgrade()` drops tables but not the native
  Postgres enum types it implicitly created alongside them, leaving 15
  orphaned types that collided with the next `CREATE TYPE` on re-upgrade.
  Fixed by adding explicit `DROP TYPE IF EXISTS` calls at the end of
  `downgrade()` in `e7ddb5e5e606`'s replacement,
  `6fa4e9cbc1db_initial_schema.py` (same migration, new revision id since
  the old one was already referenced by migrations 2 and 3's
  `down_revision`).
- `tests/conftest.py`'s `client` fixture now overrides FastAPI's `get_db`
  dependency to yield the *same* session as the `db_session` fixture,
  bound with `join_transaction_mode="create_savepoint"`. Needed once route
  handlers started calling `db.commit()` themselves (every auth endpoint
  does): without `create_savepoint` mode, the first `commit()` inside a
  request would commit the outer test transaction for real, and the
  fixture's final `rollback()` would silently no-op — every test's rows
  would leak into the database permanently. Caught before it caused
  damage by reasoning through the SQLAlchemy "joining a session to an
  external transaction" docs while writing the fixture, not by observing
  a leak.
- `request.client.host` is the literal string `"testclient"` under
  FastAPI's `TestClient`, which the `inet` audit/rate-limit columns
  reject outright. `_client_ip()` in `app/api/routes/auth.py` validates
  with `ipaddress.ip_address()` and treats anything that doesn't parse as
  no IP rather than erroring — found by running the auth tests, not
  anticipated in advance.

- **Split the data model into two Alembic migrations** rather than one, to
  unblock real (not just written-but-unverified) testing while PostGIS is
  unavailable locally: `e7ddb5e5e606_initial_schema` creates everything
  except two columns; `2b1e9c52e97c_add_postgis_geography_columns`
  (depends on `e7ddb5e5e606`) enables the postgis extension and adds
  `douars.location` / `reports.location` plus their GIST indexes.
  Verified: the first migration applies cleanly and all 16 tables exist
  with correct enum labels; the second fails with exactly the expected
  "extension postgis is not available" error and nothing else. Caveat
  found while testing: this split helps less than hoped — the ORM model
  always includes `location` in `INSERT`s (even as `NULL`), so creating
  *any* `Douar` or `Report` row still fails until the second migration
  runs. Auth/RBAC/admin/scoring-config/notifications/refresh-tokens are
  fully testable now; anything touching douars or reports is not.
- Found and fixed a real bug this split surfaced: `sa.Enum(SomeStrEnum,
  name=...)` by default uses the Python enum **member names** as the
  Postgres enum labels, not the `StrEnum` **values** — so `Language` was
  about to create a `language` type with labels `AR`/`FR` while the code
  everywhere else uses lowercase `ar`/`fr`, breaking every
  `server_default` and equality check. Fixed via `values_callable` on a
  shared `SAEnum(...)` instance per type in `app/models/enums.py`
  (`app/models/enums.py:140` on). Caught by actually running the
  migration, not by reading the code — another point for not skipping
  execution even on the DB-independent-feeling parts.
- Every native Postgres enum type is declared **exactly once**, as a
  module-level `SAEnum(...)` in `app/models/enums.py`, and imported by
  every model that uses it (`severity_level` is used by both
  `reports.severity_reported` and `validations.urgency_opinion`).
  Declaring `Enum(X, name=...)` separately in two model files for the
  same type name is a correctness trap even though — found while
  building this — Alembic's per-table `checkfirst` during `CREATE TABLE`
  happens to make it *work*; the shared instance is still used everywhere
  since relying on that checkfirst behavior wasn't the intent.
- `reports.id` has **no** server-side default (unlike every other table's
  UUID PK) — generated client-side on the phone, per section 4, so the
  offline sync push can be idempotent on that same id.
- Added a `project_media` table, following the plan's "+ optional media
  via a `report_media`-like table `project_media`" note in section 4
  under `project_updates` — not separately itemized in the table list,
  but explicitly called for in prose.
- `audit_log` append-only (section 6.6) is enforced with a
  `BEFORE UPDATE OR DELETE` trigger that raises on any attempt
  (migration `e4ebb09017d4`), not a bare `REVOKE`: a `REVOKE` only
  constrains one specific DB role, which isn't defined anywhere in this
  schema yet and would be bypassed by whichever role a given deployment
  actually connects as (including a superuser running routine DML by
  mistake). The trigger applies unconditionally to anyone touching the
  table.

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

- [x] 1.1 Scaffold — repo layout, `pyproject.toml`, `docker-compose.yml`,
      `.env.example`, `Dockerfile`, i18n helper + `ar.json`/`fr.json` +
      key-parity test, `/health` endpoint (checks DB connectivity via a
      real `SELECT 1`), README. `docker compose up` itself can't be
      verified locally (see environment notes above) — verified instead
      with `GET /api/v1/health` against the native Postgres 16 instance,
      which is the equivalent check `docker compose`'s healthcheck would
      run. `app/core/security.py` (password hashing, JWT, refresh
      tokens) also done here, ahead of 1.3, since it's pure logic needed
      by several later steps and has no DB dependency.
- [x] 1.2 Database — all 16 tables from section 4 (incl. `project_media`)
      as typed SQLAlchemy 2.x models in `backend/app/models/`; all 3
      migrations applied cleanly to both `w4f` and `w4f_test`
      (`alembic upgrade head` — initial schema, postgis geography
      columns, audit_log append-only trigger). `backend/app/seed.py` run
      twice against the real dev database: 4 territories (1 province +
      3 communes), 10 douars, 4 users (one per role), 15 reports, 1
      active scoring_config — identical counts both times, confirming
      idempotency per the plan's own acceptance criterion. 7 model tests
      pass, 0 skipped.
- [x] 1.3 Auth — `POST /auth/login` (lockout after 5 failures, 15 min;
      per-IP rate limiting via `app/core/rate_limit.py`, an in-memory
      limiter — documented there as needing a shared store like Redis for
      a multi-worker/multi-instance deployment), `POST /auth/refresh`
      (rotation + reuse-detection revokes the whole token family),
      `POST /auth/logout`, `POST /auth/logout-all`, `GET /auth/me`,
      `POST /auth/change-password`. 24 tests (18 endpoint + 6 rate-limiter
      unit tests), all passing against the real Postgres instance.
      Login/login_failed/logout both write to `audit_log` via the new
      `app/services/audit.py` helper (the full audit write-path lands
      properly in 1.4, but login needed it now for the "wrong password
      locks the account" acceptance test).
- [x] 1.4 RBAC, territory scope, audit — `require_roles(...)` (deps.py)
      used by every route; a route-coverage test walks the full FastAPI
      route tree (including a meta-test that proves the detection logic
      itself actually flags an unguarded synthetic route, not just that
      it passes vacuously) and fails on anything not using
      `require_roles` except the hand-reviewed exemption list
      (health/login/refresh). `app/services/territory_scope.py`:
      `get_accessible_territory_ids()` resolves a user's assigned
      territories plus all descendants ("a province assignment sees its
      communes"); a user with zero assignments gets an empty set, not
      everything — least privilege is the default. Fully tested (4
      tests: no assignment, direct commune, province-sees-communes,
      multiple assignments unioned) since this only touches
      territories/user_territories, not douars/reports. `write_audit_log`
      (built in 1.3) is the single audit writer everything uses.
      **Deferred to 1.6**: the plan's own acceptance criterion "a
      moqaddem/expert from territory A gets 404 on territory B
      resources" needs an actual territory-bound resource to test against
      (douars/reports) — there's nothing to scope yet. Also deferred:
      a full create/update/delete example demonstrating `old_value`/
      `new_value` capture — audit so far only has login/logout/
      change-password, which don't have a real "before" state to diff;
      1.5's user CRUD is the first natural place for that.
- [x] 1.5 Admin endpoints — `POST/GET /users`, `GET/PATCH /users/{id}`,
      `POST /users/{id}/deactivate` (also revokes all their refresh
      tokens — a deactivated account shouldn't keep a live session),
      `POST /users/{id}/reset-password` (generates a random temporary
      password server-side and returns it once, rather than letting the
      admin choose/know the user's real password — also revokes active
      sessions), `PUT /users/{id}/territories` (full replace, not merge),
      `GET/POST /territories`, `PATCH /territories/{id}`, `GET /audit`
      (filters: actor_id, entity_type, action, date_from/date_to;
      paginated). All admin-only. 22 new tests, all passing first try
      against the real Postgres instance — including the `old_value`/
      `new_value` audit example deferred from 1.4 (user update, user
      deactivate, user territory reassignment all now have one).
      113 tests total, 1 skipped (still the PostGIS-blocked report test).
- [x] 1.6 Douars and reports (read side) — `POST/GET /douars`,
      `GET/PATCH /douars/{id}` (admin/manager write, all 4 roles read,
      territory-scoped; cross-territory access returns 404 not 403, per
      section 6.5); `GET /reports` (filters: status, douar/commune/
      province, score range, date range, `sort_by_score`) and
      `GET /reports/{id}` (with media, latest priority breakdown,
      validation history). `app/core/geo.py` (lat/lon ↔ geography(Point)
      conversions), `shapely` added as an explicit dependency.
      `get_descendant_ids()` extracted from `territory_scope.py` so the
      `province_id` report filter resolves "all communes under this
      province" the same way user access resolution does. All 9 tests
      (4 douars, 5 reports) pass against the real Postgres+PostGIS
      instance on the first run once the migration applied. Also
      smoke-tested live: started `uvicorn`, logged in as the seeded
      manager, hit `/auth/me`, `/douars`, `/reports` over real HTTP —
      territory scoping and lat/lon round-tripping both correct against
      actually-seeded data (e.g. Ait Ourir douar returned exactly its
      seeded 31.355/-7.667 coordinates).
- [x] 1.7 Scoring — `compute_priority` (pure function, 29 unit tests) now
      fully wired to the database. `app/services/priority.py`: builds
      `ReportForScoring`/`ValidationForScoring` from a persisted
      Report (+ its latest Validation's `urgency_opinion`, if any),
      persists the result as a new `Priority` row, and
      `recompute_all_open_reports()` does this for every report not in a
      terminal status (`rejected`/`converted_to_project`) when the
      active config changes. `GET/PUT /scoring-config` (manager-only
      write; `PUT` deactivates the old config, creates a new active one,
      recomputes, and returns `reports_recomputed`), `GET
      /reports/{id}/priority` (score + explanation, 404 if nothing
      computed yet). Section 2.1 explicitly lists "priority reasons"
      among the things the API must localize via `Accept-Language` —
      added a `reason` field (rendered through `app.i18n.t()`) to every
      breakdown entry in both this endpoint and the embedded priority in
      `GET /reports/{id}`, alongside the raw `reason_key`/`reason_params`
      (kept for clients that want to localize themselves). 11 new tests
      (5 service-level, 6 endpoint-level), all passing. 134 tests total.
- [x] 1.8 Expert validation — `POST /reports/{id}/validations`
      (expert-only, territory-scoped — 404 outside scope). Decision →
      status mapping: `validated`/`modified` both move the report to
      `validated` (ruling: "modified" is still an approval, just one
      where the expert adjusted something, not a status of its own —
      there's no such report status to move to); `recheck_requested` →
      `recheck_requested`; `rejected` → `rejected`. 409 on an
      already-terminal report (`rejected`/`converted_to_project`).
      Writes a `status_change` audit row (old/new status), recomputes
      the report's priority immediately (the expert's `urgency_opinion`
      feeds `compute_priority` via 1.7's service), and notifies per
      section 5's trigger list: `recheck_requested` → moqaddem only;
      `validated` → moqaddem **and every manager** (ruling: section 5
      doesn't scope this to managers of the report's own territory, and
      building that territory-reverse-lookup wasn't worth it for a
      prototype at this scale — `notify_all_managers()` in
      `app/services/notifications.py` is a one-line change if that needs
      tightening later); `rejected` → no notification at all, since
      section 5's trigger list doesn't list one for it. 9 new tests, all
      passing. 143 tests total.
- [x] 1.9 Projects — `POST /reports/{id}/project` (manager-only,
      territory-scoped; 409 unless the report is `validated` — reuses
      the `errors.report_not_validated` i18n key defined back in step
      1.1, unused until now), `GET /projects` (territory-scoped, status
      filter), `GET /projects/{id}` (with update history), `PATCH
      /projects/{id}`, `POST /projects/{id}/updates` (status transitions
      gated by `PROJECT_STATUS_TRANSITIONS` from `app/models/enums.py`
      — written back in step 1.2, exercised for the first time here:
      409 on any transition not in that map, confirmed for both an
      invalid forward jump (`new`→`approved`, skipping `in_study`) and
      a terminal state (`completed`→anything)). Converting a report
      writes two audit rows (project `create`, report `status_change`
      to `converted_to_project`) and notifies moqaddem + all managers
      (`project_created`); a status-changing update notifies the same
      audience with `project_status_changed`, or `project_completed`
      specifically when the new status is `completed`. 9 new tests, all
      passing first try. 152 tests total.
- [ ] 1.10 Dashboard + map + media + notifications — not started.

Phase 2 (Android), Phase 3 (Web), Phase 4 (AI) — not started.
