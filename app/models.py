from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_validator


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(v: Optional[str]) -> str:
    if v is None or not v.strip():
        raise ValueError("Title is required and cannot be blank")
    stripped = v.strip()
    if len(stripped) > 200:
        raise ValueError("Title must be 200 characters or fewer")
    return stripped


def is_task_overdue(due_date: Optional[date], status: "TaskStatus") -> bool:
    """Determine whether a task counts as overdue right now.

    Deliberately not stored anywhere — always computed against "today" at
    read time, so it can never go stale between requests. Shared by
    ``TaskResponse.is_overdue`` and the ``overdue`` filter in
    ``app/storage.py`` so the rule can't drift between the two call sites.

    Args:
        due_date: The task's due date, or ``None`` if it has none.
        status: The task's current status.

    Returns:
        ``True`` if ``due_date`` is in the past and ``status`` is not
        ``TaskStatus.DONE``; ``False`` otherwise (including when
        ``due_date`` is ``None``).
    """
    if due_date is None or status == TaskStatus.DONE:
        return False
    return due_date < date.today()


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_must_be_valid(cls, v: str) -> str:
        """Strip, then require a non-blank title of at most 200 characters.

        Args:
            v: The raw ``title`` value from the request body.

        Returns:
            The trimmed title.

        Raises:
            ValueError: If ``v`` is ``None``, blank/whitespace-only after
                stripping, or longer than 200 characters after stripping.
                Pydantic converts this into a 422 response.
        """
        return _validate_title(v)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_must_be_valid(cls, v: Optional[str]) -> str:
        """Apply the same title rule as ``TaskCreate``, only when provided.

        Because the field default is ``None`` and Pydantic v2 doesn't
        validate unset defaults, this only runs when ``title`` is actually
        present in the request body (including an explicit ``null``,
        which is rejected the same as a blank string — a task can't be
        left without a title).

        Args:
            v: The raw ``title`` value, if present in the request body.

        Returns:
            The trimmed title.

        Raises:
            ValueError: If ``v`` is ``None``, blank/whitespace-only after
                stripping, or longer than 200 characters after stripping.
        """
        return _validate_title(v)

    @field_validator("description")
    @classmethod
    def description_none_becomes_empty(cls, v: Optional[str]) -> str:
        """Normalize an explicit ``null`` description to ``""``.

        ``TaskResponse.description`` is a required ``str`` (not
        ``Optional``), and ``storage.update_task`` applies this payload via
        ``model_copy(update=...)``, which does not re-validate. Without
        this normalization, ``PATCH`` with ``{"description": null}`` would
        silently store ``None`` in a field typed as ``str``, which later
        crashes ``storage.get_all_tasks``'s search (``t.description.lower()``
        on ``None``) with an unhandled 500. ``TaskCreate`` already avoids
        this via ``payload.description or ""`` in ``storage.add_task``;
        this keeps ``TaskUpdate`` consistent with that same guarantee.

        Args:
            v: The raw ``description`` value, if present in the request body.

        Returns:
            ``v`` unchanged if truthy, otherwise ``""``.
        """
        return v or ""

    @field_validator("status")
    @classmethod
    def status_must_not_be_null(cls, v: Optional[TaskStatus]) -> TaskStatus:
        """Reject an explicit ``null`` status — same bug class as
        ``description``, found by checking the other ``Optional`` fields
        on this model after fixing ``description``.

        ``TaskResponse.status`` is a required ``TaskStatus`` (not
        ``Optional``), so a client sending ``{"status": null}`` would
        otherwise store ``None`` there via the same unvalidated
        ``model_copy(update=...)`` path. Unlike ``description``, there's no
        sensible default to coerce to — a task must always have some real
        status — so this rejects it outright (422) rather than silently
        substituting a value, matching how ``title`` is handled. Only runs
        when ``status`` is actually provided (see ``title_must_be_valid``
        for why).

        Args:
            v: The raw ``status`` value, if present in the request body.

        Returns:
            ``v`` unchanged.

        Raises:
            ValueError: If ``v`` is ``None``.
        """
        if v is None:
            raise ValueError("status cannot be explicitly set to null")
        return v

    @field_validator("priority")
    @classmethod
    def priority_must_not_be_null(cls, v: Optional[TaskPriority]) -> TaskPriority:
        """Reject an explicit ``null`` priority — see
        ``status_must_not_be_null``; identical reasoning, different field.

        Args:
            v: The raw ``priority`` value, if present in the request body.

        Returns:
            ``v`` unchanged.

        Raises:
            ValueError: If ``v`` is ``None``.
        """
        if v is None:
            raise ValueError("priority cannot be explicitly set to null")
        return v


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Whether this task is overdue right now.

        Computed fresh on every serialization via ``is_task_overdue`` —
        not a stored field, and not client-settable (there's no
        corresponding input on ``TaskCreate``/``TaskUpdate``).

        Returns:
            See ``is_task_overdue``.
        """
        return is_task_overdue(self.due_date, self.status)
