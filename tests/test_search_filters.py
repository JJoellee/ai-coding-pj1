def create(client, **overrides):
    payload = {"title": "Task", "status": "ToDo", "priority": "Medium"}
    payload.update(overrides)
    return client.post("/tasks", json=payload)


def test_search_matches_title(client):
    create(client, title="Write the quarterly report")
    create(client, title="Buy groceries")

    response = client.get("/tasks", params={"search": "quarterly"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Write the quarterly report"


def test_search_matches_description(client):
    create(client, title="Task A", description="Contains the word banana")
    create(client, title="Task B", description="Nothing relevant here")

    response = client.get("/tasks", params={"search": "banana"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Task A"


def test_search_combined_with_status_and_priority(client):
    create(client, title="Write report", status="ToDo", priority="High")
    create(client, title="Write memo", status="ToDo", priority="Low")
    create(client, title="Review report", status="InProgress", priority="High")

    response = client.get(
        "/tasks", params={"search": "report", "status": "ToDo", "priority": "High"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Write report"


def test_search_no_matches_returns_200_and_empty_list(client, created_task):
    response = client.get("/tasks", params={"search": "no-such-term-anywhere"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_invalid_status_filter_returns_422(client):
    response = client.get("/tasks", params={"status": "Bogus"})
    assert response.status_code == 422
