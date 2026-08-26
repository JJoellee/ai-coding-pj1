import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models import (
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
    is_task_overdue,
)

_tasks: dict[str, TaskResponse] = {}


def add_task(payload: TaskCreate) -> TaskResponse:
    """Create and store a new task.

    Generates ``id`` (a UUID4 string) and sets ``created_at``/
    ``updated_at`` to the same timestamp — none of these are accepted
    from ``payload``, since ``TaskCreate`` has no such fields.

    Args:
        payload: The validated fields to create the task from.

    Returns:
        The newly created, stored task.
    """
    now = datetime.now(timezone.utc)
    task_id = str(uuid.uuid4())
    task = TaskResponse(
        id=task_id,
        title=payload.title,
        description=payload.description or "",
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task
    return task


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee: Optional[str] = None,
    overdue: Optional[bool] = None,
    search: Optional[str] = None,
) -> list[TaskResponse]:
    """Return stored tasks, narrowed by each provided filter in sequence.

    Every filter is optional and combines with AND: each step below
    narrows whatever the previous step already returned, so e.g.
    ``search`` only searches within tasks that already matched ``status``
    and ``priority``, not the full task list.

    Args:
        status: Exact-match filter on task status.
        priority: Exact-match filter on task priority.
        assignee: Exact-match filter on assignee.
        overdue: If not ``None``, keep only tasks whose
            ``is_task_overdue(...)`` result equals this value.
        search: Case-insensitive substring match against title OR
            description. A blank/whitespace-only string is treated as "no
            filter" (matches everything), same as omitting it.

    Returns:
        The matching tasks. An empty list if nothing matches, or if there
        are no stored tasks at all.
    """
    tasks = list(_tasks.values())
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    if priority is not None:
        tasks = [t for t in tasks if t.priority == priority]
    if assignee is not None:
        tasks = [t for t in tasks if t.assignee == assignee]
    if overdue is not None:
        tasks = [t for t in tasks if is_task_overdue(t.due_date, t.status) == overdue]
    if search is not None:
        needle = search.strip().lower()
        if needle:
            tasks = [
                t
                for t in tasks
                if needle in t.title.lower() or needle in t.description.lower()
            ]
    return tasks


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Look up a single task by id.

    Args:
        task_id: The task's UUID string.

    Returns:
        The task, or ``None`` if no task with this id is stored. Does not
        raise — the caller (a route handler) turns ``None`` into a 404.
    """
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """Apply a partial update to a stored task.

    Only fields actually present in ``payload`` are changed
    (``model_dump(exclude_unset=True)``); everything else on the existing
    task is left as-is. ``updated_at`` is always refreshed to now, even if
    no other field changed. Business-rule validation (e.g. status
    transitions) is the caller's responsibility — this function applies
    whatever ``payload`` already contains without re-checking it.

    Args:
        task_id: The task's UUID string.
        payload: The fields to change.

    Returns:
        The updated task, or ``None`` if no task with this id is stored.
    """
    existing = _tasks.get(task_id)
    if existing is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    updated = existing.model_copy(update={**updates, "updated_at": datetime.now(timezone.utc)})
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    """Delete a task by id.

    Args:
        task_id: The task's UUID string.

    Returns:
        ``True`` if a task was found and deleted, ``False`` if no task
        with this id was stored.
    """
    return _tasks.pop(task_id, None) is not None


def _reset() -> None:
    _tasks.clear()
