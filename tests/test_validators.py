from app.validators import validate_task


def test_valid_task_has_no_errors():
    result = validate_task({"title": "Write tests", "status": "ToDo", "priority": "Medium"})
    assert result == {"valid": True, "errors": []}


def test_blank_title_is_invalid():
    result = validate_task({"title": "   ", "status": "ToDo", "priority": "Medium"})
    assert result["valid"] is False
    assert "Title is required and cannot be blank" in result["errors"]


def test_missing_title_is_invalid():
    result = validate_task({"status": "ToDo", "priority": "Medium"})
    assert result["valid"] is False
    assert "Title is required and cannot be blank" in result["errors"]


def test_invalid_status_and_priority_are_reported():
    result = validate_task({"title": "Task", "status": "Blocked", "priority": "Urgent"})
    assert result["valid"] is False
    assert len(result["errors"]) == 2
