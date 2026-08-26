"""Standalone task validation utility.

Independent of the FastAPI/Pydantic request pipeline so it can be reused
(e.g. for validating a task dict loaded from a file or import job) and
unit-tested on its own.
"""
from typing import Any


VALID_STATUSES = ("ToDo", "InProgress", "Done")
VALID_PRIORITIES = ("Low", "Medium", "High")


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
    """Validate a plain task dict against the same core rules as the API.

    Standalone stdlib-only check, independent of Pydantic/FastAPI — and
    deliberately not called from any route. Every request already goes
    through equivalent validation via ``TaskCreate``/``TaskUpdate``
    (``app/models.py``), so wiring this in would just duplicate that
    check. This function exists for validating a task dict from *outside*
    the request pipeline — e.g. a bulk import or a data file — where
    there's no Pydantic model in the loop already.

    Args:
        task: A dict that may contain ``title``, ``status``, and
            ``priority`` keys. Other keys are ignored.

    Returns:
        ``{"valid": bool, "errors": list[str]}``. ``valid`` is ``True``
        only if ``errors`` is empty. Checks title presence/non-blankness,
        and that ``status``/``priority`` are each one of the fixed literal
        values in ``VALID_STATUSES``/``VALID_PRIORITIES`` — note these are
        hardcoded string tuples here, not imported from
        ``app.models.TaskStatus``/``TaskPriority``, so the two could drift
        if one changes without the other.
    """
    errors: list[str] = []

    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("Title is required and cannot be blank")

    status = task.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"Status must be one of: {', '.join(VALID_STATUSES)}")

    priority = task.get("priority")
    if priority not in VALID_PRIORITIES:
        errors.append(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")

    return {"valid": len(errors) == 0, "errors": errors}
