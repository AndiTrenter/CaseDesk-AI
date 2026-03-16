"""
CaseDesk AI - Response Generator Service
AI-powered response generation with document bundling and email sending
"""
import os
import json
import smtplib
import zipfile
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import uuid
import aiofiles

logger = logging.getLogger(__name__)


class ResponseGeneratorService:
    """AI-powered response generation with document bundling"""
    
    def __init__(self, db, ai_service):
        self.db = db
        self.ai_service = ai_service
    
    async def analyze_case_requirements(self, case_id: str, user_id: str) -> Dict[str, Any]:
        """Analyze case and determine required documents and response type"""
        # Get case with all related data
        case = await self.db.cases.find_one(
            {"id": case_id, "user_id": user_id},
            {"_id": 0}
        )
        if not case:
            return {"success": False, "error": "Fall nicht gefunden"}
        
        # Get linked documents
        documents = await self.db.documents.find(
            {"case_id": case_id, "user_id": user_id},
            {"_id": 0}
        ).to_list(100)
        
        # Get linked emails
        emails = await self.db.emails.find(
            {"case_id": case_id, "user_id": user_id},
            {"_id": 0}
        ).to_list(100)
        
        # Get case history (correspondence)
        history = await self.db.correspondence.find(
            {"case_id": case_id, "user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        
        # Build context for AI
        context = f"""
FALL: {case.get('title')}
BESCHREIBUNG: {case.get('description', 'Keine')}
AKTENZEICHEN: {case.get('reference_number', 'Keines')}
STATUS: {case.get('status')}

VERKNÜPFTE DOKUMENTE ({len(documents)}):
"""
        for doc in documents:
            context += f"\n- {doc.get('display_name', doc.get('original_filename'))}"
            context += f"\n  Typ: {doc.get('document_type')}, Absender: {doc.get('sender', 'Unbekannt')}"
            if doc.get('ai_summary'):
                context += f"\n  Zusammenfassung: {doc.get('ai_summary')}"
            if doc.get('ocr_text'):
                context += f"\n  Inhalt (Auszug): {doc.get('ocr_text', '')[:500]}..."
        
        if emails:
            context += f"\n\nVERKNÜPFTE E-MAILS ({len(emails)}):"
            for email in emails[:5]:
                context += f"\n- {email.get('subject')} von {email.get('sender')}"
                if email.get('ai_summary'):
                    context += f"\n  Zusammenfassung: {email.get('ai_summary')}"
        
        if history:
            context += f"\n\nBISHERIGE KORRESPONDENZ ({len(history)}):"
            for h in history[:5]:
                context += f"\n- {h.get('created_at')[:10]}: {h.get('subject')}"
                context += f" ({h.get('status', 'erstellt')})"
        
        # AI analysis
        system_prompt = """Du bist ein Experte für Fallanalyse und Korrespondenz mit Behörden.
Analysiere den Fall und identifiziere:
1. Art der erforderlichen Antwort (z.B. Widerspruch, Antrag, Stellungnahme, Einspruch)
2. Welche Dokumente/Nachweise benötigt werden
3. Fristen die beachtet werden müssen
4. Empfohlene Vorgehensweise

Antworte NUR mit einem validen JSON:
{
    "antworttyp": "z.B. Widerspruch, Antrag, Stellungnahme",
    "empfaenger": "Name/Behörde an die geantwortet werden soll",
    "benoetigt_dokumente": ["Liste der benötigten Dokumente"],
    "verfuegbare_dokumente": ["Liste der bereits vorhandenen passenden Dokumente"],
    "fehlende_dokumente": ["Liste der noch zu beschaffenden Dokumente"],
    "fristen": ["Erkannte Fristen mit Datum"],
    "empfehlung": "Kurze Empfehlung zur Vorgehensweise",
    "dringlichkeit": "hoch/mittel/niedrig"
}"""

        prompt = f"""Analysiere diesen Fall und identifiziere die Anforderungen:

{context}

Was wird für eine angemessene Antwort benötigt?"""

        try:
            response = await self.ai_service.generate(prompt, system_prompt)
            
            # Parse JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group())
                return {
                    "success": True,
                    "case": case,
                    "documents": documents,
                    "emails": emails,
                    "history": history,
                    "analysis": analysis
                }
            else:
                return {
                    "success": True,
                    "case": case,
                    "documents": documents,
                    "emails": emails,
                    "history": history,
                    "analysis": {"raw_response": response}
                }
        except Exception as e:
            logger.error(f"Case analysis error: {e}")
            return {
                "success": True,
                "case": case,
                "documents": documents,
                "emails": emails,
                "history": history,
                "analysis": None,
                "error": str(e)
            }
    
    async def generate_response(
        self,
        case_id: str,
        user_id: str,
        response_type: str,
        recipient: str,
        subject: str,
        instructions: str = None,
        include_document_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete response package"""
        
        # Get case data
        case = await self.db.cases.find_one(
            {"id": case_id, "user_id": user_id},
            {"_id": 0}
        )
        if not case:
            return {"success": False, "error": "Fall nicht gefunden"}
        
        # Get user info
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        
        # Get selected documents
        documents = []
        if include_document_ids:
            documents = await self.db.documents.find(
                {"id": {"$in": include_document_ids}, "user_id": user_id},
                {"_id": 0}
            ).to_list(100)
        
        # Get all case documents for context
        all_case_docs = await self.db.documents.find(
            {"case_id": case_id, "user_id": user_id},
            {"_id": 0}
        ).to_list(100)
        
        # Build context
        context = f"""
FALL: {case.get('title')}
AKTENZEICHEN: {case.get('reference_number', 'nicht angegeben')}
BESCHREIBUNG: {case.get('description', '')}

ABSENDER (Nutzer):
Name: {user.get('full_name', user.get('username'))}
E-Mail: {user.get('email')}

EMPFÄNGER: {recipient}
BETREFF: {subject}
ART DES SCHREIBENS: {response_type}

VERFÜGBARE DOKUMENTE IM FALL:
"""
        for doc in all_case_docs:
            context += f"\n- {doc.get('display_name', doc.get('original_filename'))}"
            if doc.get('ai_summary'):
                context += f": {doc.get('ai_summary')}"
            if doc.get('ocr_text'):
                context += f"\n  Inhalt: {doc.get('ocr_text', '')[:300]}..."
        
        if include_document_ids:
            context += f"\n\nALS ANLAGE BEIZUFÜGEN:"
            for doc in documents:
                context += f"\n- {doc.get('display_name', doc.get('original_filename'))}"
        
        # Generate response
        system_prompt = """Du bist ein Experte für formelle Korrespondenz mit Behörden und Ämtern.
Erstelle ein professionelles, korrektes Antwortschreiben.

WICHTIGE REGELN:
- Schreibe formal und höflich
- Verwende das korrekte Format für offizielle Schreiben
- Beziehe dich auf vorhandene Aktenzeichen
- Erwähne beigefügte Anlagen
- NIEMALS falsche Angaben oder erfundene Fakten
- Nur auf Basis der vorhandenen Dokumente argumentieren
- Bei Unklarheiten im Schreiben darauf hinweisen

FORMAT:
- Absender oben rechts
- Empfänger links
- Datum
- Betreff mit Aktenzeichen
- Anrede
- Text
- Grußformel
- Unterschrift
- Anlagen-Verzeichnis"""

        prompt = f"""Erstelle ein {response_type} basierend auf folgendem Kontext:

{context}

ZUSÄTZLICHE ANWEISUNGEN: {instructions or 'Keine weiteren Anweisungen'}

Erstelle das vollständige Schreiben."""

        try:
            response_text = await self.ai_service.generate(prompt, system_prompt, max_tokens=3000)
            
            # Create correspondence record
            correspondence_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            correspondence = {
                "id": correspondence_id,
                "user_id": user_id,
                "case_id": case_id,
                "type": response_type,
                "subject": subject,
                "recipient": recipient,
                "content": response_text,
                "document_ids": include_document_ids or [],
                "status": "draft",
                "created_at": now,
                "updated_at": now,
                "sent_at": None,
                "sent_via": None
            }
            
            await self.db.correspondence.insert_one(correspondence)
            
            return {
                "success": True,
                "correspondence_id": correspondence_id,
                "content": response_text,
                "documents": documents,
                "case": case
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_download_package(
        self,
        correspondence_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Create a ZIP package with response letter and attachments"""
        
        # Get correspondence
        correspondence = await self.db.correspondence.find_one(
            {"id": correspondence_id, "user_id": user_id},
            {"_id": 0}
        )
        if not correspondence:
            return {"success": False, "error": "Korrespondenz nicht gefunden"}
        
        # Get attached documents
        documents = []
        if correspondence.get("document_ids"):
            documents = await self.db.documents.find(
                {"id": {"$in": correspondence["document_ids"]}, "user_id": user_id},
                {"_id": 0}
            ).to_list(100)
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"antwort_{correspondence_id[:8]}.zip")
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add response letter as text file
                letter_filename = f"Schreiben_{correspondence.get('subject', 'Antwort')[:30]}.txt"
                letter_filename = letter_filename.replace("/", "-").replace("\\", "-")
                zipf.writestr(letter_filename, correspondence.get("content", ""))
                
                # Add attached documents
                for i, doc in enumerate(documents, 1):
                    if os.path.exists(doc.get("storage_path", "")):
                        ext = Path(doc["storage_path"]).suffix
                        doc_filename = f"Anlage_{i}_{doc.get('display_name', doc.get('original_filename', 'dokument'))}"
                        if not doc_filename.endswith(ext):
                            doc_filename += ext
                        doc_filename = doc_filename.replace("/", "-").replace("\\", "-")
                        zipf.write(doc["storage_path"], doc_filename)
            
            return {
                "success": True,
                "zip_path": zip_path,
                "filename": f"antwort_{correspondence_id[:8]}.zip"
            }
            
        except Exception as e:
            logger.error(f"Package creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_via_email(
        self,
        correspondence_id: str,
        user_id: str,
        mail_account_id: str,
        recipient_email: str
    ) -> Dict[str, Any]:
        """Send correspondence via email with attachments"""
        
        # Get correspondence
        correspondence = await self.db.correspondence.find_one(
            {"id": correspondence_id, "user_id": user_id},
            {"_id": 0}
        )
        if not correspondence:
            return {"success": False, "error": "Korrespondenz nicht gefunden"}
        
        # Get mail account
        account = await self.db.mail_accounts.find_one(
            {"id": mail_account_id, "user_id": user_id},
            {"_id": 0}
        )
        if not account:
            return {"success": False, "error": "E-Mail-Konto nicht gefunden"}
        
        # Get attached documents
        documents = []
        if correspondence.get("document_ids"):
            documents = await self.db.documents.find(
                {"id": {"$in": correspondence["document_ids"]}, "user_id": user_id},
                {"_id": 0}
            ).to_list(100)
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = account['email']
            msg['To'] = recipient_email
            msg['Subject'] = correspondence.get('subject', 'Antwort')
            
            # Body
            msg.attach(MIMEText(correspondence.get('content', ''), 'plain', 'utf-8'))
            
            # Attachments
            for doc in documents:
                if os.path.exists(doc.get("storage_path", "")):
                    with open(doc["storage_path"], "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = doc.get('display_name', doc.get('original_filename', 'dokument'))
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
            
            # Send
            smtp_server = account.get('smtp_server', account.get('imap_server', '').replace('imap', 'smtp'))
            smtp_port = account.get('smtp_port', 587)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if account.get('smtp_use_tls', True):
                    server.starttls()
                server.login(account['email'], account['password'])
                server.send_message(msg)
            
            # Update correspondence status
            now = datetime.now(timezone.utc).isoformat()
            await self.db.correspondence.update_one(
                {"id": correspondence_id},
                {"$set": {
                    "status": "sent",
                    "sent_at": now,
                    "sent_via": "email",
                    "sent_to": recipient_email,
                    "updated_at": now
                }}
            )
            
            return {
                "success": True,
                "message": f"E-Mail erfolgreich an {recipient_email} gesendet"
            }
            
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "error": "SMTP-Authentifizierung fehlgeschlagen"}
        except smtplib.SMTPException as e:
            return {"success": False, "error": f"SMTP-Fehler: {str(e)}"}
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_case_correspondence_history(
        self,
        case_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all correspondence for a case"""
        history = await self.db.correspondence.find(
            {"case_id": case_id, "user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        return history
    
    async def update_correspondence(
        self,
        correspondence_id: str,
        user_id: str,
        content: str = None,
        subject: str = None,
        status: str = None
    ) -> Dict[str, Any]:
        """Update correspondence"""
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if content is not None:
            update_data["content"] = content
        if subject is not None:
            update_data["subject"] = subject
        if status is not None:
            update_data["status"] = status
        
        result = await self.db.correspondence.update_one(
            {"id": correspondence_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"success": True}
        return {"success": False, "error": "Nicht gefunden oder keine Änderungen"}
    
    async def delete_correspondence(
        self,
        correspondence_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Delete correspondence"""
        result = await self.db.correspondence.delete_one(
            {"id": correspondence_id, "user_id": user_id}
        )
        
        if result.deleted_count > 0:
            return {"success": True}
        return {"success": False, "error": "Nicht gefunden"}
