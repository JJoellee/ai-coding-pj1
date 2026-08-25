from datetime import date, timedelta


def test_create_task_with_valid_due_date_returns_201(client):
    due = (date.today() + timedelta(days=7)).isoformat()
    response = client.post("/tasks", json={"title": "Ship the report", "due_date": due})
    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == due
    assert body["is_overdue"] is False


def test_create_task_invalid_due_date_format_returns_422(client):
    response = client.post("/tasks", json={"title": "Bad date", "due_date": "not-a-date"})
    assert response.status_code == 422


def test_overdue_detection_for_past_due_date(client):
    past = (date.today() - timedelta(days=1)).isoformat()
    response = client.post("/tasks", json={"title": "Late task", "due_date": past})
    assert response.status_code == 201
    assert response.json()["is_overdue"] is True


def test_done_task_with_past_due_date_is_not_overdue(client):
    past = (date.today() - timedelta(days=1)).isoformat()
    response = client.post(
        "/tasks", json={"title": "Finished late", "due_date": past, "status": "Done"}
    )
    assert response.status_code == 201
    assert response.json()["is_overdue"] is False


def test_update_due_date(client, created_task):
    new_due = (date.today() + timedelta(days=3)).isoformat()
    response = client.patch(f"/tasks/{created_task['id']}", json={"due_date": new_due})
    assert response.status_code == 200
    assert response.json()["due_date"] == new_due


def test_filter_overdue_true_returns_only_overdue_tasks(client):
    past = (date.today() - timedelta(days=1)).isoformat()
    future = (date.today() + timedelta(days=1)).isoformat()
    client.post("/tasks", json={"title": "Overdue one", "due_date": past})
    client.post("/tasks", json={"title": "Not overdue", "due_date": future})
    client.post("/tasks", json={"title": "No due date"})

    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Overdue one"
