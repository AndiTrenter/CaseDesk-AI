"""
CaseDesk AI - Background Email Sync Service
Periodically fetches emails for all active accounts with auto_sync enabled
"""
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


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
        """Sync a single mail account"""
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
                        process_result = await email_service.process_email_with_ai(
                            fetched_email["id"], user_id, ai_service
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
