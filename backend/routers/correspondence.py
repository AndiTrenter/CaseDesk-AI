"""Correspondence & Response Generation Router"""
from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from typing import Optional
import json
import logging

from deps import db, require_auth, log_action
from models import Draft, DraftCreate

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Drafts ====================

@router.get("/drafts")
async def list_drafts(
    case_id: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    drafts = await db.drafts.find(query, {"_id": 0}).sort("updated_at", -1).to_list(100)
    return drafts


@router.post("/drafts")
async def create_draft(draft_data: DraftCreate, user: dict = Depends(require_auth)):
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    draft_id = str(uuid.uuid4())
    
    new_draft = {
        "id": draft_id,
        "user_id": user["id"],
        "title": draft_data.title,
        "content": draft_data.content,
        "case_id": draft_data.case_id,
        "created_at": now,
        "updated_at": now
    }
    await db.drafts.insert_one(new_draft)
    await log_action(user["id"], "create_draft", "draft", draft_id)
    return Draft(**new_draft)


@router.put("/drafts/{draft_id}")
async def update_draft(draft_id: str, draft_data: DraftCreate, user: dict = Depends(require_auth)):
    draft = await db.drafts.find_one({"id": draft_id, "user_id": user["id"]})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if draft_data.title is not None:
        update_data["title"] = draft_data.title
    if draft_data.content is not None:
        update_data["content"] = draft_data.content
    
    await db.drafts.update_one({"id": draft_id}, {"$set": update_data})
    await log_action(user["id"], "update_draft", "draft", draft_id)
    updated = await db.drafts.find_one({"id": draft_id}, {"_id": 0})
    return Draft(**updated)


@router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str, user: dict = Depends(require_auth)):
    result = await db.drafts.delete_one({"id": draft_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Draft not found")
    await log_action(user["id"], "delete_draft", "draft", draft_id)
    return {"success": True, "message": "Draft deleted"}


# ==================== Response Generation ====================

@router.get("/cases/{case_id}/analyze")
async def analyze_case(case_id: str, user: dict = Depends(require_auth)):
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    return await response_service.analyze_case_requirements(case_id, user["id"])


@router.post("/cases/{case_id}/generate-response")
async def generate_case_response(
    case_id: str,
    response_type: str = Form(...),
    recipient: str = Form(...),
    subject: str = Form(...),
    instructions: str = Form(None),
    document_ids: str = Form(None),
    output_format: str = Form("pdf"),
    user: dict = Depends(require_auth)
):
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    doc_ids = json.loads(document_ids) if document_ids else []
    
    result = await response_service.generate_response(
        case_id=case_id, user_id=user["id"],
        response_type=response_type, recipient=recipient, subject=subject,
        instructions=instructions, include_document_ids=doc_ids,
        output_format=output_format if output_format in ("pdf", "docx") else "pdf"
    )
    
    if result.get("success"):
        await log_action(user["id"], "generate_response", "correspondence",
                        result.get("correspondence_id"), {"case_id": case_id, "type": response_type})
    return result


# ==================== Correspondence ====================

@router.get("/correspondence")
async def list_correspondence(case_id: Optional[str] = None, user: dict = Depends(require_auth)):
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    return await db.correspondence.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.get("/correspondence/{correspondence_id}")
async def get_correspondence(correspondence_id: str, user: dict = Depends(require_auth)):
    corr = await db.correspondence.find_one(
        {"id": correspondence_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not corr:
        raise HTTPException(status_code=404, detail="Correspondence not found")
    return corr


@router.put("/correspondence/{correspondence_id}")
async def update_correspondence(
    correspondence_id: str,
    content: str = Form(None),
    subject: str = Form(None),
    status: str = Form(None),
    user: dict = Depends(require_auth)
):
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    result = await response_service.update_correspondence(correspondence_id, user["id"], content, subject, status)
    if result.get("success"):
        await log_action(user["id"], "update_correspondence", "correspondence", correspondence_id)
    return result


@router.delete("/correspondence/{correspondence_id}")
async def delete_correspondence(correspondence_id: str, user: dict = Depends(require_auth)):
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    result = await response_service.delete_correspondence(correspondence_id, user["id"])
    if result.get("success"):
        await log_action(user["id"], "delete_correspondence", "correspondence", correspondence_id)
    return result


@router.get("/correspondence/{correspondence_id}/download")
async def download_correspondence_package(correspondence_id: str, user: dict = Depends(require_auth)):
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    result = await response_service.create_download_package(correspondence_id, user["id"])
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    await log_action(user["id"], "download_package", "correspondence", correspondence_id)
    return FileResponse(result["zip_path"], filename=result["filename"], media_type="application/zip")


@router.post("/correspondence/{correspondence_id}/send")
async def send_correspondence(
    correspondence_id: str,
    mail_account_id: str = Form(...),
    recipient_email: str = Form(...),
    user: dict = Depends(require_auth)
):
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    result = await response_service.send_via_email(
        correspondence_id, user["id"], mail_account_id, recipient_email
    )
    if result.get("success"):
        await log_action(user["id"], "send_correspondence", "correspondence",
                        correspondence_id, {"recipient": recipient_email})
    return result
