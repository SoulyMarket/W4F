# W4F — Build Plan for Claude Code

> Platform for collecting, prioritizing, validating and tracking drinking-water access problems in rural Moroccan douars.
> Chain: **Terrain → Données → Analyse → Priorité → Vérification → Décision → Projet → Suivi → Retour terrain**

This file is the single source of truth for building the project. Read it fully before writing code. Work **phase by phase, step by step**, and do not start a step until the previous step's acceptance criteria pass.

---

## 0. How to work

- Build in the order given in section 9. After each step: run the tests, fix failures, then commit with a clear message (`feat(auth): ...`, `feat(db): ...`).
- Keep a `PROGRESS.md` at the repo root: tick off steps, note decisions and anything deferred.
- If something in this plan is ambiguous, choose the simplest option that respects the security rules (section 6), write the decision in `PROGRESS.md`, and continue. Stop and ask only for decisions that are hard to reverse (changing the stack, deleting data, changing the auth model).
- Never commit secrets. Use `.env` (git-ignored) plus a committed `.env.example`.
- UI language is **Arabic first** (default, right-to-left), with **French** as the second language the user can switch to. See section 2.1. Never hard-code UI text: every string lives in resource/translation files with both `ar` and `fr` versions from day one.
- Code, identifiers, comments and commit messages are in **English**.

---

## 1. Users and roles

| Role | Who | Can |
|---|---|---|
| `admin` | Technical administrator | Manage users, roles, territories; read audit logs; system settings. No business decisions. |
| `manager` | Responsable / gestionnaire | Read everything in their territories; dashboard and map; convert validated reports into projects; change project status; edit scoring weights. |
| `expert` | Technical expert | Read reports in their territories; validate / request re-verification / modify analysis; propose a technical solution; give an urgency opinion. |
| `moqaddem` | Field agent | Create reports for douars in **their own territory only**; upload photos, videos, GPS; see the status of their dossiers, priorities and projects. Uses the Android app only. |

**Least privilege**: each user sees only what their role and territory allow. Territory filtering is enforced **in database queries**, not only in route guards.

---

## 2. Tech stack

### Backend (`/backend`)
- Python 3.12+, **FastAPI**, Uvicorn
- **PostgreSQL 16** (+ **PostGIS** extension enabled; store `geography(Point, 4326)` for locations)
- **SQLAlchemy 2.x** (typed, `Mapped[...]`), **Alembic** migrations
- **Pydantic v2** + `pydantic-settings`
- Auth: **argon2-cffi** (password hashing), **PyJWT** (access tokens)
- Media storage: **MinIO** (S3-compatible) via `boto3`, presigned upload URLs
- Tests: **pytest**, `httpx` / FastAPI `TestClient`, a dedicated Postgres test database (via Docker)
- Lint/format: **ruff**, type check: **mypy** (non-blocking at first)
- **Docker Compose**: `api`, `db` (postgis/postgis:16), `minio`

### Android app (`/android`) — Phase 2
- **Kotlin**, **Jetpack Compose**, Material 3
- MVVM + **Hilt** (DI), Coroutines + Flow
- **Room** (local DB) encrypted with **SQLCipher**
- **WorkManager** (background sync)
- **Retrofit** + OkHttp + kotlinx.serialization
- **CameraX** (photo/video), **Fused Location Provider** (GPS)
- **MapLibre Android** (map, with offline tile packs)
- **Firebase Cloud Messaging** (push notifications)
- Secure token storage: **Android Keystore** + EncryptedSharedPreferences (or DataStore + Tink)
- minSdk 26, targetSdk latest stable

### Web dashboard (`/web`) — Phase 3
- **React + TypeScript + Vite**, TanStack Query, React Router
- **MapLibre GL JS** (map), Recharts (charts), Tailwind CSS

### 2.1 Languages and RTL (applies to every phase)
- **Default locale: `ar` (Modern Standard Arabic, RTL)**. Second locale: `fr`. Each user has `preferred_language` (`ar` | `fr`, default `ar`); apps start in that language and allow switching in settings.
- **Digits**: use Western digits (0–9), as is usual in Morocco, in both languages. Dates in `dd/MM/yyyy`.
- **Backend**: never return UI sentences built in code. Store machine values (enums, keys + params) and localize at the edge:
  - API reads `Accept-Language` (fallback: the user's `preferred_language`, then `ar`) for any human-readable text (error messages, priority reasons, notification text).
  - Translations in `backend/app/i18n/ar.json` and `fr.json`; a `t(key, lang, **params)` helper. A test fails if any key exists in one file and not the other.
  - Enum values (problem types, statuses, solution types) are returned as codes; clients translate them.
- **Android**: `android:supportsRtl="true"`; `values/strings.xml` = Arabic (default), `values-fr/strings.xml` = French; per-app language via `AppCompatDelegate.setApplicationLocales`. Use only start/end (never left/right) for padding and alignment; mirror directional icons (`autoMirrored`). Arabic-capable font (e.g. **Noto Sans Arabic** or **Cairo**, bundled). Test every screen in both directions.
- **Web**: **i18next** + react-i18next, `ar` default; set `<html lang dir>` dynamically (`dir="rtl"` for Arabic); use Tailwind logical utilities (`ms-*`, `me-*`, `ps-*`, `pe-*`, `text-start`) only; charts and map controls must also flip correctly.
- Free-text fields (observations, comments) accept Arabic, French or Darija in Arabic or Latin script; store as UTF-8, no transliteration.

---

## 3. Repository structure

```
w4f/
├── PROGRESS.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config.py, security.py, logging.py, rate_limit.py
│   │   ├── db/            # session.py, base.py
│   │   ├── models/        # one file per entity
│   │   ├── schemas/       # Pydantic in/out models
│   │   ├── api/
│   │   │   ├── deps.py    # get_db, get_current_user, require_roles, territory scope
│   │   │   └── routes/    # auth.py, users.py, territories.py, douars.py, reports.py,
│   │   │                  # priorities.py, validations.py, projects.py, dashboard.py,
│   │   │                  # audit.py, sync.py, media.py, notifications.py
│   │   ├── services/      # scoring.py, audit.py, sync.py, notifications.py, storage.py
│   │   └── seed.py        # demo data
│   └── tests/
├── android/
└── web/
```

---

## 4. Data model

All tables: `id UUID PK` (default `gen_random_uuid()`), `created_at`, `updated_at` (timestamptz, UTC). Use Postgres enums or check constraints for status fields.

### `users`
`id, full_name, email (unique, lowercase), phone (nullable), password_hash, role (admin|manager|expert|moqaddem), preferred_language (ar|fr, default ar), is_active, failed_login_count, locked_until (nullable), last_login_at`

### `territories`
Hierarchy: `id, name_ar, name_fr, level (province|commune), parent_id (nullable FK territories)`.

### `user_territories`
`user_id, territory_id` (composite PK). A user assigned to a province sees all its communes.

### `douars`
`id, name_ar, name_fr, commune_id (FK territories), location geography(Point), population, families_count, notes`

### `reports` (signalements)
- `id UUID` — **generated on the phone** (enables idempotent offline sync)
- `douar_id, moqaddem_id (FK users)`
- `water_source` (enum: `network | well | spring | tank_truck | river | other`)
- `problem_type` (enum: `no_water | intermittent | low_pressure | contamination | broken_pump | broken_pipe | dry_source | other`)
- `problem_started_on (date), duration_days (int)`
- `interruption_frequency` (enum: `permanent | daily | weekly | monthly | rare`)
- `has_alternative_source (bool), alternative_distance_km (numeric, nullable)`
- `severity_reported` (enum: `low | medium | high | critical`)
- `water_quality_risk (bool)`
- `affected_families, affected_people (int)`
- `observations (text)`
- `location geography(Point), location_accuracy_m`
- `collected_at` (device time), `synced_at` (server time)
- `status` (enum: `submitted | under_review | recheck_requested | validated | rejected | converted_to_project`)
- `version (int)` — incremented on every server-side change (for sync)

### `report_media`
`id, report_id, kind (photo|video), object_key (MinIO), mime_type, size_bytes, sha256, captured_at, upload_status (pending|uploaded)`

### `scoring_config`
`id, weights (jsonb), is_active, created_by, created_at` — only one active row. Managers edit; history kept.

### `priorities`
`id, report_id, score (0–100), breakdown (jsonb: list of {criterion, value, weight, points, reason_key, reason_params}), config_id, computed_at` — reasons are stored as translation keys + params, never as sentences. Recomputed on report change and on config change; keep history (latest = current).

### `validations`
`id, report_id, expert_id, decision (validated|recheck_requested|modified|rejected), comment, proposed_solution (text), urgency_opinion (low|medium|high|critical), created_at`

### `projects`
`id, report_id (unique), douar_id, title, solution_type` (enum: `pipe_repair | pump_repair | network_extension | reservoir | source_improvement | equipment | temporary_solution | technical_study`), `description, status` (enum: `new | in_study | approved | in_preparation | in_progress | completed | cancelled`), `owner_id, planned_start, planned_end, actual_start, actual_end, progress_percent`

### `project_updates`
`id, project_id, author_id, old_status, new_status, progress_percent, note, created_at` (+ optional media via `report_media`-like table `project_media`)

### `notifications`
`id, user_id, type, params (jsonb), entity_type, entity_id, is_read, created_at` — title/body are rendered from `type` + `params` in the recipient's language (push text is rendered at send time with the recipient's `preferred_language`)

### `device_tokens`
`id, user_id, fcm_token (unique), platform, last_seen_at`

### `refresh_tokens`
`id, user_id, token_hash (sha256), family_id, expires_at, revoked_at, replaced_by, user_agent, ip`

### `audit_log` (append-only)
`id, actor_id, action (create|update|delete|login|login_failed|logout|status_change|export), entity_type, entity_id, old_value jsonb, new_value jsonb, ip, user_agent, created_at`
- Create a DB trigger or revoke `UPDATE/DELETE` on this table for the app role so it cannot be modified.

---

## 5. API (prefix `/api/v1`)

### Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | email + password → access token (15 min) + refresh token (30 days for moqaddem, 7 days others) |
| POST | `/auth/refresh` | rotate refresh token; reuse of an old token revokes the whole family |
| POST | `/auth/logout` | revoke current refresh token |
| POST | `/auth/logout-all` | revoke all user sessions |
| GET | `/auth/me` | current user + territories |
| POST | `/auth/change-password` | |

### Admin
- `GET/POST /users`, `GET/PATCH /users/{id}`, `POST /users/{id}/deactivate`, `POST /users/{id}/reset-password`
- `GET/POST/PATCH /territories`, `PUT /users/{id}/territories`
- `GET /audit` (filters: actor, entity, action, date range; paginated)

### Douars
- `GET /douars` (territory-scoped, search, pagination), `POST`, `GET/PATCH /douars/{id}` — admin/manager write

### Reports
- `GET /reports` (filters: status, douar, commune, province, priority range, date; sort by score)
- `GET /reports/{id}` (with media URLs, priority breakdown, validations history)

### Priorities / scoring
- `GET /reports/{id}/priority` → score + explanation
- `GET /scoring-config`, `PUT /scoring-config` (manager) → triggers recompute of all open reports

### Validation (expert)
- `POST /reports/{id}/validations` → updates report status accordingly, notifies the moqaddem

### Projects (manager)
- `POST /reports/{id}/project` (only if report `validated`)
- `GET /projects`, `GET/PATCH /projects/{id}`
- `POST /projects/{id}/updates` (status change with allowed transitions only, see below)

Allowed project transitions:
`new → in_study → approved → in_preparation → in_progress → completed`; any non-completed → `cancelled`. Reject everything else with 409.

### Dashboard
- `GET /dashboard/summary` — totals: douars, reports by status, priority douars (score ≥ 70), projects by status, recurring problems (douars with ≥ 3 reports in 12 months)
- `GET /dashboard/map` — GeoJSON FeatureCollection of douars with latest score, report count, project status

### Media
- `POST /media/upload-url` → presigned PUT URL for MinIO (validate mime: jpeg/png/webp/mp4; max photo 10 MB, video 100 MB)
- `POST /media/{id}/complete` → verify object exists, size and sha256, mark `uploaded`
- `GET` media goes through short-lived presigned GET URLs (never public buckets)

### Sync (moqaddem, Phase 2)
- `POST /sync/push` — body: list of reports (with client UUIDs) + media metadata. **Idempotent**: same UUID twice = no duplicate; returns per-item result `{id, status: created|updated|unchanged|rejected, error?}`.
- `GET /sync/pull?since=<server_cursor>` — returns changes in the moqaddem's territory since cursor: douars, their own reports' statuses, priorities, validations (requests for re-verification), projects and updates, notifications. Returns new `cursor`.
- Conflict rule: the phone owns field data while the report is `submitted` and not yet reviewed; once the server status moves past `submitted`, **server wins** and the push of field-data edits is rejected with a reason (the moqaddem must create a new observation).

### Notifications
- `GET /notifications`, `POST /notifications/{id}/read`, `POST /devices` (register FCM token)
- Triggers: new report (→ experts of territory), recheck requested (→ moqaddem), validated (→ moqaddem + managers), priority changed by ≥ 10 points, project created / status changed / completed (→ moqaddem + managers).

Use consistent error format: `{"error": {"code": "...", "message": "..."}}` — `code` is stable English, `message` is localized (Arabic by default). OpenAPI docs enabled only when `ENV=dev`.

---

## 6. Security requirements (non-negotiable)

1. Passwords: Argon2id; minimum 10 characters; never logged.
2. Login: rate limit per IP and per account (e.g. 5 failures → lock 15 min); log `login_failed` in audit.
3. JWT: short-lived access token (HS256 with strong secret from env, or RS256); include `sub`, `role`, `exp`, `jti`. Refresh tokens are opaque random strings, stored only as SHA-256 hashes, rotated on each use, with reuse detection.
4. Every route has an explicit role requirement via `require_roles(...)`. No route is accidentally public (add a test that iterates all routes and checks this).
5. Territory scoping applied in a shared query helper used by every list/detail endpoint; test that a moqaddem/expert from territory A gets 404 on territory B resources.
6. Every create/update/delete/status change writes to `audit_log` with old and new values (service-layer helper, not ad hoc).
7. Input validation through Pydantic with bounds (e.g. people ≥ 0, lat/lng ranges, text length limits).
8. CORS restricted to the web dashboard origin.
9. Security headers on responses; HTTPS assumed in production (behind a reverse proxy).
10. Media: presigned URLs only, mime and size checks, private bucket.
11. Backups: a `scripts/backup.sh` doing `pg_dump` + MinIO mirror, documented in README.
12. Android: encrypted Room DB, tokens in Keystore-backed storage, no tokens in logs, certificate pinning optional (document how to enable).

---

## 7. Priority scoring (explainable, not AI)

Default weights (total 100), stored in `scoring_config.weights` and editable by managers:

| Criterion | Max points | Rule |
|---|---|---|
| People affected | 25 | `min(affected_people / 1000, 1) × 25` |
| Duration | 15 | `min(duration_days / 30, 1) × 15` |
| Frequency | 10 | permanent 1.0, daily 0.8, weekly 0.5, monthly 0.25, rare 0.1 |
| No alternative source | 15 | 15 if `has_alternative_source = false`, else 0 |
| Distance to alternative | 10 | `min(km / 5, 1) × 10` (0 if no alternative → already covered above, give full 10) |
| Severity | 15 | low 0.25, medium 0.5, high 0.75, critical 1.0 — use the **expert's urgency opinion if present**, otherwise the reported severity |
| Water quality / safety risk | 10 | 10 if true |

- Output: `score` (rounded int 0–100) and `breakdown` — one entry per criterion with points earned and a reason key + params, rendered in the requested language. Examples:

  | Key | ar | fr |
  |---|---|---|
  | `priority.people_affected` | `{count} شخص متضرر` | `{count} personnes concernées` |
  | `priority.no_alternative` | `لا يوجد مصدر بديل للماء` | `Aucune source alternative` |
  | `priority.long_duration` | `المشكل مستمر منذ {days} يوما` | `Problème depuis {days} jours` |
  | `priority.expert_confirmed` | `المشكل مؤكد من طرف خبير` | `Problème confirmé par un expert` (informational line when a validation exists) |

- `GET /reports/{id}/priority` returns the breakdown sorted by points, so the UI can show **«لماذا هذه الأولوية؟»** / «Pourquoi cette priorité ?».
- Implement in `services/scoring.py` as a **pure function** (`compute_priority(report, validation, weights) -> PriorityResult`) with thorough unit tests.
- The score is decision **support** only: nothing in the system changes a status automatically based on the score.

---

## 8. Android app (Phase 2) — design

### Screens (Arabic by default, RTL; simple, big buttons, icons next to every label, minimal typing)
1. **تسجيل الدخول** (Connexion) — email/phone + password; remember session.
2. **الرئيسية** (Accueil) — big «تبليغ جديد» button; list of my dossiers with status chips; sync status bar («كل شيء متزامن» / «3 في الانتظار» / «بدون اتصال»).
3. **تبليغ جديد** (Nouveau signalement) — stepper with short pages:
   1. الدوار — searchable list from local DB (searches both Arabic and French names), pre-filtered to my territory
   2. المشكل — chips with icons for type, source, frequency, severity
   3. الأرقام — families, people, duration, alternative source yes/no + distance (numeric keypad)
   4. الإثباتات — photo/video via CameraX, GPS auto-captured with accuracy shown
   5. ملخص — summary + confirmation dialog before saving
4. **تفاصيل الملف** (Détail du dossier) — data, media, priority + «لماذا هذه الأولوية؟», validation history, linked project and its progress, re-verification requests highlighted.
5. **الإشعارات** (Notifications)
6. **الخريطة** (Carte) — my douars with status colors (offline tiles for my territory).
7. **الإعدادات** (Paramètres) — language (العربية / Français), sync now, upload media only on Wi-Fi (default on), logout.

### Offline-first rules
- Room is the **single source of truth**; the UI only reads from Room.
- Report saved locally with a client-generated UUID and `sync_state` (`pending | syncing | synced | failed | rejected`).
- **Outbox**: WorkManager `SyncWorker` (constraints: network connected) runs on save, periodically (15 min), and on "Synchroniser maintenant". It pushes pending reports, uploads media (separate `MediaUploadWorker`, Wi-Fi constraint by default, resumable/retry with backoff), then pulls with the stored cursor.
- Compress photos (max 1600 px long side, JPEG ~80%) and limit video length (e.g. 60 s, 720p).
- Never block data entry on network or GPS (GPS can be "pending" and filled later).
- Show sync state per dossier and globally.

### Module structure
`app/` with packages: `data/local` (Room entities, DAOs), `data/remote` (Retrofit API, DTOs), `data/repository`, `sync/` (workers), `domain/`, `ui/` (screens, components, theme), `di/`.

---

## 9. Build order and acceptance criteria

### Phase 1 — Backend (government side)

**Step 1.1 — Scaffold**
- Monorepo layout, `docker-compose.yml` (postgis, minio, api), `.env.example`, `pyproject.toml`, ruff config, `/health` endpoint, i18n helper with `ar.json`/`fr.json` + key-parity test, README with run instructions.
- ✅ `docker compose up` starts all services; `GET /api/v1/health` returns 200 and checks DB connectivity.

**Step 1.2 — Database**
- All models from section 4, first Alembic migration, PostGIS extension, audit_log protection.
- `seed.py`: 1 province (Al Haouz / الحوز), 3 communes, 10 douars with realistic coordinates and names in both Arabic and French, one user per role, 15 sample reports with varied data.
- ✅ `alembic upgrade head` on an empty DB succeeds; seed runs twice without duplicates.

**Step 1.3 — Auth**
- Login, refresh with rotation and reuse detection, logout, logout-all, me, change-password, lockout, rate limit.
- ✅ Tests: valid login; wrong password increments counter and locks; refresh rotation; reusing old refresh token revokes the family; deactivated user cannot log in.

**Step 1.4 — RBAC, territory scope, audit**
- `require_roles`, territory query helper, audit service + middleware/dependency.
- ✅ Tests: route-coverage test (every route declares roles except login/refresh/health); cross-territory access returns 404; every write produces an audit row with old/new values.

**Step 1.5 — Admin endpoints** (users, territories, audit read)
- ✅ Tests for create/update/deactivate users and territory assignment; non-admins get 403.

**Step 1.6 — Douars and reports (read side)**
- ✅ Filtering, pagination, sorting by priority; tests for scoping.

**Step 1.7 — Scoring**
- `compute_priority` + config endpoints + recompute job.
- ✅ Unit tests for each criterion and edge cases (zero people, no alternative, expert override); changing config recomputes scores.

**Step 1.8 — Expert validation**
- ✅ Validation changes report status correctly, creates notification for the moqaddem, writes audit.

**Step 1.9 — Projects**
- ✅ Only validated reports can become projects; transition rules enforced (409 on invalid); updates logged.

**Step 1.10 — Dashboard + map GeoJSON + media endpoints + notifications**
- ✅ Summary numbers match seed data in tests; GeoJSON validates; presigned upload/complete flow works against MinIO.

### Phase 2 — Moqaddem sync + Android

**Step 2.1 — Sync API** (`/sync/push`, `/sync/pull`, device tokens, FCM sender service with a no-op fallback when Firebase is not configured)
- ✅ Tests: pushing the same batch twice creates no duplicates; pull returns only own-territory data and a working cursor; conflict rule enforced.

**Step 2.2 — Android scaffold**: Compose, Hilt, Room+SQLCipher, Retrofit, theme with bundled Arabic font, RTL + `ar`/`fr` string resources, in-app language switch, navigation, login + token storage.
**Step 2.3 — Report form** with CameraX, GPS, local save.
**Step 2.4 — Sync workers** (push, media upload, pull) + sync status UI.
**Step 2.5 — Dossier detail, notifications (FCM), map with offline tiles.**
- ✅ Every screen checked in Arabic (RTL) and French (LTR): no clipped text, no left/right misalignment, icons mirrored where directional.
- ✅ End-to-end: put emulator in airplane mode → create 2 reports with photos → restore network → reports, media and GPS appear in backend; expert validates on backend → status and notification appear on the phone.

### Phase 3 — Web dashboard
- Arabic (RTL) by default with a language switch to French; layout, tables, charts and map controls correct in both directions.
- Login, dashboard summary, map (colored by priority), reports list + detail with «لماذا هذه الأولوية؟», expert validation screen, project board (by status), admin users/territories/audit, scoring weights editor.
- ✅ Every role sees only their allowed menus and data.

### Phase 4 — AI assistance (proposals only, never decisions)
- Anomaly detection on reports (e.g. IsolationForest on numeric fields + rules: people > douar population, duration inconsistent with start date) → flagged for expert, never auto-rejected.
- Recurring-problem detection per douar.
- LLM-generated draft reports (monthly summary per province) generated in the reader's language (Arabic by default) and clearly labeled «مسودة من إنشاء الذكاء الاصطناعي — يجب التحقق منها» / «Brouillon généré par IA — à vérifier».

---

## 10. Definition of done (prototype)

The demo shows the full chain with seeded data:
**Collecte (offline) → Synchronisation → Analyse → Priorisation expliquée → Validation expert → Projet → Suivi → Retour terrain (notification + statut sur le téléphone)**

The demo runs in **Arabic**, and switching to French works everywhere.

Plus: all tests pass, README explains setup in under 10 commands, `PROGRESS.md` is up to date, and no secrets are in the repo.
