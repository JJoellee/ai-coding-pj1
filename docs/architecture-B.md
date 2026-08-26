# Task Tracker Architecture

## What the app does

Task Tracker is a small single-user task-management app with a Kanban-style web interface. Users can create, view, edit, filter, move, and delete tasks across To Do, In Progress, and Done states; tasks are stored only in memory and reset when the backend restarts.

## Data model

The central entity is a **Task**. Its important fields are:

- `id`, `title`, `status`, `priority`
- `due_date`
- `created_at`, `updated_at`
- `is_overdue` — computed when tasks are read, rather than stored

Statuses are `ToDo`, `InProgress`, and `Done`. Priorities are `Low`, `Medium`, and `High`. Titles are required, trimmed, and limited to 200 characters. Clients cannot supply server-managed fields such as IDs, timestamps, or `is_overdue`.

## Request flow

When a user creates a task, the frontend sends a request to the FastAPI backend at `http://localhost:8000`. The backend validates the request with the task-creation model, rejecting unknown fields and invalid values. It then creates and stores a task in the in-memory storage layer and returns the task response to the frontend, which refreshes the Kanban board.

## Key files

- `app/main.py` — FastAPI application, CORS configuration, and `/tasks` CRUD routes.
- `app/models.py` — task enums, request/response models, field validation, and overdue calculation.
- `app/storage.py` — in-memory dictionary-based task CRUD operations.
- `app/business_rules.py` — allowed status transitions and transition validation.
- `app/routes/health.py` — `GET /health` endpoint.
- `app/validators.py` — standalone task-dictionary validation utility for use outside API requests.
- `frontend/index.html` — Kanban interface, API requests, drag-and-drop, modal editing, and filters.
- `tests/` — API, model, validation, due-date, and search/filter coverage.
- `pytest.ini` — ensures bare `pytest -v` can import the application.
- `README.md` — project documentation, including CI verification details.

## Conventions

Validation is primarily handled by Pydantic request models; unknown request fields are forbidden. Status changes use an explicit transition allow-list: To Do → In Progress, In Progress → Done, and Done → In Progress. Invalid transitions return `422`; updates that do not include `status` skip transition validation.

Storage is intentionally non-persistent and held in an in-memory dictionary. The frontend communicates directly with the backend using `fetch`, rendering loading, error-with-retry, and loaded states. CORS permits only specified local development origins rather than all origins.

## Not visible or assumptions

The supplied structured context did not include the promised one-line file summaries, so this document relies on the provided `AGENTS.md`. The exact task-route paths and response payload shapes beyond the documented `/tasks` CRUD API were not independently inspected. No database, authentication, deployment flow, or persistence behavior is assumed.