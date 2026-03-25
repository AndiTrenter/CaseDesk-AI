"""
CaseDesk AI - Background Services
1. Email Sync: Periodically fetches emails for all active accounts
2. Nightly Optimization: Runs at 2 AM, removes duplicate AI facts and optimizes data
"""
import asyncio
import logging
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
