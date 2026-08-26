from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app import storage
from app.business_rules import validate_status_transition
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app.routes import health

load_dotenv()

app = FastAPI(
    title="Task Tracker API",
    description="A simple CRUD REST API for tracking tasks (Module 2 learning project).",
    version="2.0.0",
)

# Module 3: frontend/index.html is served separately (e.g. a local static
# server) from the backend's own origin, so it needs CORS to fetch here.
# Local dev origins only, matching how the frontend is actually run.
LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a new task.

    Args:
        payload: Validated task fields from the request body. Pydantic
            rejects a missing/blank/overlong title, an invalid ``status``
            or ``priority``, an unparsable ``due_date``, or any unknown
            field before this function runs.

    Returns:
        The created task, including server-generated ``id``,
        ``created_at``, ``updated_at``, and computed ``is_overdue``.

    Raises:
        fastapi.exceptions.RequestValidationError: Implicitly, via
            FastAPI, when ``payload`` fails Pydantic validation. Not
            raised by this function's own body.

    Example:
        ``POST /tasks`` with ``{"title": "Ship it"}`` → ``201`` and the
        created task.
    """
    return storage.add_task(payload)


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee: str | None = None,
    overdue: bool | None = None,
    search: str | None = None,
) -> list[TaskResponse]:
    """List tasks, optionally filtered.

    All provided filters are combined with AND — e.g. ``status`` and
    ``search`` together return only tasks matching both.

    Args:
        status: Exact-match filter on task status.
        priority: Exact-match filter on task priority.
        assignee: Exact-match filter on assignee.
        overdue: If ``True``, only overdue tasks; if ``False``, only
            non-overdue tasks; if omitted, no filtering on this field.
        search: Case-insensitive substring match against title OR
            description.

    Returns:
        The matching tasks, in insertion order (dict iteration order —
        deterministic, but not sorted by any task field; the frontend
        sorts by priority client-side). An empty list, not a 404, when
        nothing matches.

    Example:
        ``GET /tasks?status=ToDo&priority=High`` → ``200`` and a
        (possibly empty) list.
    """
    return storage.get_all_tasks(
        status=status,
        priority=priority,
        assignee=assignee,
        overdue=overdue,
        search=search,
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    """Get a single task by id.

    Args:
        task_id: The task's UUID string.

    Returns:
        The matching task.

    Raises:
        fastapi.HTTPException: 404, if no task with this id exists.

    Example:
        ``GET /tasks/{id}`` → ``200`` and the task, or ``404``.
    """
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task.

    Only fields present in ``payload`` are changed
    (``model_dump(exclude_unset=True)`` in ``storage.update_task``). If
    ``status`` is included, the transition from the task's current status
    to the requested one is validated first — see
    ``app/business_rules.py``. An invalid transition rejects the *entire*
    update; no fields are applied.

    Args:
        task_id: The task's UUID string.
        payload: The fields to change. Unknown fields, or a blank/overlong
            title if provided, are rejected by Pydantic before this
            function runs.

    Returns:
        The updated task.

    Raises:
        fastapi.HTTPException: 404, if no task with this id exists.
        fastapi.HTTPException: 422 (via ``validate_status_transition``),
            if ``status`` is present and the transition isn't allowed.

    Example:
        ``PATCH /tasks/{id}`` with ``{"status": "InProgress"}`` → ``200``
        and the updated task, or ``422`` for an invalid transition.
    """
    if payload.status is not None:
        existing = storage.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        validate_status_transition(existing.status, payload.status)

    updated = storage.update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    """Delete a task.

    Args:
        task_id: The task's UUID string.

    Returns:
        None. On success the response body is empty (``204``).

    Raises:
        fastapi.HTTPException: 404, if no task with this id exists.

    Example:
        ``DELETE /tasks/{id}`` → ``204`` with no body, or ``404``.
    """
    deleted = storage.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
