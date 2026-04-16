"""
CaseDesk AI - Email Service
IMAP email fetching, processing, and integration
"""
import os
import email
import imaplib
import asyncio
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import logging
import uuid
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', './uploads'))


class EmailService:
    """IMAP Email fetching and processing service"""
    
    def __init__(self, db):
        self.db = db
    
    async def fetch_emails(
        self, 
        mail_account_id: str, 
        user_id: str,
        limit: int = 50,
        mark_as_read: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch unread emails from IMAP server
        
        Args:
            mail_account_id: Mail account ID
            user_id: User ID
            limit: Max emails to fetch
            mark_as_read: Mark fetched emails as read
            
        Returns:
            Dict with fetched emails and stats
        """
        # Get mail account
        account = await self.db.mail_accounts.find_one(
            {"id": mail_account_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not account:
            return {"success": False, "error": "Mail account not found"}
        
        if not account.get("is_active"):
            return {"success": False, "error": "Mail account is not active"}
        
        try:
            # Connect to IMAP server
            if account.get("imap_use_ssl", True):
                mail = imaplib.IMAP4_SSL(account["imap_server"], account["imap_port"])
            else:
                mail = imaplib.IMAP4(account["imap_server"], account["imap_port"])
            
            # Login
            mail.login(account["email"], account["password"])
            
            # Select inbox
            mail.select("INBOX")
            
            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")
            
            if status != "OK":
                return {"success": False, "error": "Failed to search emails"}
            
            email_ids = messages[0].split()
            email_ids = email_ids[-limit:]  # Get last N emails
            
            fetched_emails = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    
                    if status != "OK":
                        continue
                    
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Parse email
                    parsed = await self._parse_email(email_message, user_id, mail_account_id)
                    
                    if parsed:
                        # Save to database
                        await self.db.emails.insert_one(parsed)
                        fetched_emails.append(parsed)
                        
                        # Mark as read if requested
                        if mark_as_read:
                            mail.store(email_id, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            # Update last sync time
            await self.db.mail_accounts.update_one(
                {"id": mail_account_id},
                {"$set": {"last_sync": datetime.now(timezone.utc).isoformat()}}
            )
            
            mail.logout()
            
            return {
                "success": True,
                "fetched_count": len(fetched_emails),
                "emails": fetched_emails
            }
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error: {e}")
            return {"success": False, "error": f"IMAP error: {str(e)}"}
        except Exception as e:
            logger.error(f"Email fetch error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _parse_email(
        self, 
        email_message, 
        user_id: str, 
        mail_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Parse email message and extract data"""
        try:
            # Get subject
            subject = ""
            raw_subject = email_message.get("Subject", "")
            if raw_subject:
                decoded = decode_header(raw_subject)
                subject = ""
                for part, encoding in decoded:
                    if isinstance(part, bytes):
                        subject += part.decode(encoding or "utf-8", errors="ignore")
                    else:
                        subject += part
            
            # Get sender
            sender = email_message.get("From", "")
            
            # Get recipients
            recipients = []
            to_header = email_message.get("To", "")
            if to_header:
                recipients = [addr.strip() for addr in to_header.split(",")]
            
            # Get CC
            cc = []
            cc_header = email_message.get("Cc", "")
            if cc_header:
                cc = [addr.strip() for addr in cc_header.split(",")]
            
            # Get date
            date_str = email_message.get("Date", "")
            try:
                received_at = parsedate_to_datetime(date_str).isoformat()
            except:
                received_at = datetime.now(timezone.utc).isoformat()
            
            # Get message ID
            message_id = email_message.get("Message-ID", str(uuid.uuid4()))
            
            # Check if already exists
            existing = await self.db.emails.find_one({"message_id": message_id, "user_id": user_id})
            if existing:
                return None
            
            # Get body
            body_text = ""
            body_html = ""
            attachments = []
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    if "attachment" in content_disposition:
                        # Handle attachment
                        filename = part.get_filename()
                        if filename:
                            decoded_filename = decode_header(filename)
                            if decoded_filename[0][1]:
                                filename = decoded_filename[0][0].decode(decoded_filename[0][1])
                            elif isinstance(decoded_filename[0][0], bytes):
                                filename = decoded_filename[0][0].decode("utf-8", errors="ignore")
                            
                            attachment = await self._save_attachment(
                                part.get_payload(decode=True),
                                filename,
                                content_type,
                                user_id
                            )
                            if attachment:
                                attachments.append(attachment)
                    
                    elif content_type == "text/plain" and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_text = payload.decode(charset, errors="ignore")
                    
                    elif content_type == "text/html" and not body_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_html = payload.decode(charset, errors="ignore")
            else:
                content_type = email_message.get_content_type()
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or "utf-8"
                    if content_type == "text/html":
                        body_html = payload.decode(charset, errors="ignore")
                    else:
                        body_text = payload.decode(charset, errors="ignore")
            
            email_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            return {
                "id": email_id,
                "user_id": user_id,
                "mail_account_id": mail_account_id,
                "message_id": message_id,
                "subject": subject,
                "sender": sender,
                "recipients": recipients,
                "cc": cc,
                "body_text": body_text,
                "body_html": body_html,
                "received_at": received_at,
                "case_id": None,
                "attachment_ids": [a["id"] for a in attachments],
                "attachments": attachments,
                "is_read": False,
                "is_processed": False,
                "ai_summary": None,
                "detected_deadlines": [],
                "created_at": now
            }
            
        except Exception as e:
            logger.error(f"Email parse error: {e}")
            return None
    
    async def _save_attachment(
        self, 
        content: bytes, 
        filename: str, 
        content_type: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Save email attachment to disk"""
        try:
            attachment_id = str(uuid.uuid4())
            file_ext = Path(filename).suffix or ".bin"
            storage_filename = f"{attachment_id}{file_ext}"
            storage_path = UPLOAD_DIR / user_id / "attachments" / storage_filename
            
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(storage_path, 'wb') as f:
                await f.write(content)
            
            return {
                "id": attachment_id,
                "filename": filename,
                "mime_type": content_type,
                "size": len(content),
                "storage_path": str(storage_path)
            }
            
        except Exception as e:
            logger.error(f"Attachment save error: {e}")
            return None
    
    async def process_email_with_ai(
        self, 
        email_id: str, 
        user_id: str,
        ai_service
    ) -> Dict[str, Any]:
        """Process email with AI for summary and deadline detection"""
        from ai_service import DocumentAnalyzer
        
        email_doc = await self.db.emails.find_one(
            {"id": email_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not email_doc:
            return {"success": False, "error": "Email not found"}
        
        # Prepare content for analysis
        content = f"""
Betreff: {email_doc.get('subject', '')}
Von: {email_doc.get('sender', '')}
Datum: {email_doc.get('received_at', '')}

Inhalt:
{email_doc.get('body_text', '')[:3000]}
"""
        
        analyzer = DocumentAnalyzer(ai_service)
        
        try:
            analysis = await analyzer.analyze_document(content, f"Email: {email_doc.get('subject', '')}")
            
            if analysis.get("success"):
                metadata = analysis.get("metadata", {})
                
                update_data = {
                    "is_processed": True,
                    "ai_summary": metadata.get("zusammenfassung"),
                    "detected_deadlines": metadata.get("fristen", []),
                    "tags": metadata.get("tags", []),
                    "importance": metadata.get("wichtigkeit", "mittel")
                }
                
                await self.db.emails.update_one(
                    {"id": email_id},
                    {"$set": update_data}
                )
                
                return {
                    "success": True,
                    "summary": metadata.get("zusammenfassung"),
                    "deadlines": metadata.get("fristen", []),
                    "tags": metadata.get("tags", [])
                }
            else:
                return {"success": False, "error": analysis.get("error")}
                
        except Exception as e:
            logger.error(f"Email AI processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def link_email_to_case(
        self, 
        email_id: str, 
        case_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Link email to a case"""
        # Verify email exists
        email_doc = await self.db.emails.find_one(
            {"id": email_id, "user_id": user_id}
        )
        if not email_doc:
            return {"success": False, "error": "Email not found"}
        
        # Verify case exists
        case = await self.db.cases.find_one(
            {"id": case_id, "user_id": user_id}
        )
        if not case:
            return {"success": False, "error": "Case not found"}
        
        # Update email
        await self.db.emails.update_one(
            {"id": email_id},
            {"$set": {"case_id": case_id}}
        )
        
        # Add to case
        await self.db.cases.update_one(
            {"id": case_id},
            {"$addToSet": {"email_ids": email_id}}
        )
        
        return {"success": True}
    
    async def import_attachment_as_document(
        self, 
        email_id: str, 
        attachment_id: str, 
        user_id: str,
        case_id: str = None
    ) -> Dict[str, Any]:
        """Import email attachment as a document"""
        email_doc = await self.db.emails.find_one(
            {"id": email_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not email_doc:
            return {"success": False, "error": "Email not found"}
        
        attachment = None
        for att in email_doc.get("attachments", []):
            if att["id"] == attachment_id:
                attachment = att
                break
        
        if not attachment:
            return {"success": False, "error": "Attachment not found"}
        
        # Create document record
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        document = {
            "id": doc_id,
            "user_id": user_id,
            "case_id": case_id or email_doc.get("case_id"),
            "email_id": email_id,
            "filename": attachment["filename"],
            "original_filename": attachment["filename"],
            "display_name": attachment["filename"],
            "mime_type": attachment["mime_type"],
            "size": attachment["size"],
            "storage_path": attachment["storage_path"],
            "document_type": "other",
            "ocr_text": "",
            "ocr_processed": False,
            "ai_analyzed": False,
            "tags": [],
            "metadata": {"source": "email", "email_subject": email_doc.get("subject")},
            "created_at": now,
            "updated_at": now
        }
        
        await self.db.documents.insert_one(document)
        
        # Update attachment reference
        await self.db.emails.update_one(
            {"id": email_id, "attachments.id": attachment_id},
            {"$set": {"attachments.$.document_id": doc_id}}
        )
        
        return {"success": True, "document_id": doc_id, "document": document}
