# Task Tracker — Architecture

## What the app does

Task Tracker is a REST API for creating, listing, retrieving, partially updating, and deleting tasks. It supports task filtering by status, priority, assignee, overdue state, and text search.

## Data model

The core entity is a **Task**. It has a server-generated UUID `id`; required, trimmed `title`; `description`; `status` (`ToDo`, `InProgress`, `Done`); `priority` (`Low`, `Medium`, `High`); optional `assignee` and `due_date`; and UTC `created_at` and `updated_at` timestamps. `is_overdue` is computed when a task is serialized: its due date is before today and its status is not `Done`.

## Request flow

When a user sends `POST /tasks`, FastAPI validates the request against `TaskCreate`. Unknown fields, invalid enum values, invalid dates, and missing, blank, or over-200-character titles are rejected before the route runs. The route passes validated data to storage, which generates a UUID and UTC timestamps, creates a `TaskResponse`, stores it in an in-memory dictionary, and returns it with HTTP 201.

## Key files

- `app/main.py` — FastAPI application setup, CORS policy, health-router inclusion, and `/tasks` CRUD routes.
- `app/models.py` — task enums, request/response models, title validation, and overdue calculation.
- `app/storage.py` — in-memory task dictionary and CRUD/filtering operations.
- `app/business_rules.py` — referenced by the update route for status-transition validation; implementation not visible from the files I read.
- `app/routes/health.py` — referenced as the health router; implementation not visible from the files I read.
- `frontend/index.html` — referenced in a CORS comment as a separately served frontend; implementation not visible from the files I read.

## Conventions

Validation is model-based: input models forbid unknown fields, validate title content, parse dates, and constrain status and priority to enums. Storage is process-local and in memory, using a dictionary keyed by task ID. Missing task lookups become HTTP 404 responses in route handlers; invalid input is handled by FastAPI/Pydantic, and invalid status transitions are delegated to the referenced business-rules module. Frontend/backend interaction is cross-origin HTTP: the API permits only listed local origins on ports 5500 and 8080, with `GET`, `POST`, `PATCH`, `DELETE`, and `OPTIONS`.

## Not visible or assumptions

The permitted status-transition rules are not visible from the files I read. Health endpoint behavior is not visible from the files I read. Frontend behavior, UI design, and its exact API usage are not visible from the files I read. Persistence beyond the running process, authentication, database use, tests, deployment, configuration values, and error-response formatting beyond the explicit 404 cases are not visible from the files I read.