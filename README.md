# Task Tracker API

A simple CRUD REST API for tracking tasks, built with Python and FastAPI.
Built incrementally across two learning modules — see [MODULE1_NOTES.md](MODULE1_NOTES.md)
and [MODULE2_NOTES.md](MODULE2_NOTES.md) for the checklist artifacts and
reflection log from each. **This README describes the current (Module 2)
behavior**; Module 1's JSON-file/int-id version has been superseded, not kept
side by side.

## Scope

**In scope:** create, view, update, and delete tasks. Each task has `id`,
`title`, `description`, `status` (`ToDo`, `InProgress`, `Done`), `priority`
(`Low`, `Medium`, `High`), `assignee`, `created_at`, and `updated_at`.
Filtering the task list by `status` and `priority`. Status changes are
constrained to a fixed set of valid transitions (see below).

**Out of scope:** authentication, user accounts, multi-tenancy, real-time
updates, mobile app, notifications, a production database, deployment, and a
frontend.

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
  data/
    tasks.json               # unused leftover from Module 1 (kept for the record only)
  tests/
    conftest.py               # client fixture + autouse storage._reset()
    test_health.py
    test_tasks.py              # Module 2 CRUD/filter/transition tests
    test_models.py              # Pydantic-level rules (blank title, max length, extra="forbid", etc.)
    test_validators.py
    verify_a.py                 # standalone script version of the test_models.py checks
  requirements.txt
  .env.example
  MODULE1_NOTES.md
  MODULE2_NOTES.md
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
  -d "{\"title\": \"Ship module 2\", \"priority\": \"High\", \"assignee\": \"Joelle\"}"
```

List tasks, optionally filtered:

```bash
curl http://127.0.0.1:8000/tasks
curl "http://127.0.0.1:8000/tasks?status=Done"
curl "http://127.0.0.1:8000/tasks?priority=High"
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
| GET    | `/tasks`         | List tasks (optional `status`, `priority` query params) |
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
| `status` not one of `ToDo`/`InProgress`/`Done`   | 422    | Pydantic enum validation error                                          |
| `priority` not one of `Low`/`Medium`/`High`      | 422    | Pydantic enum validation error                                          |
| Unknown field in the request body (e.g. `id`, `created_at`, `updated_at`) | 422 | Pydantic `extra_forbidden` validation error                |
| Invalid status transition                        | 422    | `Invalid status transition from {current} to {new}. Allowed transitions: [...]` |
| Task ID not found                                | 404    | `Task with id {id} not found`                                           |
