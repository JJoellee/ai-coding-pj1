import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    temp_file = tmp_path / "tasks.json"
    temp_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_FILE", temp_file)
    return TestClient(app)
