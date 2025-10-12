from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional, List
import uuid

router = APIRouter(prefix="/tasks", tags=["tasks"])

tasks_db = {}

class Task(BaseModel):
    id: str
    title: str
    due_date: Optional[date] = None
    status: str = "Pending"  # Pending, Overdue, Completed
    assigned_user: Optional[str] = None
    overdue_reason: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    due_date: Optional[str] = None
    assigned_user: Optional[str] = None

    @validator("due_date")
    def validate_due_date(cls, v):
        if not v:
            return None
        try:
            d = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format, must be YYYY-MM-DD")
        return v


# Utility function to update overdue tasks
def check_and_mark_overdue():
    today = date.today()
    for task in tasks_db.values():
        if (
            task.due_date
            and task.due_date < today
            and task.status != "Completed"
        ):
            task.status = "Overdue"
            task.overdue_reason = "Due date has passed"
        elif task.status == "Overdue" and task.due_date and task.due_date >= today:
            task.status = "Pending"
            task.overdue_reason = None


@router.get("/", response_model=List[Task])
def list_tasks():
    check_and_mark_overdue()
    return list(tasks_db.values())


@router.post("/", response_model=Task)
def create_task(task: TaskCreate):
    due_date = (
        datetime.strptime(task.due_date, "%Y-%m-%d").date()
        if task.due_date
        else None
    )

    # Validate past date
    if due_date and due_date < date.today():
        raise HTTPException(status_code=400, detail="Due date cannot be in the past")

    new_task = Task(
        id=str(uuid.uuid4()),
        title=task.title,
        due_date=due_date,
        assigned_user=task.assigned_user,
    )
    tasks_db[new_task.id] = new_task
    return new_task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: str, updated: TaskCreate):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]
    if updated.title:
        task.title = updated.title
    if updated.due_date:
        d = datetime.strptime(updated.due_date, "%Y-%m-%d").date()
        if d < date.today():
            raise HTTPException(status_code=400, detail="Due date cannot be in the past")
        task.due_date = d
    if updated.assigned_user:
        task.assigned_user = updated.assigned_user

    tasks_db[task_id] = task
    return task


@router.post("/{task_id}/complete", response_model=Task)
def mark_complete(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]
    task.status = "Completed"
    task.overdue_reason = None
    tasks_db[task_id] = task
    return task


@router.post("/mark_overdue")
def mark_overdue():
    """Simulate midnight auto-update"""
    check_and_mark_overdue()
    return {"message": "Overdue tasks updated"}
