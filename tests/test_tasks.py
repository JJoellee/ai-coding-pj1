def create_sample_task(client, **overrides):
    payload = {
        "title": "Write the report",
        "description": "Quarterly summary",
        "status": "ToDo",
        "priority": "High",
        "assignee": "Joelle",
    }
    payload.update(overrides)
    return client.post("/tasks", json=payload)


def test_create_task_success(client):
    response = create_sample_task(client)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Write the report"
    assert body["status"] == "ToDo"
    assert body["priority"] == "High"
    assert body["assignee"] == "Joelle"


def test_create_task_blank_title_returns_422(client):
    response = create_sample_task(client, title="   ")
    assert response.status_code == 422
    assert response.json()["detail"] == "Title is required and cannot be blank"


def test_create_task_invalid_status_returns_422(client):
    response = create_sample_task(client, status="Blocked")
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = create_sample_task(client, priority="Urgent")
    assert response.status_code == 422


def test_create_task_defaults_status_and_priority(client):
    response = client.post("/tasks", json={"title": "Minimal task"})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ToDo"
    assert body["priority"] == "Medium"
    assert body["description"] == ""
    assert body["assignee"] is None
    assert "created_at" in body


def test_create_task_title_over_200_chars_returns_422(client):
    response = create_sample_task(client, title="x" * 201)
    assert response.status_code == 422


def test_create_task_rejects_unknown_field(client):
    response = create_sample_task(client, made_up="value")
    assert response.status_code == 422


def test_create_task_rejects_client_supplied_id(client):
    response = create_sample_task(client, id=999)
    assert response.status_code == 422


def test_update_task_rejects_client_supplied_created_at(client):
    created = create_sample_task(client).json()
    response = client.patch(
        f"/tasks/{created['id']}", json={"created_at": "2025-01-01T00:00:00Z"}
    )
    assert response.status_code == 422


def test_list_tasks_returns_all(client):
    create_sample_task(client, title="Task A")
    create_sample_task(client, title="Task B")
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tasks_filter_by_status(client):
    create_sample_task(client, title="Task A", status="Done")
    create_sample_task(client, title="Task B", status="ToDo")
    response = client.get("/tasks", params={"status": "Done"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Task A"


def test_list_tasks_filter_by_priority(client):
    create_sample_task(client, title="Task A", priority="Low")
    create_sample_task(client, title="Task B", priority="High")
    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Task B"


def test_get_task_not_found_returns_404(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task_status(client):
    created = create_sample_task(client).json()
    response = client.patch(f"/tasks/{created['id']}", json={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_update_task_blank_title_returns_422(client):
    created = create_sample_task(client).json()
    response = client.patch(f"/tasks/{created['id']}", json={"title": "   "})
    assert response.status_code == 422
    assert response.json()["detail"] == "Title is required and cannot be blank"


def test_done_task_cannot_move_back_to_todo(client):
    created = create_sample_task(client, status="Done").json()
    response = client.patch(f"/tasks/{created['id']}", json={"status": "ToDo"})
    assert response.status_code == 422
    assert "cannot be moved back" in response.json()["detail"]


def test_done_task_cannot_move_back_to_in_progress(client):
    created = create_sample_task(client, status="Done").json()
    response = client.patch(f"/tasks/{created['id']}", json={"status": "InProgress"})
    assert response.status_code == 422


def test_update_nonexistent_task_returns_404(client):
    response = client.patch("/tasks/999", json={"status": "Done"})
    assert response.status_code == 404


def test_delete_task(client):
    created = create_sample_task(client).json()
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_delete_nonexistent_task_returns_404(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
