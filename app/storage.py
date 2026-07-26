"""Simple JSON-file storage for tasks.

Module 1 scope: no production database. A single JSON file on disk is the
entire persistence layer, guarded by a lock so requests don't interleave
reads/writes.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "tasks.json"
_lock = threading.Lock()


def _read_all() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    content = DATA_FILE.read_text(encoding="utf-8").strip()
    return json.loads(content) if content else []


def _write_all(tasks: list[dict[str, Any]]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def list_tasks() -> list[dict[str, Any]]:
    with _lock:
        return _read_all()


def get_task(task_id: int) -> Optional[dict[str, Any]]:
    with _lock:
        tasks = _read_all()
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def create_task(task_data: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        tasks = _read_all()
        next_id = max((t["id"] for t in tasks), default=0) + 1
        task = {
            "id": next_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **task_data,
        }
        tasks.append(task)
        _write_all(tasks)
        return task


def update_task(task_id: int, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
    with _lock:
        tasks = _read_all()
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                tasks[i] = {**task, **updates}
                _write_all(tasks)
                return tasks[i]
    return None


def delete_task(task_id: int) -> bool:
    with _lock:
        tasks = _read_all()
        filtered = [t for t in tasks if t["id"] != task_id]
        if len(filtered) == len(tasks):
            return False
        _write_all(filtered)
        return True
