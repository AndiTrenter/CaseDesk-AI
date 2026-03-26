"""Emails & Mail Accounts Router"""
from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging
import imaplib
import smtplib
import ssl

from deps import db, require_auth, log_action

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Mail Accounts ====================

@router.post("/mail/accounts/test-connection")
async def test_mail_connection(
    email: str = Form(...),
    imap_server: str = Form(...),
    imap_port: int = Form(993),
    password: str = Form(...),
    smtp_server: str = Form(None),
    smtp_port: int = Form(587),
    user: dict = Depends(require_auth)
):
    """Test IMAP and SMTP connection before saving"""
    results = {
        "imap": {"success": False, "message": ""},
        "smtp": {"success": False, "message": ""}
    }
    
    # Test IMAP connection
    try:
        context = ssl.create_default_context()
        if imap_port == 993:
            imap = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
        else:
            imap = imaplib.IMAP4(imap_server, imap_port)
            imap.starttls(ssl_context=context)
        
        imap.login(email, password)
        imap.select('INBOX')
        imap.logout()
        results["imap"] = {"success": True, "message": "IMAP-Verbindung erfolgreich"}
    except imaplib.IMAP4.error as e:
        results["imap"] = {"success": False, "message": f"IMAP-Authentifizierung fehlgeschlagen: {str(e)}"}
    except Exception as e:
        results["imap"] = {"success": False, "message": f"IMAP-Verbindungsfehler: {str(e)}"}
    
    # Test SMTP connection if server provided
    if smtp_server:
        try:
            context = ssl.create_default_context()
            if smtp_port == 465:
                smtp = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
            else:
                smtp = smtplib.SMTP(smtp_server, smtp_port)
                smtp.starttls(context=context)
            
            smtp.login(email, password)
            smtp.quit()
            results["smtp"] = {"success": True, "message": "SMTP-Verbindung erfolgreich"}
        except smtplib.SMTPAuthenticationError as e:
            results["smtp"] = {"success": False, "message": f"SMTP-Authentifizierung fehlgeschlagen: {str(e)}"}
        except Exception as e:
            results["smtp"] = {"success": False, "message": f"SMTP-Verbindungsfehler: {str(e)}"}
    else:
        results["smtp"] = {"success": True, "message": "Kein SMTP-Server angegeben (nur Empfang)"}
    
    overall_success = results["imap"]["success"] and results["smtp"]["success"]
    return {
        "success": overall_success,
        "results": results,
        "message": "Verbindungstest erfolgreich" if overall_success else "Verbindungstest fehlgeschlagen"
    }


@router.get("/mail/accounts")
async def list_mail_accounts(user: dict = Depends(require_auth)):
    accounts = await db.mail_accounts.find(
        {"user_id": user["id"]}, {"_id": 0, "password": 0}
    ).to_list(100)
    return accounts


@router.post("/mail/accounts")
async def create_mail_account(
    email: str = Form(...),
    display_name: str = Form(...),
    imap_server: str = Form(...),
    imap_port: int = Form(993),
    imap_use_ssl: bool = Form(True),
    password: str = Form(...),
    smtp_server: str = Form(None),
    smtp_port: int = Form(587),
    auto_sync: bool = Form(True),
    sync_interval: int = Form(5),
    user: dict = Depends(require_auth)
):
    account_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    account = {
        "id": account_id,
        "user_id": user["id"],
        "email": email,
        "display_name": display_name,
        "imap_server": imap_server,
        "imap_port": imap_port,
        "imap_use_ssl": imap_use_ssl,
        "password": password,
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "smtp_use_tls": True,
        "is_active": True,
        "auto_sync": auto_sync,
        "sync_interval": sync_interval,
        "last_sync": None,
        "created_at": now
    }
    
    try:
        await db.mail_accounts.insert_one(account)
        await log_action(user["id"], "create_mail_account", "mail_account", account_id)
        
        account.pop("password")
        account.pop("_id", None)  # Remove MongoDB _id if present
        return {"success": True, "account": account}
    except Exception as e:
        logger.error(f"Failed to create mail account: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern: {str(e)}")


@router.put("/mail/accounts/{account_id}")
async def update_mail_account(
    account_id: str,
    display_name: str = Form(None),
    imap_server: str = Form(None),
    imap_port: int = Form(None),
    smtp_server: str = Form(None),
    smtp_port: int = Form(None),
    password: str = Form(None),
    auto_sync: bool = Form(None),
    sync_interval: int = Form(None),
    is_active: bool = Form(None),
    user: dict = Depends(require_auth)
):
    """Update mail account settings"""
    account = await db.mail_accounts.find_one({"id": account_id, "user_id": user["id"]})
    if not account:
        raise HTTPException(status_code=404, detail="Mail account not found")
    
    update_data = {}
    if display_name is not None:
        update_data["display_name"] = display_name
    if imap_server is not None:
        update_data["imap_server"] = imap_server
    if imap_port is not None:
        update_data["imap_port"] = imap_port
    if smtp_server is not None:
        update_data["smtp_server"] = smtp_server
    if smtp_port is not None:
        update_data["smtp_port"] = smtp_port
    if password is not None and password.strip():
        update_data["password"] = password
    if auto_sync is not None:
        update_data["auto_sync"] = auto_sync
    if sync_interval is not None:
        update_data["sync_interval"] = sync_interval
    if is_active is not None:
        update_data["is_active"] = is_active
    
    if update_data:
        await db.mail_accounts.update_one({"id": account_id}, {"$set": update_data})
        await log_action(user["id"], "update_mail_account", "mail_account", account_id)
    
    # Return updated account (without password)
    updated = await db.mail_accounts.find_one({"id": account_id}, {"_id": 0, "password": 0})
    return {"success": True, "account": updated}


@router.delete("/mail/accounts/{account_id}")
async def delete_mail_account(account_id: str, user: dict = Depends(require_auth)):
    result = await db.mail_accounts.delete_one({"id": account_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mail account not found")
    
    await log_action(user["id"], "delete_mail_account", "mail_account", account_id)
    return {"success": True, "message": "Mail account deleted"}


# ==================== Email Operations ====================

@router.get("/emails")
async def list_emails(
    case_id: Optional[str] = None,
    unread_only: bool = False,
    user: dict = Depends(require_auth)
):
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    if unread_only:
        query["is_read"] = False
    
    emails = await db.emails.find(query, {"_id": 0}).sort("received_at", -1).to_list(500)
    return emails


@router.get("/emails/{email_id}")
async def get_email(email_id: str, user: dict = Depends(require_auth)):
    email_doc = await db.emails.find_one(
        {"id": email_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if not email_doc.get("is_read"):
        await db.emails.update_one({"id": email_id}, {"$set": {"is_read": True}})
    
    return email_doc


@router.post("/emails/fetch/{account_id}")
async def fetch_emails(account_id: str, user: dict = Depends(require_auth)):
    from email_service import EmailService
    from ai_service import get_ai_service
    
    email_service = EmailService(db)
    result = await email_service.fetch_emails(account_id, user["id"])
    
    if result.get("success") and result.get("fetched_count", 0) > 0:
        ai_service = await get_ai_service(db)
        processed = 0
        tasks_created = 0
        events_created = 0
        
        for fetched_email in result.get("emails", []):
            try:
                process_result = await email_service.process_email_with_ai(
                    fetched_email["id"], user["id"], ai_service
                )
                if process_result.get("success"):
                    processed += 1
                    
                    for deadline in process_result.get("deadlines", []):
                        task_id = str(uuid.uuid4())
                        now = datetime.now(timezone.utc).isoformat()
                        task = {
                            "id": task_id,
                            "user_id": user["id"],
                            "case_id": fetched_email.get("case_id"),
                            "title": f"Frist: {deadline.get('beschreibung', deadline) if isinstance(deadline, dict) else deadline}",
                            "description": f"Erkannt aus E-Mail: {fetched_email.get('subject', '')}",
                            "priority": "high",
                            "status": "open",
                            "due_date": deadline.get("datum") if isinstance(deadline, dict) else None,
                            "source": "email_ai",
                            "source_id": fetched_email["id"],
                            "created_at": now,
                            "updated_at": now
                        }
                        await db.tasks.insert_one(task)
                        tasks_created += 1
                    
                    from routers.events import create_events_from_deadlines
                    ec = await create_events_from_deadlines(
                        user["id"], process_result.get("deadlines", []),
                        fetched_email.get("subject", "E-Mail"),
                        fetched_email.get("case_id"),
                        fetched_email["id"]
                    )
                    events_created += ec
            except Exception as e:
                logger.error(f"Error auto-processing email: {e}")
        
        result["processed_count"] = processed
        result["tasks_created"] = tasks_created
        result["events_created"] = events_created
        
        await log_action(user["id"], "fetch_emails", "mail_account", account_id,
                        {"fetched_count": result.get("fetched_count", 0), "processed": processed})
    
    return result


@router.post("/emails/{email_id}/process")
async def process_email(email_id: str, user: dict = Depends(require_auth)):
    from email_service import EmailService
    from ai_service import get_ai_service
    
    email_service = EmailService(db)
    ai_service = await get_ai_service(db)
    return await email_service.process_email_with_ai(email_id, user["id"], ai_service)


@router.post("/emails/{email_id}/link")
async def link_email_to_case(
    email_id: str,
    case_id: str = Form(...),
    user: dict = Depends(require_auth)
):
    from email_service import EmailService
    email_service = EmailService(db)
    result = await email_service.link_email_to_case(email_id, case_id, user["id"])
    if result.get("success"):
        await log_action(user["id"], "link_email", "email", email_id, {"case_id": case_id})
    return result


@router.post("/emails/{email_id}/import-attachment/{attachment_id}")
async def import_attachment(
    email_id: str,
    attachment_id: str,
    case_id: str = Form(None),
    user: dict = Depends(require_auth)
):
    from email_service import EmailService
    email_service = EmailService(db)
    result = await email_service.import_attachment_as_document(
        email_id, attachment_id, user["id"], case_id
    )
    if result.get("success"):
        await log_action(user["id"], "import_attachment", "document", result.get("document_id"))
    return result


@router.delete("/emails/{email_id}")
async def delete_email(email_id: str, user: dict = Depends(require_auth)):
    result = await db.emails.delete_one({"id": email_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Email not found")
    await log_action(user["id"], "delete_email", "email", email_id)
    return {"success": True, "message": "Email deleted"}
