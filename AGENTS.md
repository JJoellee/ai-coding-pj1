# AGENTS.md

Guidance for Codex (or any AI assistant) working in this repository.

## 1. Tech stack

- Python **3.11** — pinned in CI and `Dockerfile`, both with real passing
  automated evidence. 3.12.2 also worked for local dev throughout this
  project. 3.10 (an earlier, untested guess in Module 1's original README)
  should not be assumed to work — it was never actually tried.
- FastAPI `0.115.0` (`requirements.txt`)
- Pydantic **v2** `2.9.2` (`requirements.txt`) — confirmed v2-only APIs in
  use: `ConfigDict`, `field_validator`, `computed_field` (`app/models.py`)
- Uvicorn `0.30.6` (`requirements.txt`)
- pytest `8.3.3`, httpx `0.27.2` (`requirements.txt`) — test suite uses
  `fastapi.testclient.TestClient`
- Frontend: vanilla HTML/CSS/JavaScript, single file (`frontend/index.html`),
  no framework, no build step

## 2. Run command

```bash
uvicorn app.main:app --reload --port 8000
```

## 3. Test command

```bash
pytest -v
```

Requires `pytest.ini` (repo root, `pythonpath = .`) to resolve `from app
import storage` in `tests/conftest.py` — `tests/` has no `__init__.py`, so
without it bare `pytest -v` fails in CI with
`ModuleNotFoundError: No module named 'app'` even though `python -m pytest`
works fine locally (`-m` adds the current directory to `sys.path`
automatically; bare `pytest` does not). Don't remove `pytest.ini`.

## 4. Architecture summary

- **Backend** (`app/`):
  - `main.py` — the FastAPI app instance and every `/tasks` route
    (`create_task`, `list_tasks`, `get_task`, `update_task`, `delete_task`),
    plus CORS middleware. Routes are registered directly on `app`, not via
    a separate router (only `health` uses a router).
  - `models.py` — `TaskStatus`, `TaskPriority` enums; `TaskCreate`,
    `TaskUpdate`, `TaskResponse` Pydantic models; `is_task_overdue()`.
  - `storage.py` — in-memory `dict[str, TaskResponse]` CRUD. Not persisted;
    resets on every restart.
  - `business_rules.py` — **this is where task transition rules live**
    (`VALID_TRANSITIONS`, `validate_status_transition`).
  - `routes/health.py` — `GET /health`, included via `app.include_router`.
  - `validators.py` — standalone `validate_task()` dict-validation utility.
    Deliberately not wired into the API — every request already goes
    through equivalent validation via `TaskCreate`/`TaskUpdate`, so wiring
    this in would duplicate that check. Exists for validating a task dict
    from outside the request pipeline (e.g. a bulk import).
- **Frontend** (`frontend/index.html`): Kanban board, fetches from the
  backend at `http://localhost:8000`, drag-and-drop, create/edit modal,
  filter bar.
- **Tests** (`tests/`): `conftest.py` (fixtures, autouse `storage._reset()`),
  `test_health.py`, `test_tasks.py`, `test_models.py`, `test_validators.py`,
  `test_due_dates.py`, `test_search_filters.py`, plus a standalone script
  `verify_a.py` (run directly, not via pytest).
- **Where task rules live:** business/transition rules →
  `app/business_rules.py`; field-level validation (title, due date format,
  unknown fields) → `app/models.py`.

## 5. Business rules

- Status values (`app/models.py`, `TaskStatus`): `ToDo`, `InProgress`, `Done`.
- Priority values (`app/models.py`, `TaskPriority`): `Low`, `Medium`, `High`.
- Transition rules (`app/business_rules.py`, `VALID_TRANSITIONS`) — an
  explicit allow-list, not an if/elif chain:
  - `ToDo → InProgress` ✅
  - `InProgress → Done` ✅
  - `Done → InProgress` ✅ (reopen)
  - Everything else — `ToDo → Done`, `Done → ToDo`, any status → itself,
    `InProgress → ToDo` — is rejected with `422`.
- A `PATCH` with no `status` field skips transition validation entirely
  (`app/main.py`, `update_task`).
- Title: required, trimmed, blank or >200 chars rejected (`app/models.py`,
  `_validate_title`).
- Unknown fields on `TaskCreate`/`TaskUpdate` are rejected
  (`extra="forbid"`), so a client can't set `id`, `created_at`,
  `updated_at`, or `is_overdue` directly.
- `is_overdue` is **computed on every read**, never stored — `due_date` in
  the past **and** `status != Done` (`app/models.py`, `is_task_overdue`).

## 6. UI states and CORS

- **UI states** (`frontend/index.html`, `boardState` / `renderBoard()`):
  `loading` (shown while `GET /tasks` is pending), `error` (fetch failed —
  banner + Retry button), and a `loaded` state that covers both "ready" and
  "empty" — columns always render; an individually empty column shows a
  "No tasks" placeholder rather than hiding.
- **CORS** (`app/main.py`): `CORSMiddleware` allows only an explicit list of
  local dev origins (`localhost`/`127.0.0.1` on ports `5500` and `8080`) —
  not `*`. Add an origin to `LOCAL_FRONTEND_ORIGINS` if serving the frontend
  from a different port.

## 7. Do-not rules

- Do not add authentication.
- Do not add a database.
- Do not add deployment steps.
- Do not make major UI changes without asking first.

## 8. CI and Docker (added Module 4)

- **CI** (`.github/workflows/ci.yml`): runs on every `push`/`pull_request`
  — checkout, Python 3.11 (pinned), `pip install -r requirements.txt`,
  `pytest -v`. No deploy step, no `continue-on-error`/`|| true`/
  `--exit-zero`. Verified with a real green → red → green cycle (see
  `README.md` § CI workflow summary for the actual commit SHAs).
- **Docker** (`Dockerfile`, `.dockerignore`): multi-stage,
  `python:3.11-slim` (not `latest`), non-root `app` user, `HEALTHCHECK`
  against `GET /health`. Both build and run verified live, including
  `docker exec ... whoami` → `app`. Full rationale — including a real
  (not reputation-based) alpine-vs-slim benchmark — in
  `docs/decisions/dockerfile-design.md`.
- Python version resolved (see § 1): 3.11, on real CI/Docker evidence —
  no remaining open items from this module.
