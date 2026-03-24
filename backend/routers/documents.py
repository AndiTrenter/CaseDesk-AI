"""Documents Router"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
import uuid
import os
import json
import httpx
import aiofiles
import logging
import io

from deps import db, require_auth, log_action, UPLOAD_DIR, OCR_SERVICE_URL
from models import Document

logger = logging.getLogger(__name__)
router = APIRouter()


def extract_text_from_pdf(content: bytes) -> str:
    """Fallback: Extract text directly from PDF, with OCR for scanned pages"""
    text_parts = []

    # First try: Extract embedded text with PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_parts.append(page_text)
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")

    # If we got text from embedded text, return it
    if text_parts and sum(len(t) for t in text_parts) > 50:
        return "\n".join(text_parts)

    # Second try: OCR scanned pages with tesseract
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(content, dpi=300)
        ocr_parts = []
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img, lang='deu+eng')
            if page_text and page_text.strip():
                ocr_parts.append(page_text)
        if ocr_parts:
            return "\n".join(ocr_parts)
    except Exception as e:
        logger.warning(f"Tesseract OCR fallback failed: {e}")

    return "\n".join(text_parts)


async def try_ocr_or_fallback(filename: str, content: bytes, mime_type: str) -> str:
    """Try OCR service first, fall back to direct PDF text extraction"""
    ocr_text = ""

    # Try OCR service
    if mime_type in ["application/pdf", "image/png", "image/jpeg", "image/tiff"]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                ocr_response = await client.post(
                    f"{OCR_SERVICE_URL}/ocr",
                    files={"file": (filename, content, mime_type)}
                )
                if ocr_response.status_code == 200:
                    ocr_data = ocr_response.json()
                    ocr_text = ocr_data.get("text", "")
        except Exception as e:
            logger.warning(f"OCR service unavailable: {e}")

    # Fallback: direct PDF text extraction
    if not ocr_text and mime_type == "application/pdf":
        logger.info("Using fallback PDF text extraction")
        ocr_text = extract_text_from_pdf(content)

    return ocr_text


@router.get("/documents")
async def list_documents(
    case_id: Optional[str] = None,
    search: Optional[str] = None,
    document_type: Optional[str] = None,
    unassigned: Optional[bool] = None,
    user: dict = Depends(require_auth)
):
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    if document_type:
        query["document_type"] = document_type
    if unassigned:
        query["case_id"] = None
    
    if search:
        try:
            text_results = await db.documents.find(
                {"$text": {"$search": search}, "user_id": user["id"]},
                {"_id": 0, "score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).to_list(100)
            
            if text_results:
                return text_results
        except Exception:
            pass
        
        query["$or"] = [
            {"display_name": {"$regex": search, "$options": "i"}},
            {"original_filename": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
            {"ai_summary": {"$regex": search, "$options": "i"}}
        ]
    
    documents = await db.documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return documents


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    case_id: str = Form(None),
    document_type: str = Form("other"),
    user: dict = Depends(require_auth)
):
    now = datetime.now(timezone.utc).isoformat()
    doc_id = str(uuid.uuid4())
    
    user_upload_dir = UPLOAD_DIR / user["id"]
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix
    storage_filename = f"{doc_id}{file_ext}"
    storage_path = user_upload_dir / storage_filename
    
    content = await file.read()
    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(content)
    
    document = {
        "id": doc_id,
        "user_id": user["id"],
        "case_id": case_id,
        "filename": file.filename,
        "original_filename": file.filename,
        "display_name": file.filename,
        "storage_path": str(storage_path),
        "mime_type": file.content_type or "application/octet-stream",
        "size": len(content),
        "document_type": document_type,
        "ocr_text": None,
        "ocr_processed": False,
        "ai_analyzed": False,
        "tags": [],
        "metadata": {},
        "created_at": now,
        "updated_at": now
    }
    
    await db.documents.insert_one(document)
    
    if case_id:
        await db.cases.update_one(
            {"id": case_id, "user_id": user["id"]},
            {"$addToSet": {"document_ids": doc_id}}
        )
    
    await log_action(user["id"], "upload_document", "document", doc_id, {"filename": file.filename})
    
    # Background AI processing
    try:
        ocr_text = await try_ocr_or_fallback(file.filename, content, file.content_type)
        
        if ocr_text:
            from ai_service import get_ai_service, DocumentAnalyzer
            ai_service = await get_ai_service(db)
            analyzer = DocumentAnalyzer(ai_service)
            
            analysis = await analyzer.analyze_document(ocr_text, file.filename)
            
            if analysis.get("success"):
                metadata = analysis.get("metadata", {})
                new_display_name = analysis.get("new_filename", file.filename)
                
                update_data = {
                    "ocr_text": ocr_text,
                    "ocr_processed": True,
                    "ai_analyzed": True,
                    "display_name": new_display_name,
                    "document_type": metadata.get("dokumenttyp", document_type).lower().replace("ae", "ae").replace("oe", "oe").replace("ue", "ue"),
                    "tags": metadata.get("tags", []),
                    "ai_summary": metadata.get("zusammenfassung"),
                    "sender": metadata.get("absender"),
                    "importance": metadata.get("wichtigkeit", "mittel"),
                    "deadlines": metadata.get("fristen", []),
                    "metadata": metadata,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                if metadata.get("datum") and metadata["datum"] != "null":
                    try:
                        update_data["document_date"] = metadata["datum"]
                    except Exception:
                        pass
                
                await db.documents.update_one({"id": doc_id}, {"$set": update_data})
                document.update(update_data)
                
                # Create tasks AND calendar events for deadlines
                for deadline in metadata.get("fristen", []):
                    try:
                        task = {
                            "id": str(uuid.uuid4()),
                            "user_id": user["id"],
                            "title": f"Frist: {metadata.get('kurzthema', 'Dokument')}",
                            "description": f"Automatisch erkannte Frist aus: {new_display_name}",
                            "priority": "high",
                            "status": "todo",
                            "due_date": deadline if isinstance(deadline, str) else deadline.get("datum"),
                            "case_id": case_id,
                            "document_id": doc_id,
                            "source": "document_ai",
                            "created_at": now,
                            "updated_at": now
                        }
                        await db.tasks.insert_one(task)
                    except Exception:
                        pass
                
                # Auto-create calendar events from deadlines
                from routers.events import create_events_from_deadlines
                await create_events_from_deadlines(
                    user["id"], metadata.get("fristen", []),
                    new_display_name, case_id, doc_id
                )
            else:
                await db.documents.update_one(
                    {"id": doc_id},
                    {"$set": {"ocr_text": ocr_text, "ocr_processed": True, "updated_at": now}}
                )
    except Exception as e:
        logger.error(f"Document processing error: {e}")
    
    document.pop("_id", None)
    return {"success": True, "document": document}


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(document_id: str, user: dict = Depends(require_auth)):
    document = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    ocr_text = document.get("ocr_text")
    
    if not ocr_text and document.get("storage_path") and os.path.exists(document["storage_path"]):
        try:
            async with aiofiles.open(document["storage_path"], 'rb') as f:
                content = await f.read()
            
            ocr_text = await try_ocr_or_fallback(
                document["original_filename"], content, document["mime_type"]
            )
        except Exception as e:
            logger.warning(f"OCR reprocess error: {e}")
    
    if ocr_text:
        from ai_service import get_ai_service, DocumentAnalyzer
        ai_service = await get_ai_service(db)
        analyzer = DocumentAnalyzer(ai_service)
        
        analysis = await analyzer.analyze_document(ocr_text, document["original_filename"])
        
        if analysis.get("success"):
            metadata = analysis.get("metadata", {})
            new_display_name = analysis.get("new_filename", document["display_name"])
            
            update_data = {
                "ocr_text": ocr_text,
                "ocr_processed": True,
                "ai_analyzed": True,
                "display_name": new_display_name,
                "tags": metadata.get("tags", []),
                "ai_summary": metadata.get("zusammenfassung"),
                "sender": metadata.get("absender"),
                "deadlines": metadata.get("fristen", []),
                "metadata": metadata,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if metadata.get("datum") and metadata["datum"] != "null":
                update_data["document_date"] = metadata["datum"]
            
            await db.documents.update_one({"id": document_id}, {"$set": update_data})
            
            from routers.events import create_events_from_deadlines
            await create_events_from_deadlines(
                user["id"], metadata.get("fristen", []),
                new_display_name, document.get("case_id"), document_id
            )
            
            return {"success": True, "message": "Document reprocessed", "display_name": new_display_name}
    
    return {"success": False, "error": "No text to process"}


@router.post("/documents/{document_id}/ocr")
async def process_document_ocr(document_id: str, user: dict = Depends(require_auth)):
    document = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.get("storage_path", "")):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        async with aiofiles.open(document["storage_path"], 'rb') as f:
            content = await f.read()
        
        ocr_text = await try_ocr_or_fallback(
            document["original_filename"], content, document["mime_type"]
        )
        
        if ocr_text:
            await db.documents.update_one(
                {"id": document_id},
                {"$set": {"ocr_text": ocr_text, "ocr_processed": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return {"success": True, "ocr_text": ocr_text[:500]}
        else:
            return {"success": False, "error": "No text could be extracted"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str, user: dict = Depends(require_auth)):
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return Document(**document)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, user: dict = Depends(require_auth)):
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.get("storage_path") and os.path.exists(document["storage_path"]):
        os.remove(document["storage_path"])
    
    if document.get("case_id"):
        await db.cases.update_one(
            {"id": document["case_id"]},
            {"$pull": {"document_ids": document_id}}
        )
    
    await db.documents.delete_one({"id": document_id})
    await log_action(user["id"], "delete_document", "document", document_id)
    return {"success": True, "message": "Document deleted"}


@router.get("/documents/{document_id}/preview")
async def get_document_preview(document_id: str, user: dict = Depends(require_auth)):
    document = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document["id"],
        "display_name": document.get("display_name", document["original_filename"]),
        "mime_type": document["mime_type"],
        "size": document["size"],
        "ocr_text": document.get("ocr_text"),
        "ai_summary": document.get("ai_summary"),
        "tags": document.get("tags", []),
        "metadata": document.get("metadata", {}),
        "sender": document.get("sender"),
        "document_date": document.get("document_date"),
        "deadlines": document.get("deadlines", []),
        "importance": document.get("importance")
    }


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str, user: dict = Depends(require_auth)):
    document = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = document["storage_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        filename=document.get("display_name", document["original_filename"]),
        media_type=document["mime_type"]
    )


@router.get("/documents/{document_id}/auto-link")
async def auto_link_document(document_id: str, user: dict = Depends(require_auth)):
    from ai_service import get_ai_service, ProactiveAssistant
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    return await assistant.auto_link_documents(user["id"], document_id)


@router.put("/documents/{document_id}")
async def update_document(
    document_id: str,
    display_name: str = Form(None),
    document_type: str = Form(None),
    tags: str = Form(None),
    case_id: str = Form(None),
    user: dict = Depends(require_auth)
):
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if display_name is not None:
        update_data["display_name"] = display_name
    if document_type is not None:
        update_data["document_type"] = document_type
    if tags is not None:
        update_data["tags"] = json.loads(tags) if tags else []
    
    old_case_id = document.get("case_id")
    if case_id is not None and case_id != old_case_id:
        update_data["case_id"] = case_id if case_id else None
        if old_case_id:
            await db.cases.update_one({"id": old_case_id}, {"$pull": {"document_ids": document_id}})
        if case_id:
            await db.cases.update_one(
                {"id": case_id, "user_id": user["id"]},
                {"$addToSet": {"document_ids": document_id}}
            )
    
    await db.documents.update_one({"id": document_id}, {"$set": update_data})
    await log_action(user["id"], "update_document", "document", document_id)
    
    updated = await db.documents.find_one({"id": document_id}, {"_id": 0})
    return {"success": True, "document": updated}


@router.post("/documents/batch-reprocess")
async def batch_reprocess_documents(user: dict = Depends(require_auth)):
    """Reprocess all unprocessed documents using fallback text extraction + AI analysis"""
    unprocessed = await db.documents.find(
        {"user_id": user["id"], "ocr_processed": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)

    processed = 0
    errors = 0

    for doc in unprocessed:
        try:
            storage_path = doc.get("storage_path", "")
            if not storage_path or not os.path.exists(storage_path):
                continue

            async with aiofiles.open(storage_path, 'rb') as f:
                content = await f.read()

            ocr_text = await try_ocr_or_fallback(
                doc["original_filename"], content, doc["mime_type"]
            )

            if ocr_text:
                from ai_service import get_ai_service, DocumentAnalyzer
                ai_service = await get_ai_service(db)
                analyzer = DocumentAnalyzer(ai_service)
                analysis = await analyzer.analyze_document(ocr_text, doc["original_filename"])

                now = datetime.now(timezone.utc).isoformat()
                if analysis.get("success"):
                    metadata = analysis.get("metadata", {})
                    update_data = {
                        "ocr_text": ocr_text,
                        "ocr_processed": True,
                        "ai_analyzed": True,
                        "display_name": analysis.get("new_filename", doc["display_name"]),
                        "document_type": metadata.get("dokumenttyp", doc.get("document_type", "other")).lower(),
                        "tags": metadata.get("tags", []),
                        "ai_summary": metadata.get("zusammenfassung"),
                        "sender": metadata.get("absender"),
                        "importance": metadata.get("wichtigkeit", "mittel"),
                        "deadlines": metadata.get("fristen", []),
                        "metadata": metadata,
                        "updated_at": now
                    }
                    if metadata.get("datum") and metadata["datum"] != "null":
                        update_data["document_date"] = metadata["datum"]
                    await db.documents.update_one({"id": doc["id"]}, {"$set": update_data})
                else:
                    await db.documents.update_one(
                        {"id": doc["id"]},
                        {"$set": {"ocr_text": ocr_text, "ocr_processed": True, "updated_at": now}}
                    )
                processed += 1
            else:
                errors += 1
        except Exception as e:
            logger.error(f"Batch reprocess error for {doc['id']}: {e}")
            errors += 1

    return {"success": True, "processed": processed, "errors": errors, "total": len(unprocessed)}



@router.post("/documents/assign-case")
async def assign_documents_to_case(
    document_ids: str = Form(...),
    case_id: str = Form(...),
    user: dict = Depends(require_auth)
):
    doc_ids = json.loads(document_ids)
    
    case = await db.cases.find_one({"id": case_id, "user_id": user["id"]})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    updated = 0
    for doc_id in doc_ids:
        result = await db.documents.update_one(
            {"id": doc_id, "user_id": user["id"]},
            {"$set": {"case_id": case_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.modified_count:
            await db.cases.update_one({"id": case_id}, {"$addToSet": {"document_ids": doc_id}})
            updated += 1
    
    await log_action(user["id"], "assign_documents", "case", case_id, {"count": updated})
    return {"success": True, "updated": updated}
