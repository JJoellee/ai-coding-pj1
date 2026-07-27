# Task Tracker API

A CRUD REST API for tracking tasks (FastAPI) with a vanilla-JS Kanban board
frontend. Built incrementally across three learning modules plus a
mid-course project — see [MODULE1_NOTES.md](MODULE1_NOTES.md),
[MODULE2_NOTES.md](MODULE2_NOTES.md), [MODULE3_NOTES.md](MODULE3_NOTES.md),
and [docs/midcourse/](docs/midcourse/) for the checklist artifacts,
prompt log, verification evidence, and reflection from each. **This README
describes current behavior**; those files record what changed and why.

## Scope

**In scope:** create, view, update, and delete tasks. Each task has `id`,
`title`, `description`, `status` (`ToDo`, `InProgress`, `Done`), `priority`
(`Low`, `Medium`, `High`), `assignee`, `due_date`, `is_overdue` (computed),
`created_at`, and `updated_at`. Filtering the task list by `status`,
`priority`, `assignee`, `overdue`, and free-text `search` (title/
description), all combinable. Status changes are constrained to a fixed set
of valid transitions (see below). A browser-based Kanban board
(`frontend/index.html`) for viewing, dragging, filtering, searching, and
editing tasks.

**Out of scope:** authentication, user accounts, multi-tenancy, real-time
sync, mobile app, notifications, a production database, deployment, tags,
comments, an activity log, and any frontend framework or build step.

## What changed in Module 2 (vs. Module 1)

- **Storage is now in-memory only** (`app/storage.py`, a module-level
  `dict[str, TaskResponse]`) — not the JSON file. Restarting the server
  clears all tasks. `data/tasks.json` from Module 1 is no longer read or
  written by the app; it's left in the repo only as a record of Module 1.
- **IDs are now UUID strings**, generated with `uuid.uuid4()`, not
  sequential integers.
- **`updated_at` was added** alongside `created_at`; both are set server-side
  and are rejected if a client tries to supply them.
- **The status-transition rule changed, not just extended.** Module 1's rule
  was "`Done` can't go back to `ToDo` or `InProgress`." Module 2 replaces it
  with an explicit allow-list — see the table below. Notably,
  **`Done → InProgress` (reopening a task) is now allowed**, which Module 1
  forbade, and **`ToDo → Done` (skipping `InProgress`) is now forbidden**,
  which Module 1 allowed.
- **Routes moved from `app/routes/tasks.py` into `app/main.py` directly**,
  registered on the app instance rather than via a separate `APIRouter`.
  `app/routes/health.py` is unchanged and still included the same way.
- **The blank-title error is no longer flattened to a plain string.** Module
  1 had a custom `RequestValidationError` handler so a blank title returned
  `{"detail": "Title is required and cannot be blank"}`. Module 2's spec only
  requires "422 through Pydantic," so that handler was removed — a blank
  title now returns Pydantic's default nested error shape instead.

## What the mid-course project added

Two scoped features on top of Module 1-3, on branch `mid-course-project`
(see [docs/midcourse/](docs/midcourse/) for the full user stories, ADR,
prompt log, and verification evidence):

- **Due dates + overdue.** Optional `due_date` (ISO date) on create/update.
  `is_overdue` is a *computed* response field (never stored) — true when
  `due_date` is in the past and `status` isn't `Done`. `GET /tasks?overdue=true`
  filters to only overdue tasks. Visible on cards as an "Overdue" pill and
  editable in the New Task/Edit modal.
- **Search + combined filters.** `GET /tasks?search=<text>` matches
  case-insensitively against `title` or `description`, and combines via AND
  with `status`, `priority`, `assignee`, and `overdue`. A filter bar above
  the board (search box, status/priority dropdowns, overdue checkbox, clear
  button) drives real backend queries — not client-side filtering.

## Design decisions

- **Storage:** in-memory `dict`, keyed by task id. Simplest option for a
  learning project with no persistence requirement; resets on every restart.
- **IDs:** UUID4 strings, assigned in `storage.add_task`.
- **Update semantics:** `PATCH /tasks/{id}` for partial updates — only the
  fields you send are changed (`payload.model_dump(exclude_unset=True)`).
- **Validation:** enforced at the Pydantic model level (`app/models.py`) —
  title required and non-blank after trimming, max 200 characters,
  `status`/`priority` restricted to their enums, and unknown fields rejected
  (`extra="forbid"`) so a client can't sneak in `id`, `created_at`, or
  `updated_at`.
- **Business rule:** status transitions are validated against an explicit
  allow-list (`app/business_rules.py`) rather than an if/elif chain, so the
  rule and its "what's allowed" error message can't drift apart.
- **CORS:** the frontend is served separately from the backend (a static
  file server, not FastAPI), so `CORSMiddleware` allows a small explicit
  list of local dev origins — not `*` — matching how it's actually run.
- **`is_overdue` is computed, not stored:** it's a Pydantic `@computed_field`
  on `TaskResponse`, derived fresh from `due_date`/`status` on every
  response, so it can never go stale between requests. See
  `docs/midcourse/mini-adr.md` for the alternative that was rejected.

## Project structure

```
task-tracker/
  app/
    main.py             # FastAPI app instance + all /tasks routes
    models.py            # TaskStatus, TaskPriority, TaskCreate, TaskUpdate, TaskResponse
    storage.py            # in-memory dict CRUD (id/created_at/updated_at generated here)
    business_rules.py      # VALID_TRANSITIONS + validate_status_transition
    validators.py           # standalone validate_task() utility, independent of FastAPI/Pydantic
    routes/
      health.py             # GET /health
  frontend/
    index.html              # Kanban board: vanilla HTML/CSS/JS, no build step
  data/
    tasks.json               # unused leftover from Module 1 (kept for the record only)
  tests/
    conftest.py               # client fixture + autouse storage._reset()
    test_health.py
    test_tasks.py              # CRUD/filter/transition + PATCH edge-case tests
    test_models.py              # Pydantic-level rules (blank title, max length, extra="forbid", etc.)
    test_validators.py
    test_due_dates.py            # due_date + is_overdue tests (mid-course project)
    test_search_filters.py        # search + combined-filter tests (mid-course project)
    verify_a.py                 # standalone script version of the test_models.py checks
  docs/
    midcourse/                  # mid-course project docs (user stories, ADR, prompt log, verification, reflection)
  requirements.txt
  .env.example
  MODULE1_NOTES.md
  MODULE2_NOTES.md
  MODULE3_NOTES.md
```

## Setup

Requires Python 3.10+.

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env       # Windows; `cp .env.example .env` on macOS/Linux
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

Data lives in memory only — restarting the server clears all tasks.

## Run the frontend

The board is a static file — serve it with any local static server (it
can't be opened as `file://`, since `fetch` needs a real origin for CORS to
apply). With the backend already running on `8000`:

```bash
cd frontend
python -m http.server 5500
```

Open http://localhost:5500/index.html. If you serve it from a different
port, add that origin to `LOCAL_FRONTEND_ORIGINS` in `app/main.py`.

## Test

```bash
pytest -v
```

## Try it with curl

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Create a task (note the response `id` — it's a UUID string, needed for the
next steps):

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Ship module 2\", \"priority\": \"High\", \"assignee\": \"Joelle\", \"due_date\": \"2026-08-01\"}"
```

List tasks, optionally filtered (combine as many as you like):

```bash
curl http://127.0.0.1:8000/tasks
curl "http://127.0.0.1:8000/tasks?status=Done"
curl "http://127.0.0.1:8000/tasks?priority=High"
curl "http://127.0.0.1:8000/tasks?overdue=true"
curl "http://127.0.0.1:8000/tasks?search=report"
curl "http://127.0.0.1:8000/tasks?search=report&status=ToDo&priority=High"
```

Get one task (replace `TASK_ID` with the id from the create response):

```bash
curl http://127.0.0.1:8000/tasks/TASK_ID
```

Update a task (partial — only send the fields you're changing):

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/TASK_ID \
  -H "Content-Type: application/json" \
  -d "{\"status\": \"InProgress\"}"
```

Delete a task:

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/TASK_ID
```

## API reference

| Method | Path             | Description                                  |
|--------|------------------|-----------------------------------------------|
| GET    | `/health`        | Health check                                  |
| GET    | `/tasks`         | List tasks (optional `status`, `priority`, `assignee`, `overdue`, `search` query params — all combinable) |
| GET    | `/tasks/{id}`    | Get one task                                  |
| POST   | `/tasks`         | Create a task (201)                           |
| PATCH  | `/tasks/{id}`    | Partially update a task                       |
| DELETE | `/tasks/{id}`    | Delete a task (204, no body)                  |

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
