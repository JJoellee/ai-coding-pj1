# Task Tracker Architecture

## Purpose and scope

Task Tracker is a course learning project with a FastAPI REST API and a
separately served, vanilla-JavaScript Kanban board. It supports creating,
listing, filtering, retrieving, updating, moving, and deleting tasks. Storage
is in memory only, so tasks are lost when the backend restarts.

## Components

| Component | Responsibility | Evidence |
|---|---|---|
| API application | Creates the FastAPI app, configures CORS, includes the health router, and registers task routes directly on the app. | `app/main.py` |
| Models and validation | Defines task status and priority enums; input/output models; title validation; and computed overdue state. | `app/models.py` |
| Business rules | Defines the explicit status-transition allow-list and produces `422` for invalid moves. | `app/business_rules.py` |
| Storage | Keeps tasks in a module-level dictionary; generates UUID4 IDs and UTC timestamps; and applies list filters. | `app/storage.py` |
| Health route | Returns an `ok` status and current UTC timestamp; it is a liveness check, not a dependency check. | `app/routes/health.py` |
| Frontend | Contains the complete HTML, CSS, and JavaScript Kanban interface and calls the backend at `http://localhost:8000`. | `frontend/index.html` |
| Tests | Uses FastAPI `TestClient` and resets storage before and after each test. | `tests/conftest.py`, `tests/` |

## Task data model

The core entity is a task with these visible fields:

| Field | Source and behavior |
|---|---|
| `id` | Server-generated UUID4 string. |
| `title` | Required, trimmed, non-blank, and at most 200 characters. |
| `description` | Optional input; stored as a string when a task is created. |
| `status` | `ToDo`, `InProgress`, or `Done`; defaults to `ToDo`. |
| `priority` | `Low`, `Medium`, or `High`; defaults to `Medium`. |
| `assignee` | Optional. |
| `due_date` | Optional date. |
| `created_at`, `updated_at` | Server-generated timezone-aware UTC datetimes. |
| `is_overdue` | Computed when a response is serialized: due date is before today and status is not `Done`. |

`TaskCreate` and `TaskUpdate` forbid unknown fields, preventing clients from
setting server-managed fields such as IDs, timestamps, and `is_overdue`.

## API and request flow

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/health` | Returns basic service liveness information. |
| `POST` | `/tasks` | Validates a task request, creates a task, and returns `201`. |
| `GET` | `/tasks` | Returns tasks; `status`, `priority`, `assignee`, `overdue`, and `search` filters combine with AND. |
| `GET` | `/tasks/{task_id}` | Returns one task or `404`. |
| `PATCH` | `/tasks/{task_id}` | Applies supplied fields, validates a supplied status transition, and returns the updated task or `404`/`422`. |
| `DELETE` | `/tasks/{task_id}` | Deletes a task and returns `204`, or `404` when it is absent. |

Create flow:

1. The frontend task form sends JSON to `POST /tasks`.
2. `TaskCreate` validates the fields before the route body runs.
3. The route calls `storage.add_task()`.
4. Storage generates the ID and timestamps, stores a `TaskResponse`, and
   returns it.
5. The frontend closes the form and reloads the task list.

## Business rules and errors

Status transitions are an explicit allow-list:

- `ToDo` -> `InProgress`
- `InProgress` -> `Done`
- `Done` -> `InProgress` (reopen)

All other transitions, including a transition to the same status, return
`422`. A patch that does not include `status` skips transition validation.
Missing task IDs return `404`; invalid request fields, enum values, dates, and
titles are rejected with `422` through request-model validation.

## Frontend interaction

`frontend/index.html` renders the board by task status, sorts cards by
priority, and shows loading, error-with-retry, and loaded states. It uses a
modal for task creation/editing and refetches tasks after a successful form
submission. Drag-and-drop changes a card optimistically, sends a `PATCH`, and
rolls back the visual move if the API rejects it or cannot be reached.

The frontend escapes task-derived values before placing them into HTML. It is
served separately during local development; CORS accepts only the explicit
localhost and loopback origins on ports 5500 and 8080.

## Testing and operations

The test suite uses `pytest` and FastAPI's `TestClient`. `pytest.ini` supplies
the repository Python path required by bare `pytest -v`. The repository also
contains CI that installs `requirements.txt` and runs `pytest -v`, plus a
multi-stage Dockerfile that runs as a non-root user and has a `/health`
health check.

## Boundaries and limitations

- The current storage is process-local and non-persistent.
- Authentication, user accounts, multi-tenancy, a production database, and a
  deployment workflow are out of scope for this course project.
- The repository contains local Docker and CI artifacts, but production-hosting
  architecture and concurrent-write guarantees are not confirmed here.
- `data/tasks.json` is historical material and is not used by current storage.

## Part 5.5D: context-strategy comparison log

| Strategy | What it got right | What it got wrong, missed, or invented | Best suited task shape |
|---|---|---|---|
| A - minimal context | Produced a broad, readable architecture narrative with a data model, create flow, key files, conventions, and assumptions. | Presented detailed repository-specific claims without identifying a context source and repeated the document twice. | A first-pass outline when exact repository accuracy is not yet required. |
| B - structured context | Covered backend, frontend, tests, configuration, storage, and conventions; it also identified that the promised file summaries were absent. | Called the app single-user without support in the draft, made its data-model list less complete than the other drafts, and repeated the document twice. | A cross-cutting architecture document where a structured repository map is available. |
| C - targeted anchor files | Carefully separated visible route/model/storage facts from unseen business rules, health behavior, and frontend implementation. | Was incomplete for a full architecture document because it intentionally omitted details outside its anchor files; it also repeated the document twice. | A bounded technical question, such as documenting a route, validation boundary, or storage flow. |

### Verdict

Strategy B was selected for the final architecture document because it provides
the best broad component map for an architecture audience while exposing gaps
that should be checked against a small set of anchor files. This document uses
that broad structure and verifies its repository claims against the relevant
source files.

For cross-cutting architecture documentation, I use Strategy B because
structured context provides a broad component map while making information gaps
visible. For a bounded route, model, or storage investigation, I use Strategy C
because anchor files constrain claims to evidence actually examined.
