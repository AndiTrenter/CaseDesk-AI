"""Events Router with deadline automation and reminders"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import uuid

from deps import db, require_auth, log_action
from models import Event, EventCreate

router = APIRouter()

# Reminder time options (in minutes before event)
REMINDER_OPTIONS = {
    "none": None,
    "at_time": 0,
    "5_min": 5,
    "15_min": 15,
    "30_min": 30,
    "1_hour": 60,
    "2_hours": 120,
    "1_day": 1440,
    "2_days": 2880,
    "1_week": 10080,
    "2_weeks": 20160
}


@router.get("/events", response_model=List[Event])
async def list_events(
    case_id: str = None,
    user: dict = Depends(require_auth)
):
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    events = await db.events.find(query, {"_id": 0}).sort("start_time", 1).to_list(1000)
    return events


@router.get("/events/reminder-options")
async def get_reminder_options(user: dict = Depends(require_auth)):
    """Get available reminder time options"""
    return {
        "options": [
            {"value": "none", "label": "Keine Erinnerung"},
            {"value": "at_time", "label": "Zur Terminzeit"},
            {"value": "5_min", "label": "5 Minuten vorher"},
            {"value": "15_min", "label": "15 Minuten vorher"},
            {"value": "30_min", "label": "30 Minuten vorher"},
            {"value": "1_hour", "label": "1 Stunde vorher"},
            {"value": "2_hours", "label": "2 Stunden vorher"},
            {"value": "1_day", "label": "1 Tag vorher"},
            {"value": "2_days", "label": "2 Tage vorher"},
            {"value": "1_week", "label": "1 Woche vorher"},
            {"value": "2_weeks", "label": "2 Wochen vorher"}
        ]
    }


@router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, user: dict = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())
    
    # Get reminder settings
    reminder_enabled = getattr(event_data, 'reminder_enabled', False)
    reminder_type = getattr(event_data, 'reminder_type', 'none')
    reminder_minutes = REMINDER_OPTIONS.get(reminder_type)
    reminder_channels = getattr(event_data, 'reminder_channels', ['app'])  # Future: ['app', 'email', 'whatsapp']
    
    new_event = {
        "id": event_id,
        "user_id": user["id"],
        "title": event_data.title,
        "description": event_data.description,
        "start_time": event_data.start_time.isoformat() if event_data.start_time else None,
        "end_time": event_data.end_time.isoformat() if event_data.end_time else None,
        "all_day": event_data.all_day if hasattr(event_data, 'all_day') else False,
        "location": event_data.location if hasattr(event_data, 'location') else None,
        "case_id": event_data.case_id,
        "reminder_enabled": reminder_enabled,
        "reminder_type": reminder_type,
        "reminder_minutes": reminder_minutes,
        "reminder_channels": reminder_channels,
        "reminder_sent": False,
        "created_at": now,
        "updated_at": now
    }
    await db.events.insert_one(new_event)
    await log_action(user["id"], "create_event", "event", event_id)

    # Create reminder record if enabled
    if reminder_enabled and reminder_minutes is not None and event_data.start_time:
        reminder_time = event_data.start_time - timedelta(minutes=reminder_minutes)
        reminder_id = str(uuid.uuid4())
        reminder = {
            "id": reminder_id,
            "user_id": user["id"],
            "event_id": event_id,
            "title": f"Erinnerung: {event_data.title}",
            "reminder_time": reminder_time.isoformat(),
            "channels": reminder_channels,
            "sent": False,
            "sent_at": None,
            "created_at": now
        }
        await db.reminders.insert_one(reminder)
        new_event["reminder_id"] = reminder_id

    # Auto-create task if requested
    create_task = getattr(event_data, 'create_task', False)
    if create_task:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "user_id": user["id"],
            "title": event_data.title,
            "description": f"Termin: {event_data.description or event_data.title}",
            "status": "todo",
            "priority": "medium",
            "due_date": event_data.start_time.isoformat() if event_data.start_time else None,
            "case_id": event_data.case_id,
            "event_id": event_id,
            "created_at": now,
            "updated_at": now
        }
        await db.tasks.insert_one(task)
        new_event["task_id"] = task_id

    return new_event


@router.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventCreate, user: dict = Depends(require_auth)):
    event = await db.events.find_one({"id": event_id, "user_id": user["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if event_data.title is not None:
        update_data["title"] = event_data.title
    if event_data.description is not None:
        update_data["description"] = event_data.description
    if event_data.start_time is not None:
        update_data["start_time"] = event_data.start_time.isoformat()
    if event_data.end_time is not None:
        update_data["end_time"] = event_data.end_time.isoformat()
    if event_data.case_id is not None:
        update_data["case_id"] = event_data.case_id
    if hasattr(event_data, 'location') and event_data.location is not None:
        update_data["location"] = event_data.location
    
    await db.events.update_one({"id": event_id}, {"$set": update_data})
    await log_action(user["id"], "update_event", "event", event_id)
    
    updated = await db.events.find_one({"id": event_id}, {"_id": 0})
    return updated


@router.delete("/events/{event_id}")
async def delete_event(event_id: str, user: dict = Depends(require_auth)):
    result = await db.events.delete_one({"id": event_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await log_action(user["id"], "delete_event", "event", event_id)
    return {"success": True, "message": "Event deleted"}


async def create_events_from_deadlines(user_id: str, deadlines: list, source_name: str, case_id: str = None, document_id: str = None):
    """Auto-create calendar events from detected deadlines"""
    created = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for deadline in deadlines:
        try:
            deadline_date = None
            deadline_desc = ""
            
            if isinstance(deadline, dict):
                deadline_date = deadline.get("datum")
                deadline_desc = deadline.get("beschreibung", "")
            elif isinstance(deadline, str):
                deadline_desc = deadline
                # Try to parse date from string
                import re
                date_match = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{2,4})', deadline)
                if date_match:
                    d, m, y = date_match.groups()
                    if len(y) == 2:
                        y = "20" + y
                    deadline_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            
            if not deadline_date:
                continue
            
            # Check for duplicate
            existing = await db.events.find_one({
                "user_id": user_id,
                "start_date": deadline_date,
                "source": "auto_deadline",
                "source_id": document_id
            })
            if existing:
                continue
            
            event_id = str(uuid.uuid4())
            event = {
                "id": event_id,
                "user_id": user_id,
                "title": f"Frist: {deadline_desc or source_name}",
                "description": f"Automatisch erkannt aus: {source_name}",
                "start_time": f"{deadline_date}T09:00:00",
                "end_time": f"{deadline_date}T09:30:00",
                "all_day": True,
                "case_id": case_id,
                "source": "auto_deadline",
                "source_id": document_id,
                "created_at": now,
                "updated_at": now
            }
            await db.events.insert_one(event)
            created += 1
        except Exception:
            continue
    
    return created
