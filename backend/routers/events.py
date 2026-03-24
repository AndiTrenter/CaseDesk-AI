"""Events Router with deadline automation"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List
import uuid

from deps import db, require_auth, log_action
from models import Event, EventCreate

router = APIRouter()


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


@router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, user: dict = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())
    
    new_event = {
        "id": event_id,
        "user_id": user["id"],
        "title": event_data.title,
        "description": event_data.description,
        "start_date": event_data.start_date,
        "start_time": event_data.start_time,
        "end_date": event_data.end_date,
        "end_time": event_data.end_time,
        "all_day": event_data.all_day if hasattr(event_data, 'all_day') else False,
        "case_id": event_data.case_id,
        "created_at": now,
        "updated_at": now
    }
    await db.events.insert_one(new_event)
    await log_action(user["id"], "create_event", "event", event_id)
    return Event(**new_event)


@router.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventCreate, user: dict = Depends(require_auth)):
    event = await db.events.find_one({"id": event_id, "user_id": user["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ["title", "description", "start_date", "start_time", "end_date", "end_time", "case_id"]:
        val = getattr(event_data, field, None)
        if val is not None:
            update_data[field] = val
    
    await db.events.update_one({"id": event_id}, {"$set": update_data})
    await log_action(user["id"], "update_event", "event", event_id)
    
    updated = await db.events.find_one({"id": event_id}, {"_id": 0})
    return Event(**updated)


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
                "start_date": deadline_date,
                "start_time": "09:00",
                "end_date": deadline_date,
                "end_time": "09:30",
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
