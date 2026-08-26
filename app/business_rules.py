from fastapi import HTTPException, status

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """Enforce the status-transition allow-list.

    Checked against the ``(current, new)`` pair via ``VALID_TRANSITIONS``,
    not just whether ``new`` is a real status — so this also rejects
    same-status "transitions" (e.g. ``ToDo`` → ``ToDo``), which are valid
    enum values individually but not a valid move.

    Args:
        current: The task's status before the update.
        new: The requested status.

    Raises:
        fastapi.HTTPException: 422, if ``(current, new)`` is not in
            ``VALID_TRANSITIONS``. The detail message lists every allowed
            transition.
    """
    if (current, new) not in VALID_TRANSITIONS:
        allowed = sorted({f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition from {current.value} to {new.value}. Allowed transitions: {allowed}",
        )
