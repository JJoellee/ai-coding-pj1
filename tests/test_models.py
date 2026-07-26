import pytest
from pydantic import ValidationError

from app.models import TaskCreate, TaskPriority, TaskStatus, TaskUpdate


def test_whitespace_title_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title=" ")


def test_empty_title_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="")


def test_title_over_200_chars_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="x" * 201)


def test_defaults_applied():
    task = TaskCreate(title="Hello")
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.MEDIUM
    assert task.description == ""
    assert task.assignee is None


def test_extra_field_rejected_on_create():
    with pytest.raises(ValidationError):
        TaskCreate(title="x", made_up="value")


def test_id_rejected_on_create():
    with pytest.raises(ValidationError):
        TaskCreate(title="x", id="abc")


def test_created_at_rejected_on_update():
    with pytest.raises(ValidationError):
        TaskUpdate(created_at="2025-01-01T00:00:00Z")


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="x", status="Whatever")
