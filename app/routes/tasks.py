from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app import storage
from app.models import Task, TaskCreate, TaskPriority, TaskStatus, TaskUpdate

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[Task])
def list_tasks(
    status: Optional[TaskStatus] = Query(default=None),
    priority: Optional[TaskPriority] = Query(default=None),
):
    tasks = storage.list_tasks()
    if status is not None:
        tasks = [t for t in tasks if t["status"] == status.value]
    if priority is not None:
        tasks = [t for t in tasks if t["priority"] == priority.value]
    return tasks


@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = storage.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    return storage.create_task(payload.model_dump(mode="json"))


@router.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    existing = storage.get_task(task_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    updates = payload.model_dump(exclude_unset=True, mode="json")

    if "status" in updates:
        new_status = TaskStatus(updates["status"])
        current_status = TaskStatus(existing["status"])
        if current_status == TaskStatus.DONE and new_status in (
            TaskStatus.TODO,
            TaskStatus.IN_PROGRESS,
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid status transition: a task with status 'Done' cannot "
                    "be moved back to 'ToDo' or 'InProgress'"
                ),
            )

    updated = storage.update_task(task_id, updates)
    return updated


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    deleted = storage.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None
