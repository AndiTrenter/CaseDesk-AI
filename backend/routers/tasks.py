"""Tasks Router"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List, Optional
import uuid
import logging

from deps import db, require_auth, log_action
from models import TaskCreate
from routers.date_utils import safe_parse_datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tasks")
async def list_tasks(
    case_id: str = None,
    status: str = None,
    user: dict = Depends(require_auth)
):
    """List all tasks for the current user"""
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    if status:
        query["status"] = status
    
    # Status normalization mapping
    status_map = {
        "open": "todo",
        "pending": "todo",
        "completed": "done",
        "closed": "done"
    }
    
    try:
        tasks = await db.tasks.find(query, {"_id": 0}).sort("due_date", 1).to_list(1000)
        # Ensure all tasks have required fields and normalize status
        for task in tasks:
            if "priority" not in task:
                task["priority"] = "medium"
            # Normalize legacy status values
            current_status = task.get("status", "todo")
            task["status"] = status_map.get(current_status, current_status)
            if task["status"] not in ["todo", "in_progress", "done"]:
                task["status"] = "todo"
            
            # ROBUST FIX: Handle both datetime objects AND malformed string dates from legacy DB
            task["due_date"] = safe_parse_datetime(task.get("due_date"))
            task["created_at"] = safe_parse_datetime(task.get("created_at"))
            task["updated_at"] = safe_parse_datetime(task.get("updated_at"))
        
        return tasks
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return []


@router.post("/tasks")
async def create_task(task_data: TaskCreate, user: dict = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    task_id = str(uuid.uuid4())
    
    new_task = {
        "id": task_id,
        "user_id": user["id"],
        "title": task_data.title,
        "description": task_data.description,
        "priority": task_data.priority or "medium",
        "status": task_data.status or "todo",
        "due_date": task_data.due_date.isoformat() if task_data.due_date else None,
        "case_id": task_data.case_id,
        "created_at": now,
        "updated_at": now
    }
    await db.tasks.insert_one(new_task)
    await log_action(user["id"], "create_task", "task", task_id)
    
    # Return without _id
    new_task.pop("_id", None)
    return new_task


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, task_data: TaskCreate, user: dict = Depends(require_auth)):
    task = await db.tasks.find_one({"id": task_id, "user_id": user["id"]})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if task_data.title is not None:
        update_data["title"] = task_data.title
    if task_data.description is not None:
        update_data["description"] = task_data.description
    if task_data.priority is not None:
        update_data["priority"] = task_data.priority
    if task_data.status is not None:
        update_data["status"] = task_data.status
    if task_data.due_date is not None:
        update_data["due_date"] = task_data.due_date.isoformat() if hasattr(task_data.due_date, 'isoformat') else task_data.due_date
    if task_data.case_id is not None:
        update_data["case_id"] = task_data.case_id
    
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    await log_action(user["id"], "update_task", "task", task_id)
    
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return updated


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(require_auth)):
    result = await db.tasks.delete_one({"id": task_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await log_action(user["id"], "delete_task", "task", task_id)
    return {"success": True, "message": "Task deleted"}
