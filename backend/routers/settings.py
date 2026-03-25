"""Settings, Dashboard, Export & Healthcheck Router"""
from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from typing import Optional
import os
import json
import zipfile
import tempfile
import logging
import shutil

from deps import db, require_auth, require_admin, log_action, OCR_SERVICE_URL
from models import CaseStatus, TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Healthcheck Dashboard ====================

@router.get("/admin/health")
async def admin_health_check(user: dict = Depends(require_admin)):
    """Comprehensive health check for all services"""
    import httpx

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }

    # MongoDB
    try:
        info = await db.command("ping")
        doc_count = await db.documents.count_documents({})
        user_count = await db.users.count_documents({})
        results["services"]["mongodb"] = {
            "status": "connected",
            "documents": doc_count,
            "users": user_count
        }
    except Exception as e:
        results["services"]["mongodb"] = {"status": "error", "error": str(e)}

    # OCR Service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OCR_SERVICE_URL}/health")
            results["services"]["ocr"] = {
                "status": "connected" if resp.status_code == 200 else "error",
                "url": OCR_SERVICE_URL
            }
    except Exception:
        results["services"]["ocr"] = {
            "status": "unavailable",
            "url": OCR_SERVICE_URL,
            "note": "Fallback-OCR (Tesseract) aktiv"
        }

    # AI Provider
    settings = await db.system_settings.find_one({}, {"_id": 0})
    ai_provider = os.environ.get("AI_PROVIDER") or (settings.get("ai_provider") if settings else "disabled")
    api_key = os.environ.get("OPENAI_API_KEY") or (settings.get("openai_api_key") if settings else None)

    if ai_provider == "openai":
        results["services"]["openai"] = {
            "status": "configured" if api_key else "no_api_key",
            "provider": "openai"
        }
    elif ai_provider == "ollama":
        ollama_url = os.environ.get("OLLAMA_URL", "http://ollama:11434")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{ollama_url}/api/tags")
                models = [m["name"] for m in resp.json().get("models", [])] if resp.status_code == 200 else []
                results["services"]["ollama"] = {
                    "status": "connected",
                    "url": ollama_url,
                    "models": models
                }
        except Exception:
            results["services"]["ollama"] = {"status": "unavailable", "url": ollama_url}
    else:
        results["services"]["ai"] = {"status": "disabled"}

    # Email Sync
    mail_accounts = await db.mail_accounts.count_documents({})
    results["services"]["email_sync"] = {
        "status": "active" if mail_accounts > 0 else "no_accounts",
        "accounts": mail_accounts
    }

    # Storage
    try:
        upload_dir = os.environ.get("UPLOAD_DIR", "./uploads")
        total, used, free = shutil.disk_usage(upload_dir)
        results["services"]["storage"] = {
            "status": "ok",
            "total_gb": round(total / (1024**3), 1),
            "used_gb": round(used / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "usage_percent": round(used / total * 100, 1)
        }
    except Exception as e:
        results["services"]["storage"] = {"status": "error", "error": str(e)}

    # Tesseract OCR
    try:
        import subprocess
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=5)
        results["services"]["tesseract"] = {
            "status": "installed",
            "version": result.stdout.split("\n")[0] if result.returncode == 0 else "unknown"
        }
    except Exception:
        results["services"]["tesseract"] = {"status": "not_installed"}

    return results


# ==================== Settings ====================

@router.get("/settings/system")
async def get_system_settings(user: dict = Depends(require_admin)):
    settings = await db.system_settings.find_one({}, {"_id": 0})
    if settings and settings.get("openai_api_key"):
        settings["openai_api_key"] = "***configured***"
    return settings or {}


@router.put("/settings/system")
async def update_system_settings(
    ai_provider: str = Form(None),
    openai_api_key: str = Form(None),
    internet_access: str = Form(None),
    default_language: str = Form(None),
    user: dict = Depends(require_admin)
):
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if ai_provider is not None:
        update_data["ai_provider"] = ai_provider
        update_data["allow_external_ai"] = ai_provider == "openai"
    if openai_api_key is not None and openai_api_key != "***configured***":
        update_data["openai_api_key"] = openai_api_key if openai_api_key else None
    if internet_access is not None:
        update_data["internet_access"] = internet_access
    if default_language is not None:
        update_data["default_language"] = default_language
    
    await db.system_settings.update_one({}, {"$set": update_data})
    await log_action(user["id"], "update_settings", "system")
    return {"success": True, "message": "Settings updated"}


# ==================== Storage Limits Settings ====================

# Default storage limits (in bytes)
DEFAULT_STORAGE_LIMITS = {
    "max_single_file_mb": 100,           # 100 MB per file
    "max_email_attachment_mb": 50,       # 50 MB per email attachment
    "max_total_storage_gb": 100,         # 100 GB total uploads
    "max_user_storage_gb": 10,           # 10 GB per user (default)
    "max_database_gb": 50,               # 50 GB database
    "max_ollama_models_gb": 50,          # 50 GB for AI models
}


@router.get("/settings/storage")
async def get_storage_settings(user: dict = Depends(require_admin)):
    """Get global storage limit settings"""
    settings = await db.system_settings.find_one({}, {"_id": 0})
    storage_limits = settings.get("storage_limits", DEFAULT_STORAGE_LIMITS) if settings else DEFAULT_STORAGE_LIMITS
    
    # Get current usage
    upload_dir = os.environ.get("UPLOAD_DIR", "./uploads")
    try:
        total, used, free = shutil.disk_usage(upload_dir)
        disk_info = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round(used / total * 100, 1)
        }
    except:
        disk_info = {"error": "Could not read disk info"}
    
    # Get per-user storage usage
    users = await db.users.find({}, {"_id": 0, "id": 1, "email": 1, "username": 1}).to_list(1000)
    user_storage = []
    for u in users:
        docs = await db.documents.find({"user_id": u["id"]}, {"_id": 0, "size": 1}).to_list(100000)
        total_size = sum(d.get("size", 0) for d in docs)
        user_storage.append({
            "user_id": u["id"],
            "email": u.get("email"),
            "username": u.get("username"),
            "storage_used_mb": round(total_size / (1024**2), 2),
            "document_count": len(docs)
        })
    
    return {
        "limits": storage_limits,
        "disk": disk_info,
        "user_storage": user_storage
    }


@router.put("/settings/storage")
async def update_storage_settings(
    max_single_file_mb: int = Form(None),
    max_email_attachment_mb: int = Form(None),
    max_total_storage_gb: int = Form(None),
    max_user_storage_gb: int = Form(None),
    max_database_gb: int = Form(None),
    max_ollama_models_gb: int = Form(None),
    user: dict = Depends(require_admin)
):
    """Update global storage limit settings"""
    settings = await db.system_settings.find_one({}, {"_id": 0})
    current_limits = settings.get("storage_limits", DEFAULT_STORAGE_LIMITS) if settings else DEFAULT_STORAGE_LIMITS
    
    if max_single_file_mb is not None:
        current_limits["max_single_file_mb"] = max_single_file_mb
    if max_email_attachment_mb is not None:
        current_limits["max_email_attachment_mb"] = max_email_attachment_mb
    if max_total_storage_gb is not None:
        current_limits["max_total_storage_gb"] = max_total_storage_gb
    if max_user_storage_gb is not None:
        current_limits["max_user_storage_gb"] = max_user_storage_gb
    if max_database_gb is not None:
        current_limits["max_database_gb"] = max_database_gb
    if max_ollama_models_gb is not None:
        current_limits["max_ollama_models_gb"] = max_ollama_models_gb
    
    await db.system_settings.update_one(
        {}, 
        {"$set": {"storage_limits": current_limits, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    await log_action(user["id"], "update_storage_settings", "system")
    return {"success": True, "limits": current_limits}


@router.get("/settings/storage/user/{user_id}")
async def get_user_storage_limit(user_id: str, user: dict = Depends(require_admin)):
    """Get storage limit for a specific user"""
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_settings = await db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
    custom_limit = user_settings.get("storage_limit_gb") if user_settings else None
    
    # Get global default
    settings = await db.system_settings.find_one({}, {"_id": 0})
    global_limit = settings.get("storage_limits", DEFAULT_STORAGE_LIMITS).get("max_user_storage_gb", 10) if settings else 10
    
    # Calculate current usage
    docs = await db.documents.find({"user_id": user_id}, {"_id": 0, "size": 1}).to_list(100000)
    total_size = sum(d.get("size", 0) for d in docs)
    
    return {
        "user_id": user_id,
        "email": target_user.get("email"),
        "global_limit_gb": global_limit,
        "custom_limit_gb": custom_limit,
        "effective_limit_gb": custom_limit if custom_limit else global_limit,
        "storage_used_mb": round(total_size / (1024**2), 2),
        "storage_used_gb": round(total_size / (1024**3), 4),
        "document_count": len(docs)
    }


@router.put("/settings/storage/user/{user_id}")
async def set_user_storage_limit(
    user_id: str,
    storage_limit_gb: int = Form(...),
    user: dict = Depends(require_admin)
):
    """Set custom storage limit for a specific user"""
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.user_settings.update_one(
        {"user_id": user_id},
        {"$set": {"storage_limit_gb": storage_limit_gb}},
        upsert=True
    )
    await log_action(user["id"], "set_user_storage_limit", "user", user_id, {"limit_gb": storage_limit_gb})
    return {"success": True, "user_id": user_id, "storage_limit_gb": storage_limit_gb}


@router.delete("/settings/storage/user/{user_id}")
async def reset_user_storage_limit(user_id: str, user: dict = Depends(require_admin)):
    """Reset user storage limit to global default"""
    await db.user_settings.update_one(
        {"user_id": user_id},
        {"$unset": {"storage_limit_gb": ""}}
    )
    await log_action(user["id"], "reset_user_storage_limit", "user", user_id)
    return {"success": True, "message": "User storage limit reset to global default"}


@router.get("/settings/user")
async def get_user_settings(user: dict = Depends(require_auth)):
    settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return settings or {"user_id": user["id"], "language": "de", "theme": "dark"}


@router.put("/settings/user")
async def update_user_settings(
    language: str = Form(None),
    theme: str = Form(None),
    notifications_enabled: bool = Form(None),
    user: dict = Depends(require_auth)
):
    update_data = {}
    if language is not None:
        update_data["language"] = language
    if theme is not None:
        update_data["theme"] = theme
    if notifications_enabled is not None:
        update_data["notifications_enabled"] = notifications_enabled
    
    await db.user_settings.update_one(
        {"user_id": user["id"]},
        {"$set": update_data},
        upsert=True
    )
    
    if language is not None:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"language": language, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"success": True, "message": "Settings updated"}


# ==================== Dashboard ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(require_auth)):
    user_id = user["id"]
    
    cases_count = await db.cases.count_documents({"user_id": user_id})
    open_cases = await db.cases.count_documents({"user_id": user_id, "status": CaseStatus.OPEN})
    documents_count = await db.documents.count_documents({"user_id": user_id})
    pending_tasks = await db.tasks.count_documents({"user_id": user_id, "status": {"$ne": TaskStatus.DONE}})
    emails_count = await db.emails.count_documents({"user_id": user_id})
    
    upcoming_events = await db.events.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("start_time", 1).limit(5).to_list(5)
    
    recent_documents = await db.documents.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    urgent_tasks = await db.tasks.find(
        {"user_id": user_id, "status": {"$ne": TaskStatus.DONE}}, {"_id": 0}
    ).sort("due_date", 1).limit(5).to_list(5)
    
    recent_emails = await db.emails.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("received_at", -1).limit(5).to_list(5)
    
    return {
        "cases": {"total": cases_count, "open": open_cases},
        "documents": {"total": documents_count},
        "tasks": {"pending": pending_tasks},
        "emails": {"total": emails_count},
        "upcoming_events": upcoming_events,
        "recent_documents": recent_documents,
        "urgent_tasks": urgent_tasks,
        "recent_emails": recent_emails
    }


# ==================== Data Export ====================

@router.get("/export/all")
async def export_all_data(user: dict = Depends(require_auth)):
    user_id = user["id"]
    
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": user["id"], "email": user.get("email"), "username": user.get("username"), "full_name": user.get("full_name")},
        "cases": await db.cases.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "tasks": await db.tasks.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "events": await db.events.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "drafts": await db.drafts.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "emails": await db.emails.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "correspondence": await db.correspondence.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    }
    
    docs = await db.documents.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    export_data["documents"] = [{k: v for k, v in d.items() if k != "ocr_text"} for d in docs]
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"casedesk_export_{user_id[:8]}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("export_data.json", json.dumps(export_data, indent=2, ensure_ascii=False, default=str))
        for doc in docs:
            if doc.get("storage_path") and os.path.exists(doc["storage_path"]):
                filename = doc.get("display_name", doc.get("original_filename", doc["id"]))
                zipf.write(doc["storage_path"], f"documents/{filename}")
    
    await log_action(user_id, "export_data", "user", user_id)
    return FileResponse(zip_path, media_type="application/zip", filename=f"casedesk_export_{user_id[:8]}.zip")


@router.get("/export/case/{case_id}")
async def export_case(case_id: str, user: dict = Depends(require_auth)):
    user_id = user["id"]
    case = await db.cases.find_one({"id": case_id, "user_id": user_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "case": case,
        "documents": await db.documents.find({"case_id": case_id, "user_id": user_id}, {"_id": 0, "ocr_text": 0}).to_list(1000),
        "tasks": await db.tasks.find({"case_id": case_id, "user_id": user_id}, {"_id": 0}).to_list(1000),
        "emails": await db.emails.find({"case_id": case_id, "user_id": user_id}, {"_id": 0}).to_list(1000),
        "events": await db.events.find({"case_id": case_id, "user_id": user_id}, {"_id": 0}).to_list(1000)
    }
