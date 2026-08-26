# Task Tracker Architecture

## What the app does
Task Tracker is a small task-management application with a FastAPI REST API and a vanilla JavaScript Kanban board. Users create, view, filter, edit, move, and delete tasks across `ToDo`, `InProgress`, and `Done` columns.

## Data model
`Task` fields: server-generated UUID `id`; required trimmed `title` (max 200 characters); `description`; `status` (`ToDo`, `InProgress`, `Done`); `priority` (`Low`, `Medium`, `High`); optional `assignee` and ISO date `due_date`; UTC `created_at` and `updated_at`. `is_overdue` is computed when returned: a past due date on a task not marked `Done`.

## Request flow: create a task
1. The board’s create dialog gathers task details and sends `POST /tasks` to the API.
2. FastAPI validates the body with `TaskCreate`; invalid or unknown fields receive `422`.
3. The route calls storage, which creates a UUID and timestamps, then stores a `TaskResponse` in memory.
4. The API returns `201 Created` with the complete task, including computed `is_overdue`.
5. The frontend closes the dialog and reloads the task list to render the task in its status column.

## Key files
- `app/main.py` — FastAPI application, CORS, and task CRUD routes.
- `app/models.py` — Pydantic task models, enums, title validation, overdue computation.
- `app/storage.py` — in-memory dictionary CRUD, UUID and timestamp generation, filtering.
- `app/business_rules.py` — explicit status-transition allow-list and `422` failures.
- `app/routes/health.py` — `GET /health` liveness endpoint.
- `app/validators.py` — standalone dictionary validator; not used by API routes.
- `frontend/index.html` — complete HTML/CSS/JavaScript Kanban interface and API client.
- `tests/test_tasks.py` — CRUD and transition-rule coverage.
- `tests/test_due_dates.py` / `tests/test_search_filters.py` — overdue, search, and filter coverage.
- `requirements.txt` — pinned Python runtime dependencies.

## Conventions
Validation is model-based: task input forbids extra fields, restricts enums, parses dates, and rejects blank or long titles. Storage is intentionally process-local and resets on restart. Missing tasks return `404`; invalid request data and invalid status moves return `422`. Allowed moves are `ToDo → InProgress`, `InProgress → Done`, and `Done → InProgress`; same-status moves are rejected. The separately served frontend calls `http://localhost:8000`, uses JSON over REST, refreshes after form changes, and rolls back optimistic drag-and-drop moves if the API rejects them. CORS permits specified local development origins only.

## Not visible or assumptions
No database, authentication, user accounts, persistence, deployment environment, or production hosting architecture is evident in the application code. The API is assumed to be single-process for its in-memory storage semantics; multi-process behavior and concurrent-write guarantees were not confirmed.