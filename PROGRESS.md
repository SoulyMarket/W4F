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

## Step status (Phase 1 — Backend) — ALL STEPS COMPLETE (175 tests, 0 skipped)

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
- [x] 1.10 Dashboard + map + media + notifications — complete.
      `GET /dashboard/summary` and `GET
      /dashboard/map` (both manager-only — section 1 is the only role
      row that lists "dashboard and map"): totals, reports/projects by
      status, priority douars (latest score ≥ 70), recurring-problem
      douars (≥ 3 reports in the trailing 12 months), and a GeoJSON
      `FeatureCollection` with per-douar latest score/report count/
      latest project status. `app/services/dashboard.py` factors out
      "latest priority score per report" and "latest project status per
      douar" so both endpoints compute them identically rather than
      drifting. `GET /notifications` (own notifications only, paginated,
      `unread_count`, localized `message` via `app.i18n.t()`), `POST
      /notifications/{id}/read`, `POST /devices` (FCM token
      registration, upserts on a token already registered to someone
      else — a phone can change owners). Also closed a gap from 1.7/1.8:
      section 5 lists "priority changed by ≥ 10 points" as a
      notification trigger but — unlike every other trigger in that
      list — never names a recipient; ruled the same audience as
      validated/project triggers (moqaddem + all managers) and wired it
      directly into `recompute_priority()` so both call sites (manual
      validation, bulk config-change recompute) get it for free. 22 new
      tests (13 dashboard/notifications + 3 priority-change-notification
      + the rest from closing that gap), all passing. 168 tests total,
      then +7 media tests below.

      **Media**: `POST /media/upload-url` (validates mime/size per
      section 6.10's limits — jpeg/png/webp/mp4, 10 MB photo / 100 MB
      video cap — creates a `pending` `ReportMedia` row, returns a
      presigned PUT URL), `POST /media/{id}/complete` (verifies the
      object actually exists via `head_object`, that its size matches
      what was declared, and that its content's real SHA-256 matches
      what the client claims — downloads and hashes the object
      server-side to do this, since neither S3 nor MinIO exposes a
      SHA-256 natively; only then marks `uploaded`). `GET /reports/{id}`
      now returns a presigned `download_url` per media item instead of
      the raw `object_key`/bucket — section 6.10 is explicit that media
      only ever goes out as a short-lived presigned URL, never a public
      bucket or a raw key. MinIO's winget package (`MinIO.Server`)
      still fails — confirmed broken again on retry: its manifest points
      at a specific dated release archive on `dl.min.io` that MinIO has
      pruned (`410 Gone`), an upstream packaging issue I can't fix from
      here. Used `moto[server]` instead (a well-known PyPI testing
      library, installed via `pip` — a vetted channel, unlike downloading
      a `.exe` directly) to run a real local S3-compatible HTTP server
      for tests: `tests/conftest.py`'s `moto_s3_endpoint` fixture starts
      `python -m moto.server` on a free port and points the `MINIO_*` env
      vars at it before any `Settings()` is constructed, so
      `app/services/storage.py`'s boto3 client — the same one that talks
      to real MinIO in every other environment — needs zero test-specific
      code. Verified the *entire* real flow end-to-end, not just mocked
      pieces: presigned PUT URL generation → an actual HTTP PUT with real
      bytes → `head_object` → downloading and hashing the object →
      presigned GET URL → an actual HTTP GET that returns the exact
      bytes uploaded. 7 new tests, all passing. 175 tests total — **all
      of Phase 1 is now complete and verified.**

## Phase 2 — Android

### Environment setup

- **Android Studio** installed via winget (`Google.AndroidStudio`) — bundles
  a JBR (JetBrains Runtime) JDK 25 at
  `C:\Program Files\Android\Android Studio\jbr`, used as `JAVA_HOME` for all
  Gradle builds here instead of the system's old Java 8.
- **Android SDK**: no `sdkmanager` ships with a bare Android Studio install
  anymore (SDK components normally download via the first-run GUI wizard,
  which isn't an option headless). Found and installed `Google.AndroidCLI`
  via winget instead — an official Google-published CLI
  (`developer.android.com/tools/agents/android-cli`) explicitly built for
  agentic/headless Android development: SDK package management, project
  scaffolding, build/deploy, emulator control, and a bundled live Android
  documentation search (`android docs search`/`docs fetch`), which is what
  resolved the AGP 9 compatibility issues below instead of guessing version
  numbers. Installed via `android sdk install platform-tools
  "platforms;android-35" "build-tools;35.0.0"`. SDK root:
  `C:\Users\souly\AppData\Local\Android\Sdk`.
- **No emulator** — `systeminfo`/`Get-ComputerInfo` show `HyperVisorPresent:
  True`, the same nested-virtualization signature that blocked Docker (see
  Phase 1's environment notes): this machine is itself a VM. The Android
  emulator needs the same acceleration (WHPX/Hyper-V) Docker's backend
  needed, so it's assumed unavailable here without being separately
  re-confirmed (not worth the multi-GB system-image download just to watch
  it fail the same way). **Verification strategy for all of Phase 2
  accordingly: JVM-level unit tests (JUnit, Robolectric where Android
  framework classes are needed, Room's in-memory/Robolectric test support)
  rather than instrumented/emulator tests** — mirrors Phase 1's PostGIS
  workaround (verify everything possible locally, document what can't be).
- Scaffolded with `android create empty-activity --namespace=com.w4f.app
  --min-sdk=26 --output=./android` (only template available) — modern
  Compose setup (Kotlin 2.3.20, AGP 9.0.1, Navigation3, Gradle 9.1.0), then
  heavily extended.
- **AGP 9.0's "built-in Kotlin" broke both `kapt` and old Hilt outright** —
  found by actually trying to resolve dependencies, not foreseeable from
  the plan or from memory of older Android tooling:
  - Hilt 2.57 (a plausible "current" guess) failed with "Android
    BaseExtension not found" — `android docs search`/`docs fetch` turned up
    an AGP-9 plugin-compatibility doc stating Hilt needs **≥ 2.59** for
    AGP 9. Bumped it.
  - `org.jetbrains.kotlin.kapt` then failed outright: "not compatible with
    built-in Kotlin support" — AGP 9 removed the old `kotlin-android`
    plugin path kapt depended on. Google's own migration doc recommends
    moving to KSP rather than using the `legacy-kapt` compatibility shim,
    so that's what was done: **KSP 2.3.4** (the version Google's own
    current migration doc uses as its example) replaces kapt for Room's
    and Hilt's annotation processors (`ksp(...)` instead of `kapt(...)`).
  - Confirmed clean after both fixes: `:app:dependencies` resolves the full
    graph (Hilt, Room+SQLCipher, Retrofit+OkHttp+kotlinx.serialization,
    WorkManager, security-crypto, DataStore, CameraX, Play Services
    Location, MapLibre, Firebase BOM — the full stack section 2's Android
    column lists, added in one pass since they don't conflict with each
    other), and `:app:compileDebugKotlin` runs `kspDebugKotlin` then
    compiles successfully.

## Phase 1 correction (found while starting Phase 2)

Writing the Android app's error-handling DTOs against section 5's documented
error contract — `{"error": {"code": "...", "message": "..."}}` — surfaced
that the backend never actually implemented this envelope: every route used
`HTTPException(status_code=..., detail=t(key, lang))`, which FastAPI renders
as plain `{"detail": "<message>"}`, with no `code` field and no `error`
wrapper. All 175 Phase 1 tests were passing despite this because none of
them asserted on error *response bodies*, only status codes.

Fixed properly rather than patched around in the Android client:
`app/core/errors.py` adds `ApiError(HTTPException)` (carries `code` — derived
from the i18n key, since both are already stable English identifiers — and
the localized `message`) plus a registered exception handler that shapes the
envelope. Converted all 40 `raise HTTPException(...)` call sites across 11
files to `raise ApiError(...)` — 39 by a one-off regex migration script
(written, run, then deleted; had one real bug caught by testing it against
the actual failing case before trusting it — see below), 1 by hand (a
variable key rather than a literal). `ruff format` cleaned up indentation
left by the mechanical replacement.

The script's first pass only converted 19 of 40 call sites (missed
everywhere a trailing comma followed `t(...)`'s closing paren before the
outer `HTTPException(...)`'s own closing paren — a multi-line-formatting
case the first regex didn't account for). Found by counting replacements
per file against a prior `grep` count rather than assuming success, fixed,
re-ran cleanly.

Added `tests/test_error_envelope.py` (4 tests) to actually verify the
envelope shape, language fallback, and Accept-Language handling — the gap
a mechanical "all tests still pass" check would never have caught, since
nothing was asserting on error bodies before. 179 tests total.

### Step 2.2 — Android scaffold: login + auth, verified on-device

Built: Hilt DI (NetworkModule, RepositoryModule), Retrofit+OkHttp+kotlinx.
serialization network layer, EncryptedSharedPreferences-backed TokenStore,
AuthRepository, LoginViewModel/Screen, HomeViewModel/Screen (stub — full
dossier list is step 2.4), Navigation3-based nav (Login ⇄ Home), the
backend's error envelope parsed into a typed `ApiException`. 13 new JVM unit
tests (ViewModel + repository, including the real `HttpException`→
`ApiException` parsing path), plus the string-resource parity test from the
scaffold commit — all passing.

**Installed and ran on a real emulator** (user's MSI App Player/BlueStacks)
rather than stopping at "compiles" — this caught a bug no unit test would:
`MainActivity` was missing `@AndroidEntryPoint`, which compiles fine but
crashes at runtime the moment a Hilt-injected `hiltViewModel()` composable
tries to resolve (`IllegalStateException: ... does not implement
GeneratedComponent`). Fixed, reinstalled, confirmed via logcat
("Displayed com.w4f.app/.MainActivity", no crash) and a screenshot: the
login screen renders correctly — Arabic title, RTL field layout with the
text cursor on the right, the bundled Noto Sans Arabic font shaping
correctly, submit button correctly disabled/enabled based on field state.

Typed real credentials and tapped submit: the full request path executed
(button → ViewModel → repository → Retrofit → OkHttp) and failed with a
**real network error**, correctly caught and mapped to
`login_error_network`, displayed in Arabic in the error color — proving the
error-handling path works, not just the happy path. Root cause: the host's
network profile is "Public", so Windows Firewall blocks inbound TCP from
BlueStacks' virtual network to the backend's port 8000 by default — a
system/security setting, so a firewall rule was handed to the user to run
themselves (`New-NetFirewallRule -DisplayName "W4F Dev API" -Direction
Inbound -LocalPort 8000 -Protocol TCP -Action Allow`, as Administrator)
rather than attempted directly. **Not yet verified: an actual successful
login round-trip against the real backend** — next session should add the
firewall rule (or otherwise get connectivity) and confirm that before
moving on to step 2.3.

MSI App Player also needed "Android Debug Bridge (ADB)" enabled in its own
settings before `adb` could do more than list the device (push/install/
shell all failed with connection errors until then) — noted here in case
reconnecting to the same emulator in a future session hits the same wall.

### Phase 1 gap found and fixed: step 2.1 (Sync API) had been skipped

Resuming after step 2.2, section 9's own order was re-checked against what
actually exists — and step **2.1 — Sync API** (`/sync/push`, `/sync/pull`,
FCM sender service) had never been built: work went straight from 1.10 to
the Android scaffold (2.2). Device-token registration (`POST /devices`)
*was* already done back in 1.10, so only the two sync endpoints and the
FCM sender were actually missing. Built now, out of its proper order but
before any more Android work, since step 2.4 (sync workers) depends on it
and there's no reason to let the gap compound further.

**`POST /sync/push`** (moqaddem-only) — the *only* way a report is ever
created; there is deliberately no `POST /reports` (`reports.id` is
client-generated specifically so this push can be idempotent, section 4).
Per report item: creates if the id is new (territory-checked: the douar
must be in the moqaddem's accessible set, else `rejected`/
`errors.not_found`, same 404-not-403 convention as everywhere else),
compares field-by-field if it already exists (`unchanged` if identical,
`updated` + `version += 1` + priority recompute if not), and enforces
section 5's conflict rule verbatim: once `status` has moved past
`submitted`, the push is `rejected` with `errors.sync_conflict` — "the
phone owns field data while submitted; server wins after review." A new
report immediately gets its first `Priority` (`recompute_priority`, reused
from 1.7/1.8) and triggers the `new_report` notification to **experts of
the report's territory** — a new `notify_territory_experts()` in
`app/services/notifications.py`, scoped via the same
`get_accessible_territory_ids()` every other territory check uses (an
expert is "of" a territory if it's in their accessible set, not just a
direct assignment — a province-assigned expert covers its communes' new
reports too, consistent with how province assignments work everywhere
else). This was also the first thing to ever actually trigger
`NotificationType.NEW_REPORT`, defined back in step 1.2 but unused until
now since there was no report-creation endpoint before this.

**Ruling: "+ media metadata" in the push body.** The spec's
`POST /sync/push — body: list of reports (with client UUIDs) + media
metadata` doesn't fully specify the shape. Rather than inventing a second,
client-id-keyed media table (which would need a migration, since
`report_media.id` has a server-only default), each pushed report carries an
optional `media: [{kind, mime_type, size_bytes, captured_at}]` list that
reuses the *exact* existing creation path from `/media/upload-url`
(server-generated id and `object_key`, presigned PUT URL returned
immediately) — just batched into the same call, since the client is
already batching everything else here. Idempotency for media (a
WorkManager retry resending the same push) is keyed on the natural tuple
`(report_id, kind, mime_type, size_bytes, captured_at)` rather than a
client id: a true retry resends the identical `captured_at`, so this still
dedupes correctly without a schema change. Verified: pushing the same
media metadata twice registers exactly one `report_media` row and returns
the same `media_id` both times.

**`GET /sync/pull?since=<cursor>`** (moqaddem-only) — `cursor` is an ISO
timestamp captured *before* any query runs (a row written mid-pull is
re-delivered next time rather than silently missed — harmless for a
read-only sync target, unlike a gap). Returns, filtered to the moqaddem's
own accessible territory/own reports: douars, reports (with latest score,
reusing the exact same latest-priority-per-report join `GET /reports`
already uses — promoted from `reports.py`'s private
`_latest_priority_subquery`/`_report_to_out` to public
`latest_priority_subquery`/`report_to_out` so both endpoints share one
implementation instead of two that could drift), priorities, validations,
projects, project updates, and notifications (reusing the same
`app.i18n`-localized message rendering `GET /notifications` uses). Omitting
`since` does a full first-sync snapshot.

**FCM sender** (`app/services/fcm.py`) — `send_push(settings, tokens,
title, body, data)`, a no-op (just logs) whenever
`settings.fcm_credentials_json` is empty, which is every environment this
has actually run in so far (no real Firebase project exists here). Built
on `firebase-admin` (added as a real dependency, not dev-only — pulls in
`google-cloud-*`/`grpcio` transitively, a genuinely heavy addition for a
path that can't be exercised against the real service in this environment
either way, but it's what section 2's stack names and hand-rolling FCM's
OAuth2 service-account flow instead would be more code and more fragile
than depending on the standard library for it). Uses `messaging.Message`
per-token + `send_each()` rather than the newer `MulticastMessage`/
`send_each_for_multicast` — those now push toward Firebase **Installation
IDs** (`fids`), a different identifier namespace than the classic FCM
registration tokens this schema actually stores
(`device_tokens.fcm_token`, section 4); `.token`/`send_each()` triggers a
cosmetic deprecation warning that's suppressed in `pyproject.toml` with a
comment explaining why, not fixed by switching to the wrong ID type.
Tested with the real `firebase_admin.messaging`/`credentials` call sites
mocked (constructing a real `credentials.Certificate` needs an actual
valid PEM key, which no test fixture has) — verifies the no-op fallback
needs no mocking at all, and the configured path calls the real API with a
correctly shaped message. **Deferred to step 2.5, not an oversight**: wiring
`send_push` into the existing notification triggers (`notify_user`/
`notify_all_managers`/`notify_territory_experts`) — the Android side has no
Firebase project/`google-services.json` yet either, so there's nothing to
receive a real push against until that step sets it up.

8 new tests (6 sync — create/idempotent-unchanged/update-bumps-version/
conflict-rejected/cross-territory-rejected/role-check, plus media
idempotency and pull scoping — call it 8 total across `test_sync.py`) + 4
FCM tests, all passing against the real Postgres instance (and a live
smoke test over real HTTP: logged in as the seeded moqaddem, pushed a new
report twice — `created` then `unchanged` — pulled it back with its score,
and confirmed the seeded expert actually received the `new_report`
notification). 191 tests total.

### Step 2.3 — Report form: Room schema, CameraX, GPS, local save

Built in two commits. **Environment note carried over from 2.2**: MSI App
Player wasn't running at the start of this step (likely closed by the
earlier PC restart) and hasn't come back up during it — everything below
is verified by JVM/Robolectric unit tests and `:app:assembleDebug`
succeeding, **not** by running on a device. On-device verification (and
the still-outstanding real login round-trip from 2.2) needs the user to
reopen MSI App Player next session.

**Part 1 — encrypted Room schema + repositories.** `Douar`/`Report`/
`ReportMedia` Room entities (`data/local/db/`) mirror the backend's own
shapes closely enough that step 2.4's sync workers can map 1:1 to/from
them. SQLCipher-encrypted (section 6.12/8: "Room over SQLCipher") via
`net.zetetic:sqlcipher-android`'s `SupportOpenHelperFactory` — note the
package is `net.zetetic.database.sqlcipher`, not the older
`net.sqlcipher.database` some docs/tutorials still reference, found by
inspecting the actual AAR's `classes.jar` the same way the Retrofit
converter package name was found in step 2.2. The passphrase lives in
Keystore-backed `EncryptedSharedPreferences` (`DatabasePassphraseStore`),
generated once on first run — mirrors `EncryptedTokenStore`'s pattern
exactly. `DouarRepository`/`ReportRepository` wrap the DAOs behind
interfaces (same Hilt `@Binds` pattern as `AuthRepository`); reads are
`Flow`-based so the UI recomposes automatically as Room changes, per
section 8's "Room is the single source of truth" rule.
**Robolectric needed `sdk=35` pinned explicitly** (`app/src/test/
resources/robolectric.properties`) — the app targets SDK 36, one version
ahead of what Robolectric 4.14.1 ships framework jars for; without it every
Robolectric test fails at the class-loading stage with "targetSdkVersion=36
> maxSdkVersion=35", not a problem with the test itself. 2 DAO test classes
(Room, in-memory, Robolectric — search scoping, Arabic/French name
matching, sync-state transitions).

**Part 2 — the "تبليغ جديد" stepper + CameraX + GPS.** Five steps exactly
as section 8 lists them (الدوار → المشكل → الأرقام → الإثباتات → ملخص), one
`NewReportViewModel` holding the whole draft so step-to-step navigation is
just an in-memory state change, not a save-and-reload. Per-step validation
gates "التالي" (e.g. step 2 needs all four chip selections); step 4
(evidence) never gates anything, per section 8's explicit "never block data
entry on network or GPS" rule — confirmed by a test that a failed/denied
GPS fix still leaves `canGoNext == true`.

- **الدوار**: searches the local Room cache only, scoped to the ids in the
  logged-in user's own `territories` from `/auth/me` — not resolved
  client-side into province→commune descendants the way the backend does
  (`get_accessible_territory_ids`); ruling: a moqaddem's own assignment is
  realistically always their one commune in practice, and building a
  client-side mirror of the backend's territory-tree walk wasn't worth it
  for a prototype. Before step 2.4's pull sync exists, this list is simply
  empty — expected, not a bug; the DAO test fixtures prove the query logic
  itself works once rows exist.
- **المشكل**: `FilterChip` groups for water source/problem type/frequency/
  severity + a switch for the water-quality-risk flag.
- **الأرقام**: numeric-keypad fields for families/people/duration-in-days,
  and an alternative-source switch gating a distance field. **Ruling**:
  section 8's field list for this step has no separate "date the problem
  started" picker, only duration — so `problem_started_on` (a required
  server field) is derived as `today − duration_days` at save time rather
  than adding a date-picker UI the screen spec doesn't call for.
- **الإثباتات**: real CameraX binding (`Preview` + `ImageCapture`, rebound
  to `Preview` + `VideoCapture`/`Recorder` when toggled to video mode) with
  a runtime `CAMERA` permission request; GPS auto-captured on entering the
  step via `FusedLocationProviderClient.getCurrentLocation()`, wrapped so
  a missing permission, no fix, or provider error all resolve to `null`
  rather than throwing. Photos are compressed after capture
  (`MediaCompressor`: downscale to a 1600px long side, re-encode JPEG 80%,
  correct for EXIF rotation) per section 8's explicit rule — added
  `androidx.exifinterface:exifinterface` as a new dependency for the
  rotation fix, since BitmapFactory alone decodes pixels in sensor
  orientation and ignoring EXIF is a classic "photos come out sideways"
  bug. **Simplification, documented rather than silently cut**: video is
  recorded at CameraX's `Quality.SD` with a hard 60 s auto-stop and no
  separate compression pass (`Recorder` already encodes directly, unlike
  `ImageCapture`'s full-resolution JPEG output) — satisfies section 8's
  "limit video length (e.g. 60 s, 720p)" as a ceiling, not a mandate, and
  keeps video files well within that budget without a second transcode
  step. No `RECORD_AUDIO` permission requested — video capture omits audio
  entirely (silent evidence video is adequate for this use case, and it's
  one fewer permission prompt).
- **ملخص**: read-only recap + `AlertDialog` confirmation before the actual
  `reportRepository.saveNewReport(...)` call — matches section 8's "summary
  + confirmation dialog before saving" exactly.

Saving writes the report with `sync_state = PENDING` and every captured
media item the same way — step 2.4's `SyncWorker`/`MediaUploadWorker` pick
up from there; nothing here talks to the network.

14 new `NewReportViewModel` tests (step-gating per field, douar search
re-scoping, location capture success/failure, media add/remove, full
save-path asserting the persisted `Report`/`ReportMedia` shape and
`PENDING` state) + 2 `MediaCompressor` tests (downscale behavior, aspect
ratio preserved) + the 2 DAO test classes from part 1 — 35 Android unit
tests total, all passing; `:app:assembleDebug` succeeds.

**Added to the version catalog**: `androidx.exifinterface:exifinterface`
(photo rotation, part 2 above). Everything else step 2.3 needed
(Room/SQLCipher, CameraX, Play Services Location) was already wired into
`app/build.gradle.kts` back in step 2.2's dependency pass, just unused
until now.

### Step 2.4 — Sync workers (push, media upload, pull) + sync status UI

Also closed the 401-refresh gap `NetworkModule`'s auth interceptor had
flagged back in step 2.2 ("Does NOT handle refresh-on-401 yet — see step
2.4"), since background sync has no user present to react to a plain 401
the way the login screen does: `TokenAuthenticator` (`okhttp3.Authenticator`,
not an `Interceptor` — it only runs after a 401 comes back) refreshes once
and retries, builds its own tiny Retrofit/OkHttp pair for the refresh call
itself (reusing the main `AuthApi` binding would be circular — that binding
comes from the very `OkHttpClient` this authenticator attaches to), and
clears the session if the refresh token itself is dead (reuse-detection
revoked the family, or plain expiry) rather than retrying forever.

**Backend addition found necessary while designing this step**:
`POST /media/{id}/refresh-upload-url` (see the earlier backend commit) —
presigned URLs expire in 15 minutes, but `MediaUploadWorker` deliberately
defers upload until Wi-Fi is available (section 8), which can easily take
longer. Re-signs the same `object_key` a pending row already has instead
of registering a new one through `/media/upload-url`.

**Room schema bumped to v2** (`ReportEntity.serverStatus`/`serverScore`,
`ReportMediaEntity.serverId`) — `fallbackToDestructiveMigration` rather
than a real migration, acceptable pre-release since this is a cache/
outbox, not the system of record, and no device has synced data yet.

**`DefaultSyncRepository`** is where the actual logic lives (`SyncWorker`/
`MediaUploadWorker` are thin — they just call it and map `Result` to
`Result.success()`/`Result.retry()`):
- `pushPendingReports()` — batches every locally `PENDING` report (and its
  still-`PENDING` media) into one `/sync/push` call, idempotent on retry
  per section 5. Applies each result back: `created`/`updated`/`unchanged`
  → local `SYNCED`; anything else → `REJECTED` with the server's error key
  stored verbatim (already localized at the UI layer when 2.5 surfaces it,
  same pattern as everywhere else `errors.*`/`notifications.*` keys flow
  through the app). **Documented simplification**: the backend's push
  response has no client-facing media id to echo back (see the backend's
  own step-2.1 PROGRESS entry on this), so a result's `media[]` array is
  matched to the local rows by *position* — both sides iterate in the same
  order (verified by reading `_register_media`'s loop server-side), so this
  holds, but it's fragile in a way a real id would not be; fine for a
  prototype, called out here rather than left implicit.
- `uploadPendingMedia()` — for every locally pending media item that's been
  registered server-side (`serverId` set by the push above): re-signs its
  upload URL, PUTs the (already-compressed, from step 2.3) bytes with a
  bare `OkHttpClient` (no app interceptors — a presigned URL authenticates
  itself, and attaching a bearer token to it would just be noise), hashes
  the bytes for `/complete`'s sha256 check, and marks the row `SYNCED` or
  `FAILED`. Never touches the network type itself — that's `SyncScheduler`'s
  job via WorkManager `Constraints`, not business logic the repository
  should know about.
- `pull()` — reads the stored cursor (`SyncPreferencesStore`, plain
  DataStore; nothing here is sensitive enough to need Keystore-backed
  storage like the tokens/DB passphrase), upserts douars, and for each
  returned report either updates just the server-echo columns (existing
  local row) or inserts a full new one (a report this device never created
  — fresh install or a second device on the same account; "Room is the
  single source of truth" has to include that case too). Stores the new
  cursor last, only on success.

**`SyncScheduler`** owns all WorkManager enqueuing: `schedulePeriodicSync()`
(15 min, `CONNECTED`, `KEEP` so re-running `onCreate` doesn't reset the
schedule) from `W4FApplication.onCreate()`; `syncNow()` (`REPLACE`,
exponential backoff) called right after a new report is saved and from the
home screen's sync bar; `enqueueMediaUpload(wifiOnly)` called by
`SyncWorker` itself right after a successful push, reading the Wi-Fi-only
preference (`SyncPreferencesStore`, defaults to `true` per section 8 —
no Settings screen exists yet to change it, since it isn't separately
itemized in section 9's step list; deferred, not forgotten).

**Hilt + WorkManager wiring**: `W4FApplication` implements
`Configuration.Provider`, supplying `HiltWorkerFactory` so `@HiltWorker`
workers can have dependencies injected; WorkManager's own default
initializer is removed from the merged manifest (`tools:node="remove"` on
its `meta-data`, standard pattern) since it would otherwise build a
`Configuration` with no worker factory and crash the first time
`SyncWorker`/`MediaUploadWorker` needs constructing.

**Home screen now has its real dossier list and sync status bar**
(`HomeViewModel` combines `ReportRepository.observeReports()` with a new
`NetworkMonitor` (`ConnectivityManager.NetworkCallback` wrapped as a
`Flow<Boolean>`) — the three-state bar from section 8 screen 2 («كل شيء
متزامن» / «N في الانتظار» / «بدون اتصال») collapses "actively sending" and
"queued, about to send" into the same `PENDING` state, matching the spec's
own bar, which doesn't distinguish them either. Each dossier row gets a
status chip derived from local `syncState` only (pending/failed/rejected/
sent) — the richer server-status label (submitted/validated/etc.) is
explicitly step 2.5's "Dossier detail" territory, not duplicated here.
`SyncState.SYNCING` stays defined-but-unused in the entity (section 8's own
state list includes it): marking it mid-push risked stranding a report
there forever if the worker died between marking it and getting a
response, since `getPending()` only re-picks-up rows still `PENDING` — not
worth that risk for a transient status with no UI besides folding into the
same "pending" bucket anyway.

28 new tests (14 `SyncRepository` — push/reject/media-matching/upload-
success/upload-failure/missing-file/pull-upsert-vs-insert/error-as-Result,
not-thrown; 5 `HomeViewModel` — the three sync-status states + sync-now
delegation) + the pre-existing 22 = 50 Android unit tests total, all
passing; `:app:assembleDebug` succeeds. Not yet verified on a device (the
emulator still isn't available this session) — the actual WorkManager
scheduling, the real presigned-upload round-trip, and the 401-refresh path
all need that before they can be called done, not just "compiles and the
repository logic is unit-tested."

### On-device verification pass (steps 2.2–2.4) — six real bugs found

MSI App Player came back up this session. Rebuilt and ran the full app on
it for the first time since step 2.2's initial smoke test, end to end:
login → Home dossier list/sync bar → full "تبليغ جديد" stepper (douar
search, problem chips, numbers, GPS capture, camera) → save → push → the
new report reappearing in the dossier list as synced. Confirmed against
the real backend afterward (`GET /reports`) that the pushed report's
fields, GPS coordinates, and `status: submitted` all matched exactly what
was entered on the phone. **None of this had ever run outside a unit test
before** — six real bugs turned up, every one of them exactly the kind
unit/Robolectric tests structurally cannot catch:

1. **SQLCipher native library never loaded.** `net.zetetic:sqlcipher-android`
   doesn't load `libsqlcipher.so` on class init — `nativeOpen()` and every
   other native method failed with "No implementation found" the instant
   Room tried to open the database, crashing on first launch. Fixed with an
   explicit `System.loadLibrary("sqlcipher")` in `DatabaseModule` before
   `Room.databaseBuilder(...).build()`. Found by reading the actual
   zetetic/sqlcipher-android README usage pattern (via web search) after
   the stack trace alone didn't make the fix obvious — Robolectric never
   touches real JNI, so this was invisible until now.
2. **Cleartext HTTP blocked by Android's default network security
   policy** (API 28+) — a *second*, previously-hidden blocker behind the
   firewall issue from step 2.2: `UnknownServiceException: CLEARTEXT
   communication to 10.0.2.2 not permitted`. The firewall rule alone wasn't
   enough; cleartext is blocked client-side before any network I/O even
   starts. Fixed with a debug-build-only `network_security_config.xml`
   (`src/debug/`, allowing cleartext only to `10.0.2.2`/`localhost`/
   `127.0.0.1`) referenced from a `src/debug/AndroidManifest.xml` overlay —
   release keeps zero exceptions and stays HTTPS-only by construction,
   since the override only merges into debug builds.
3. **The step-2.2 firewall rule had never actually been applied** — `netsh
   advfirewall firewall show rule name="W4F Dev API"` found no matching
   rule despite the session believing it was done; the user re-ran
   `New-NetFirewallRule` this session and it stuck. Confirmed the backend
   was genuinely reachable first via `nc` from inside the emulator (raw
   HTTP request over the actual port) before trusting the app's own error
   message, since the two blockers above were stacked and either one alone
   would show the same generic "تعذر الاتصال بالخادم" message.
4. **The seeded moqaddem's territory assignment is province-level, not
   commune-level** — and `NewReportViewModel`'s douar search filtered the
   local Room cache by `user.territories.map { it.id }` as if those were
   always commune ids, so `WHERE communeId IN (:communeIds)` never matched
   anything; "الدوار" search silently stayed empty forever. Root cause
   wasn't just the Android code: the PROGRESS.md ruling that added this
   filter back in step 2.3 ("a moqaddem's own assignment is realistically
   always their one commune") turned out to be wrong given the actual seed
   data, which assigns the demo moqaddem to the *province* — the exact
   province→commune case the backend's own `territory_scope.py` exists to
   resolve. The real fix is simpler than the bug: `/sync/pull` already only
   ever returns douars the signed-in moqaddem can see (server-side
   resolution), so the client-side filter was pure redundant surface area
   that happened to be wrong — removed it entirely rather than trying to
   mirror the backend's descendant-resolution logic on-device.
   `DouarDao.search()`/`DouarRepository.search()` dropped the `communeIds`
   parameter; `NewReportViewModel` no longer depends on `AuthRepository` at
   all as a result.
5. **A fresh login has nothing to show a "sync now" button for.** The sync
   status bar only showed "مزامنة الآن" when something was locally pending,
   but a brand-new install has zero pending reports (nothing to push) and
   therefore no way to trigger the *pull* that would populate reference
   data (douars) — stuck until the 15-minute periodic tick. Fixed two ways:
   `HomeViewModel.init` now kicks `syncScheduler.syncNow()` on every Home
   entry (cheap and idempotent — `syncNow()` replaces any in-flight
   request), and the sync-now button is now always visible, not
   conditional on `pendingCount > 0` (section 8 screen 7 treats "sync now"
   as a standing action, not a pending-only one anyway).
6. **An unhandled CameraX init failure destabilized the whole activity.**
   BlueStacks' virtual camera HAL returns malformed `StreamConfigurationMap`
   data (`format 0xf375eda0 was not defined`), which made CameraX's own
   internal init-retry loop unstable enough that tapping "التقاط صورة"
   eventually tore down `MainActivity` (`Activity destroy timeout`) rather
   than crashing cleanly with a catchable exception — the process survived,
   relaunching was fine, but the Evidence step was unusable and gave no
   indication why. Not assumed to be BlueStacks-only: real low-end or
   unusual devices can fail camera init too, and section 8 already commits
   to "never block data entry" for exactly this kind of hardware gap.
   Wrapped the whole bind-to-lifecycle block in try/catch, surfacing
   `new_report_camera_unavailable` ("الكاميرا غير متوفرة على هذا الجهاز،
   يمكن المتابعة بدون صور") and skipping the preview/capture UI entirely on
   failure, confirmed fixed by reproducing the same tap afterward with no
   crash. `PackageManager.hasSystemFeature` wasn't a usable guard here —
   BlueStacks reports full camera feature flags (`pm list features` shows
   `android.hardware.camera.any` etc.) despite the HAL being broken, so
   only an actual bind attempt reveals the failure.

Also caught and fixed in the same pass: the summary step
(`SummaryStep.kt`) showed the raw Kotlin enum name (`NO_WATER`) instead of
the localized label for "نوع المشكل" — missed the shared
`ui/common/ReportEnumLabels.kt` helper `ProblemStep.kt` already used.

51 Android unit tests (was 50 — `DouarDaoTest`/`NewReportViewModelTest`
updated for the dropped `communeIds` parameter, `HomeViewModelTest` gained
a case for the init-triggers-sync behavior) + 194 backend tests, all
passing; `:app:assembleDebug` succeeds. **This is the first time the full
Phase 2 pipeline (steps 2.2–2.4) has been confirmed working end-to-end on
a real device against the real backend**, not just unit-tested in
isolation — login, dossier list, the full report stepper, GPS, graceful
camera degradation, local save, push sync, and the backend round-trip all
verified together in one session. Still outstanding: video capture
specifically (camera being unavailable in this environment means only the
graceful-failure path was exercised, not an actual recording), and a real
Wi-Fi-constrained `MediaUploadWorker` run with real media bytes (no media
was ever captured in this session to upload).

Phase 3 (Web), Phase 4 (AI) — not started.
