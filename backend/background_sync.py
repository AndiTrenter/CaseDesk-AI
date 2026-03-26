"""
CaseDesk AI - Background Services
1. Email Sync: Periodically fetches emails for all active accounts
2. Auto Document Import: Imports email attachments as documents with OCR and AI analysis
3. Nightly Optimization: Runs at 2 AM, removes duplicate AI facts and optimizes data
"""
import asyncio
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NightlyOptimizer:
    """Background service that runs at 2 AM daily to clean up duplicate data"""

    def __init__(self, db):
        self.db = db
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info("Nightly optimizer scheduled (runs at 02:00)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _schedule_loop(self):
        """Check every 60s if it's time to run (02:00)"""
        last_run_date = None
        while self._running:
            try:
                now = datetime.now()
                today = now.strftime("%Y-%m-%d")

                if now.hour == 2 and now.minute < 2 and last_run_date != today:
                    logger.info("Starting nightly optimization...")
                    await self._run_optimization()
                    last_run_date = today
                    logger.info("Nightly optimization complete")
            except Exception as e:
                logger.error(f"Nightly optimization error: {e}")

            await asyncio.sleep(60)

    async def _run_optimization(self):
        """Main optimization: deduplicate AI facts for all users"""
        profiles = await self.db.ai_profiles.find({}, {"_id": 0}).to_list(1000)
        total_removed = 0

        for profile in profiles:
            facts = profile.get("facts", [])
            if len(facts) < 2:
                continue

            seen = set()
            unique_facts = []
            duplicates_removed = 0

            for fact in facts:
                # Normalize key+value for comparison
                key = (fact.get("key", "").strip().lower(), fact.get("value", "").strip().lower())
                if key not in seen:
                    seen.add(key)
                    unique_facts.append(fact)
                else:
                    duplicates_removed += 1

            if duplicates_removed > 0:
                await self.db.ai_profiles.update_one(
                    {"user_id": profile["user_id"]},
                    {"$set": {
                        "facts": unique_facts,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                total_removed += duplicates_removed
                logger.info(f"User {profile['user_id'][:8]}...: removed {duplicates_removed} duplicate facts")

        if total_removed > 0:
            logger.info(f"Nightly optimization: removed {total_removed} total duplicate facts")
        else:
            logger.info("Nightly optimization: no duplicates found")

        # Log the optimization run
        await self.db.system_logs.insert_one({
            "type": "nightly_optimization",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duplicates_removed": total_removed,
            "profiles_checked": len(profiles)
        })


class BackgroundEmailSync:
    """Background service for automatic email synchronization"""
    
    def __init__(self, db):
        self.db = db
        self._running = False
        self._task = None
    
    async def start(self):
        """Start the background sync loop"""
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("Background email sync started")
    
    async def stop(self):
        """Stop the background sync loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Background email sync stopped")
    
    async def _sync_loop(self):
        """Main sync loop - runs every 60 seconds, checks which accounts need syncing"""
        while self._running:
            try:
                await self._check_and_sync()
            except Exception as e:
                logger.error(f"Background sync error: {e}")
            
            await asyncio.sleep(60)
    
    async def _check_and_sync(self):
        """Check all accounts and sync those that need it"""
        accounts = await self.db.mail_accounts.find(
            {"is_active": True, "auto_sync": True},
            {"_id": 0}
        ).to_list(100)
        
        now = datetime.now(timezone.utc)
        
        for account in accounts:
            try:
                interval_minutes = account.get("sync_interval", 5)
                last_sync = account.get("last_sync")
                
                should_sync = False
                if not last_sync:
                    should_sync = True
                else:
                    try:
                        last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        elapsed = (now - last_sync_dt).total_seconds() / 60
                        should_sync = elapsed >= interval_minutes
                    except (ValueError, TypeError):
                        should_sync = True
                
                if should_sync:
                    await self._sync_account(account)
            except Exception as e:
                logger.error(f"Error syncing account {account.get('email')}: {e}")
    
    async def _sync_account(self, account):
        """Sync a single mail account with full document processing pipeline"""
        from email_service import EmailService
        
        email_service = EmailService(self.db)
        user_id = account["user_id"]
        
        logger.info(f"Auto-syncing email: {account.get('email')}")
        
        result = await email_service.fetch_emails(
            account["id"], user_id, limit=20, mark_as_read=True
        )
        
        if result.get("success") and result.get("fetched_count", 0) > 0:
            try:
                from ai_service import get_ai_service
                ai_service = await get_ai_service(self.db)
                
                for fetched_email in result.get("emails", []):
                    try:
                        # 1. Process email with AI (summary, deadlines)
                        process_result = await email_service.process_email_with_ai(
                            fetched_email["id"], user_id, ai_service
                        )
                        
                        # 2. Auto-import attachments as documents
                        await self._auto_import_attachments(
                            email_service, fetched_email, user_id, ai_service
                        )
                        
                        if process_result.get("success"):
                            import uuid
                            now_str = datetime.now(timezone.utc).isoformat()
                            
                            for deadline in process_result.get("deadlines", []):
                                task = {
                                    "id": str(uuid.uuid4()),
                                    "user_id": user_id,
                                    "case_id": fetched_email.get("case_id"),
                                    "title": f"Frist: {deadline.get('beschreibung', deadline) if isinstance(deadline, dict) else deadline}",
                                    "description": f"Auto-erkannt aus E-Mail: {fetched_email.get('subject', '')}",
                                    "priority": "high",
                                    "status": "open",
                                    "due_date": deadline.get("datum") if isinstance(deadline, dict) else None,
                                    "source": "email_auto_sync",
                                    "source_id": fetched_email["id"],
                                    "created_at": now_str,
                                    "updated_at": now_str
                                }
                                await self.db.tasks.insert_one(task)
                            
                            from routers.events import create_events_from_deadlines
                            await create_events_from_deadlines(
                                user_id, process_result.get("deadlines", []),
                                fetched_email.get("subject", "E-Mail"),
                                fetched_email.get("case_id"),
                                fetched_email["id"]
                            )
                    except Exception as e:
                        logger.error(f"Error processing auto-synced email: {e}")
                
                logger.info(f"Auto-synced {result.get('fetched_count', 0)} emails for {account.get('email')}")
            except Exception as e:
                logger.error(f"AI processing error during auto-sync: {e}")
    
    async def _auto_import_attachments(self, email_service, email_data, user_id, ai_service):
        """
        Automatically import email attachments as documents with OCR and AI analysis.
        This enables the full workflow: Scanner → Email → CaseDesk → AI Knowledge
        """
        attachments = email_data.get("attachments", [])
        if not attachments:
            return
        
        email_id = email_data.get("id")
        email_subject = email_data.get("subject", "E-Mail-Anhang")
        
        # Supported file types for auto-import
        SUPPORTED_TYPES = {
            # Documents
            '.pdf': 'document',
            '.doc': 'document',
            '.docx': 'document',
            '.txt': 'document',
            '.rtf': 'document',
            # Images (can contain scanned documents)
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.tiff': 'image',
            '.tif': 'image',
            '.bmp': 'image',
            # Spreadsheets
            '.xls': 'spreadsheet',
            '.xlsx': 'spreadsheet',
            '.csv': 'spreadsheet',
        }
        
        for attachment in attachments:
            try:
                # Skip if already imported
                if attachment.get("document_id"):
                    continue
                
                filename = attachment.get("filename", "")
                file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                
                # Check if file type is supported
                if file_ext not in SUPPORTED_TYPES:
                    logger.debug(f"Skipping unsupported attachment type: {filename}")
                    continue
                
                doc_type = SUPPORTED_TYPES[file_ext]
                
                # Import attachment as document
                import_result = await email_service.import_attachment_as_document(
                    email_id, attachment["id"], user_id, email_data.get("case_id")
                )
                
                if not import_result.get("success"):
                    logger.warning(f"Failed to import attachment: {filename}")
                    continue
                
                doc_id = import_result.get("document_id")
                logger.info(f"Auto-imported attachment as document: {filename} (ID: {doc_id})")
                
                # Run OCR for PDFs and images
                if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']:
                    await self._process_document_ocr(doc_id, user_id)
                
                # Run AI analysis on the document
                await self._analyze_document_with_ai(doc_id, user_id, ai_service)
                
            except Exception as e:
                logger.error(f"Error auto-importing attachment {attachment.get('filename')}: {e}")
    
    async def _process_document_ocr(self, doc_id: str, user_id: str):
        """Run OCR on a document to extract text"""
        try:
            document = await self.db.documents.find_one({"id": doc_id, "user_id": user_id})
            if not document:
                return
            
            storage_path = document.get("storage_path")
            if not storage_path or not os.path.exists(storage_path):
                logger.warning(f"Document file not found: {storage_path}")
                return
            
            mime_type = document.get("mime_type", "")
            ocr_text = ""
            
            # PDF extraction
            if mime_type == "application/pdf" or storage_path.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    with open(storage_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                ocr_text += text + "\n"
                    
                    # If no text extracted (scanned PDF), try OCR
                    if not ocr_text.strip():
                        ocr_text = await self._run_tesseract_ocr(storage_path, is_pdf=True)
                        
                except Exception as e:
                    logger.error(f"PDF extraction error: {e}")
                    ocr_text = await self._run_tesseract_ocr(storage_path, is_pdf=True)
            
            # Image OCR
            elif mime_type.startswith("image/") or any(storage_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']):
                ocr_text = await self._run_tesseract_ocr(storage_path, is_pdf=False)
            
            # Update document with OCR text
            if ocr_text.strip():
                await self.db.documents.update_one(
                    {"id": doc_id},
                    {"$set": {
                        "ocr_text": ocr_text,
                        "ocr_processed": True,
                        "ocr_processed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.info(f"OCR completed for document {doc_id}: {len(ocr_text)} characters")
            else:
                await self.db.documents.update_one(
                    {"id": doc_id},
                    {"$set": {"ocr_processed": True, "ocr_text": ""}}
                )
                
        except Exception as e:
            logger.error(f"OCR processing error for document {doc_id}: {e}")
    
    async def _run_tesseract_ocr(self, file_path: str, is_pdf: bool = False) -> str:
        """Run Tesseract OCR on a file"""
        try:
            import subprocess
            import tempfile
            
            if is_pdf:
                # Convert PDF to images first using pdftoppm
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Convert PDF pages to images
                    subprocess.run([
                        "pdftoppm", "-png", "-r", "300", file_path, f"{tmpdir}/page"
                    ], check=True, capture_output=True)
                    
                    # OCR each page
                    ocr_text = ""
                    import glob
                    for img_path in sorted(glob.glob(f"{tmpdir}/page*.png")):
                        result = subprocess.run([
                            "tesseract", img_path, "stdout", "-l", "deu+eng"
                        ], capture_output=True, text=True)
                        if result.returncode == 0:
                            ocr_text += result.stdout + "\n"
                    
                    return ocr_text
            else:
                # Direct image OCR
                result = subprocess.run([
                    "tesseract", file_path, "stdout", "-l", "deu+eng"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.error(f"Tesseract error: {result.stderr}")
                    return ""
                    
        except FileNotFoundError:
            logger.warning("Tesseract not installed - OCR skipped")
            return ""
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""
    
    async def _analyze_document_with_ai(self, doc_id: str, user_id: str, ai_service):
        """Analyze document with AI and add to knowledge base"""
        try:
            document = await self.db.documents.find_one({"id": doc_id, "user_id": user_id})
            if not document:
                return
            
            # Get text content (OCR text or original)
            content = document.get("ocr_text", "")
            if not content:
                logger.debug(f"No text content for AI analysis in document {doc_id}")
                return
            
            # Limit content length for AI
            content = content[:8000]
            
            from ai_service import DocumentAnalyzer
            analyzer = DocumentAnalyzer(ai_service)
            
            filename = document.get("filename", "Dokument")
            analysis = await analyzer.analyze_document(content, filename)
            
            if analysis.get("success"):
                metadata = analysis.get("metadata", {})
                
                update_data = {
                    "ai_analyzed": True,
                    "ai_analyzed_at": datetime.now(timezone.utc).isoformat(),
                    "ai_summary": metadata.get("zusammenfassung"),
                    "ai_document_type": metadata.get("dokumenttyp"),
                    "ai_keywords": metadata.get("schlagworte", []),
                    "detected_deadlines": metadata.get("fristen", []),
                    "tags": list(set(document.get("tags", []) + metadata.get("tags", []))),
                }
                
                # Auto-assign document type if detected
                if metadata.get("dokumenttyp"):
                    doc_type_mapping = {
                        "rechnung": "invoice",
                        "vertrag": "contract",
                        "brief": "letter",
                        "bescheid": "official",
                        "antrag": "application",
                        "urteil": "judgment",
                        "mahnung": "reminder",
                    }
                    detected_type = metadata.get("dokumenttyp", "").lower()
                    for key, value in doc_type_mapping.items():
                        if key in detected_type:
                            update_data["document_type"] = value
                            break
                
                await self.db.documents.update_one(
                    {"id": doc_id},
                    {"$set": update_data}
                )
                
                # Add important facts to AI knowledge base
                await self._add_to_knowledge_base(user_id, document, metadata)
                
                logger.info(f"AI analysis completed for document {doc_id}")
                
                # Create tasks from detected deadlines
                for deadline in metadata.get("fristen", []):
                    try:
                        import uuid as uuid_module
                        now_str = datetime.now(timezone.utc).isoformat()
                        task = {
                            "id": str(uuid_module.uuid4()),
                            "user_id": user_id,
                            "case_id": document.get("case_id"),
                            "title": f"Frist: {deadline.get('beschreibung', deadline) if isinstance(deadline, dict) else deadline}",
                            "description": f"Auto-erkannt aus Dokument: {filename}",
                            "priority": "high",
                            "status": "open",
                            "due_date": deadline.get("datum") if isinstance(deadline, dict) else None,
                            "source": "document_auto_import",
                            "source_id": doc_id,
                            "created_at": now_str,
                            "updated_at": now_str
                        }
                        await self.db.tasks.insert_one(task)
                    except Exception as e:
                        logger.error(f"Error creating task from deadline: {e}")
                        
        except Exception as e:
            logger.error(f"AI analysis error for document {doc_id}: {e}")
    
    async def _add_to_knowledge_base(self, user_id: str, document: dict, metadata: dict):
        """Add important document information to AI knowledge base"""
        try:
            # Get or create AI profile for user
            profile = await self.db.ai_profiles.find_one({"user_id": user_id})
            if not profile:
                profile = {
                    "user_id": user_id,
                    "facts": [],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await self.db.ai_profiles.insert_one(profile)
            
            facts = profile.get("facts", [])
            filename = document.get("filename", "Unbekanntes Dokument")
            doc_id = document.get("id")
            
            # Add document summary as fact
            if metadata.get("zusammenfassung"):
                facts.append({
                    "key": f"Dokument: {filename}",
                    "value": metadata.get("zusammenfassung"),
                    "source": "auto_import",
                    "document_id": doc_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            # Add important detected information
            for keyword in metadata.get("schlagworte", [])[:5]:
                facts.append({
                    "key": f"Schlagwort aus {filename}",
                    "value": keyword,
                    "source": "auto_import",
                    "document_id": doc_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            # Update profile with new facts
            await self.db.ai_profiles.update_one(
                {"user_id": user_id},
                {"$set": {"facts": facts, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}")
