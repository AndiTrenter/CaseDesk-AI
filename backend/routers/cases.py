"""Cases Router"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List
import uuid

from deps import db, require_auth, log_action
from models import Case, CaseCreate, CaseStatus

router = APIRouter()


@router.get("/cases", response_model=List[Case])
async def list_cases(
    status: str = None,
    user: dict = Depends(require_auth)
):
    query = {"user_id": user["id"]}
    if status:
        query["status"] = status
    cases = await db.cases.find(query, {"_id": 0}).sort("updated_at", -1).to_list(1000)
    return [Case(**c) for c in cases]


@router.post("/cases", response_model=Case)
async def create_case(case_data: CaseCreate, user: dict = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    case_id = str(uuid.uuid4())
    
    new_case = {
        "id": case_id,
        "user_id": user["id"],
        "title": case_data.title,
        "description": case_data.description,
        "status": CaseStatus.OPEN,
        "reference_number": case_data.reference_number,
        "tags": case_data.tags or [],
        "document_ids": [],
        "email_ids": [],
        "created_at": now,
        "updated_at": now
    }
    await db.cases.insert_one(new_case)
    await log_action(user["id"], "create_case", "case", case_id)
    return Case(**new_case)


@router.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str, user: dict = Depends(require_auth)):
    case = await db.cases.find_one({"id": case_id, "user_id": user["id"]}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return Case(**case)


@router.put("/cases/{case_id}", response_model=Case)
async def update_case(case_id: str, case_data: CaseCreate, user: dict = Depends(require_auth)):
    case = await db.cases.find_one({"id": case_id, "user_id": user["id"]})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    update_data = {
        "title": case_data.title,
        "description": case_data.description,
        "reference_number": case_data.reference_number,
        "tags": case_data.tags or [],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if case_data.status:
        update_data["status"] = case_data.status
    
    await db.cases.update_one({"id": case_id}, {"$set": update_data})
    await log_action(user["id"], "update_case", "case", case_id)
    
    updated = await db.cases.find_one({"id": case_id}, {"_id": 0})
    return Case(**updated)


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str, user: dict = Depends(require_auth)):
    result = await db.cases.delete_one({"id": case_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")
    
    await db.documents.update_many({"case_id": case_id, "user_id": user["id"]}, {"$set": {"case_id": None}})
    await log_action(user["id"], "delete_case", "case", case_id)
    return {"success": True, "message": "Case deleted"}


@router.get("/cases/{case_id}/documents")
async def get_case_documents(case_id: str, user: dict = Depends(require_auth)):
    documents = await db.documents.find(
        {"case_id": case_id, "user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    return documents


@router.get("/cases/{case_id}/history")
async def get_case_history(case_id: str, user: dict = Depends(require_auth)):
    correspondence = await db.correspondence.find(
        {"case_id": case_id, "user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    audit_logs = await db.audit_logs.find(
        {"resource_id": case_id, "user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"correspondence": correspondence, "audit_logs": audit_logs}
