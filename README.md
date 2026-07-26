# Task Tracker API (Module 1)

A simple CRUD REST API for tracking tasks, built with Python and FastAPI.

## Scope

**In scope:** create, view, update, and delete tasks. Each task has `id`,
`title`, `description`, `status` (`ToDo`, `InProgress`, `Done`), `priority`
(`Low`, `Medium`, `High`), and `assignee`. Filtering the task list by
`status` and `priority`.

**Out of scope (Module 1):** authentication, user accounts, multi-tenancy,
real-time updates, mobile app, notifications, a production database, and
deployment, and no frontend.

## Design decisions

- **Storage:** a single JSON file (`data/tasks.json`) instead of a real
  database. This is a learning project, not production software — a file is
  simplest to read, debug, and reset.
- **IDs:** sequential integers assigned by the storage layer (`max(id) + 1`),
  not UUIDs — easier to read and type while testing manually.
- **Update semantics:** `PATCH /tasks/{id}` for partial updates (only the
  fields you send are changed), rather than a full-replace `PUT`.
- **Business rule:** a task in `Done` cannot move back to `ToDo` or
  `InProgress`. Attempting it returns `422` with a clear message.
- **Validation:** structural validation (types, enum values) is handled by
  Pydantic. The "title is required and cannot be blank" rule is enforced
  explicitly in the route so the error response is a plain, testable string
  rather than Pydantic's nested error format.

## Project structure

```
task-tracker/
  app/
    main.py          # FastAPI app instance, router registration
    models.py         # Pydantic models: TaskStatus, TaskPriority, Task, TaskCreate, TaskUpdate
    storage.py         # JSON file read/write (the persistence layer)
    validators.py       # Standalone validate_task() utility, independent of FastAPI
    routes/
      health.py         # GET /health
      tasks.py          # CRUD + filtering for /tasks
  data/
    tasks.json          # JSON "database" (starts as an empty list)
  tests/
    conftest.py          # TestClient fixture pointed at a temp JSON file
    test_health.py
    test_tasks.py
    test_validators.py
  requirements.txt
  .env.example
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

## Test

```bash
pytest -v
```

## Try it with curl

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Create a task:

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Ship module 1\", \"priority\": \"High\", \"assignee\": \"Joelle\"}"
```

List tasks, optionally filtered:

```bash
curl http://127.0.0.1:8000/tasks
curl "http://127.0.0.1:8000/tasks?status=Done"
curl "http://127.0.0.1:8000/tasks?priority=High"
```

Get one task:

```bash
curl http://127.0.0.1:8000/tasks/1
```

Update a task (partial — only send the fields you're changing):

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d "{\"status\": \"InProgress\"}"
```

Delete a task:

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

## API reference

| Method | Path             | Description                                  |
|--------|------------------|-----------------------------------------------|
| GET    | `/health`        | Health check                                  |
| GET    | `/tasks`         | List tasks (optional `status`, `priority` query params) |
| GET    | `/tasks/{id}`    | Get one task                                  |
| POST   | `/tasks`         | Create a task                                 |
| PATCH  | `/tasks/{id}`    | Partially update a task                       |
| DELETE | `/tasks/{id}`    | Delete a task                                 |

### Validation & error responses

| Condition                                      | Status | Detail                                                                 |
|-------------------------------------------------|--------|-------------------------------------------------------------------------|
| Title missing or blank after trimming            | 422    | `Title is required and cannot be blank`                                 |
| `status` not one of `ToDo`/`InProgress`/`Done`   | 422    | Pydantic enum validation error                                          |
| `priority` not one of `Low`/`Medium`/`High`      | 422    | Pydantic enum validation error                                          |
| Moving a `Done` task back to `ToDo`/`InProgress` | 422    | `Invalid status transition: a task with status 'Done' cannot be moved back to 'ToDo' or 'InProgress'` |
| Task ID not found                                | 404    | `Task {id} not found`                                                   |

