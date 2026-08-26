# Task Tracker API

## 1. Project overview

A CRUD REST API for tracking tasks, built with FastAPI, plus a vanilla-JS
Kanban board frontend (no framework, no build step). Each task has a
title, description, status (`ToDo`/`InProgress`/`Done`, with a fixed
allow-list of valid transitions), priority, assignee, and an optional due
date with a computed "overdue" flag. The task list supports filtering and
free-text search, all combinable. Built incrementally across an
AI-assisted coding course — see [MODULE1_NOTES.md](MODULE1_NOTES.md),
[MODULE2_NOTES.md](MODULE2_NOTES.md), [MODULE3_NOTES.md](MODULE3_NOTES.md),
and [docs/midcourse/](docs/midcourse/) for what changed at each stage and
why. **This README describes current behavior only.**

## 2. Prerequisites

- Python **3.11** — pinned in CI (`.github/workflows/ci.yml`) and
  `Dockerfile`, both with real, repeated, passing automated evidence
  behind them. 3.12.2 also worked throughout local development for this
  entire project with no issues. 3.10 — what Module 1's original README
  stated — was never actually tested against; treat that number as
  unverified, not this one.
- `pip`
- A modern browser, to use `frontend/index.html`
- `git`
- Docker — only needed for the "Run with Docker" section below; everything
  else works without it.

## 3. Local setup

From the repository root:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env       # Windows; `cp .env.example .env` on macOS/Linux
```

## 4. Run the app locally

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Storage is in-memory only — restarting the server clears all tasks.

To also use the frontend, in a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Open http://localhost:5500/index.html. If you serve it from a different
port, add that origin to `LOCAL_FRONTEND_ORIGINS` in `app/main.py` (CORS
only allows an explicit list of local dev origins, not `*`).

## 5. Run tests

```bash
pytest -v
```

Requires `pytest.ini` (repo root, `pythonpath = .`) to resolve `from app
import storage` in `tests/conftest.py` — without it, bare `pytest -v`
fails with `ModuleNotFoundError: No module named 'app'` even though
`python -m pytest` would work fine. Don't remove `pytest.ini`.

There's also a standalone script covering the same model-validation rules
as `tests/test_models.py`, runnable directly — note it needs `PYTHONPATH`
set explicitly (confirmed: fails without it, `pytest.ini`'s `pythonpath`
setting doesn't apply to a bare `python` invocation):

```bash
# macOS/Linux
PYTHONPATH=. python tests/verify_a.py

# Windows (PowerShell)
$env:PYTHONPATH="."; python tests\verify_a.py
```

## 6. Run with Docker

```bash
docker build -t task-tracker:dev .
docker run -d --name tt-dev -p 8000:8000 task-tracker:dev
curl http://localhost:8000/health
docker exec tt-dev whoami   # expected: app (non-root)
docker stop tt-dev && docker rm tt-dev
```

Verified on a real machine (2026-08-26): image builds clean (13/13 steps),
container starts, `GET /health` returns `200` with the expected JSON body,
`docker exec tt-dev whoami` → `app`, and `docker history` shows no
`python:latest` or baked-in secrets. Full write-up in
[docs/decisions/dockerfile-design.md](docs/decisions/dockerfile-design.md).

The image is a multi-stage build (`python:3.11-slim`, not `latest`),
copies only the installed dependencies and `app/` — not `tests/`, `docs/`,
`frontend/`, or any `.env` file — and runs as a non-root `app` user. No
`--reload` in the container command. It also declares a `HEALTHCHECK`
against `GET /health`, confirmed live (`docker inspect
--format='{{.State.Health.Status}}' tt-dev` → `healthy` after the 30s
start period). See `Dockerfile`, `.dockerignore`, and
[docs/decisions/dockerfile-design.md](docs/decisions/dockerfile-design.md)
for the full design rationale, including a real (not reputation-based)
alpine-vs-slim benchmark.

## 7. CI workflow summary

`.github/workflows/ci.yml` runs on every `push` and `pull_request`:
checkout → set up Python 3.11 (pinned, not `latest`) → `pip install -r
requirements.txt` → `pytest -v`. No deployment step. No
`continue-on-error`, `|| true`, or `--exit-zero` — a test failure fails
the run.

This was verified with a real green → red → green cycle, not just by
reading the YAML:

| Commit | Change | CI result |
|---|---|---|
| `784f0d2` | baseline | ✅ success |
| `e3657af` | intentional one-line test break (`tests/test_health.py`) | ❌ failure |
| `afd25c3` | revert of the above | ✅ success |

(Confirmed via the GitHub Actions API for each commit, not inferred from
the commit messages alone.)

## 8. Project structure

```
task-tracker/
  .github/
    workflows/
      ci.yml                   # push/PR: checkout, Python 3.11, pip install, pytest -v
  app/
    main.py                    # FastAPI app instance + all /tasks routes
    models.py                   # TaskStatus, TaskPriority, TaskCreate, TaskUpdate, TaskResponse
    storage.py                   # in-memory dict CRUD (id/created_at/updated_at generated here)
    business_rules.py             # VALID_TRANSITIONS + validate_status_transition
    validators.py                  # standalone validate_task() utility, independent of FastAPI/Pydantic
    routes/
      health.py                    # GET /health
  frontend/
    index.html                      # Kanban board: vanilla HTML/CSS/JS, no build step
  data/
    tasks.json                       # unused leftover from Module 1 (kept for the record only)
  tests/
    conftest.py                       # client fixture + autouse storage._reset()
    test_health.py
    test_tasks.py                      # CRUD/filter/transition + PATCH edge-case tests
    test_models.py                      # Pydantic-level rules (blank title, max length, extra="forbid", etc.)
    test_validators.py
    test_due_dates.py                    # due_date + is_overdue tests
    test_search_filters.py                # search + combined-filter tests
    verify_a.py                            # standalone script version of the test_models.py checks
  docs/
    midcourse/                              # mid-course project docs
    decisions/
      dockerfile-design.md                    # technical decision note, see § 10 below
  Dockerfile                                  # multi-stage, non-root, python:3.11-slim
  .dockerignore
  pytest.ini                                   # pythonpath = . (see Run tests, above)
  CLAUDE.md                                     # AI-assistant guidance for this repo
  requirements.txt
  .env.example
  MODULE1_NOTES.md
  MODULE2_NOTES.md
  MODULE3_NOTES.md
```

## 9. Project conventions and current limitations

- **Storage is in-memory only** — no database, no persistence. This is
  deliberate for the course's scope, not an oversight; `data/tasks.json`
  is Module 1 history, unused by current code.
- **IDs are UUID4 strings**, not sequential integers.
- **Status transitions are an explicit allow-list**
  (`app/business_rules.py`), not an if/elif chain — see `CLAUDE.md` for
  the full table. `Done → InProgress` (reopen) is allowed; `ToDo → Done`
  (skipping `InProgress`) is not.
- **`is_overdue` is computed on every response, never stored** — derived
  from `due_date`/`status` so it can't go stale between requests.
- **Validation is Pydantic-level** (`app/models.py`): required non-blank
  title (≤200 chars), enum-restricted `status`/`priority`, valid ISO
  `due_date`, and `extra="forbid"` so a client can't set `id`,
  `created_at`, `updated_at`, or `is_overdue` directly.
- **No auth, no user accounts, no multi-tenancy, no real-time sync, no
  production database, no deployment step.** Out of scope for this
  project; the Docker artifacts exist for local containerized running
  only, not for shipping anywhere.
- **`app/validators.py:validate_task`** is a standalone, stdlib-only check,
  deliberately not called from any route — every request already goes
  through equivalent validation via `TaskCreate`/`TaskUpdate`, so wiring
  this in would duplicate that check. It exists for validating a task dict
  from outside the request pipeline (e.g. a bulk import). It hardcodes its
  own valid-status/valid-priority lists rather than importing
  `TaskStatus`/`TaskPriority`, so the two could still drift if one changes
  without the other — that risk stands regardless of the wiring decision.

## 10. Technical decision notes

- [Dockerfile design](docs/decisions/dockerfile-design.md) — context,
  alternatives considered, trade-offs, and open questions behind the
  multi-stage build, beyond what fits in this README's "conventions"
  section above.

---

## API reference

| Method | Path             | Description                                  |
|--------|------------------|-----------------------------------------------|
| GET    | `/health`        | Health check                                  |
| GET    | `/tasks`         | List tasks (optional `status`, `priority`, `assignee`, `overdue`, `search` query params — all combinable) |
| GET    | `/tasks/{id}`    | Get one task                                  |
| POST   | `/tasks`         | Create a task (201)                           |
| PATCH  | `/tasks/{id}`    | Partially update a task                       |
| DELETE | `/tasks/{id}`    | Delete a task (204, no body)                  |

### Try it with curl

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Ship module 4\", \"priority\": \"High\", \"assignee\": \"Joelle\", \"due_date\": \"2026-09-01\"}"

curl http://127.0.0.1:8000/tasks
curl "http://127.0.0.1:8000/tasks?status=Done"
curl "http://127.0.0.1:8000/tasks?overdue=true"
curl "http://127.0.0.1:8000/tasks?search=report&status=ToDo&priority=High"

curl http://127.0.0.1:8000/tasks/TASK_ID

curl -X PATCH http://127.0.0.1:8000/tasks/TASK_ID \
  -H "Content-Type: application/json" \
  -d "{\"status\": \"InProgress\"}"

curl -X DELETE http://127.0.0.1:8000/tasks/TASK_ID
```

### Status transitions

| From → To            | Allowed? |
|-----------------------|----------|
| `ToDo` → `InProgress`  | ✅ |
| `InProgress` → `Done`  | ✅ |
| `Done` → `InProgress`  | ✅ (reopen) |
| `ToDo` → `Done`        | ❌ (must go through `InProgress`) |
| `Done` → `ToDo`        | ❌ |
| any status → itself    | ❌ |

An invalid transition returns 422 with detail
`Invalid status transition from {current} to {new}. Allowed transitions: [...]`.
Sending a `PATCH` with no `status` field skips this check entirely (other
fields still update normally).

### Validation & error responses

| Condition                                      | Status | Detail                                                                 |
|-------------------------------------------------|--------|-------------------------------------------------------------------------|
| Title missing, blank, or over 200 characters     | 422    | Pydantic validation error (nested `detail` list)                        |
| `due_date` not a valid ISO date                  | 422    | Pydantic date validation error                                          |
| `status` not one of `ToDo`/`InProgress`/`Done`   | 422    | Pydantic enum validation error                                          |
| `priority` not one of `Low`/`Medium`/`High`      | 422    | Pydantic enum validation error                                          |
| Unknown field in the request body (e.g. `id`, `created_at`, `updated_at`) | 422 | Pydantic `extra_forbidden` validation error                |
| Invalid status transition                        | 422    | `Invalid status transition from {current} to {new}. Allowed transitions: [...]` |
| Task ID not found                                | 404    | `Task with id {id} not found`                                           |
