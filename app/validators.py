"""Standalone task validation utility.

Independent of the FastAPI/Pydantic request pipeline so it can be reused
(e.g. for validating a task dict loaded from a file or import job) and
unit-tested on its own.
"""
from typing import Any


VALID_STATUSES = ("ToDo", "InProgress", "Done")
VALID_PRIORITIES = ("Low", "Medium", "High")


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
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
