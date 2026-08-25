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
    """A task is overdue if it has a due date in the past and isn't Done.

    Deliberately not stored anywhere — always computed against "today" at
    read time, so it can never go stale between requests.
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
        return _validate_title(v)


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
        return is_task_overdue(self.due_date, self.status)
