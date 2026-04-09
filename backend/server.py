"""
CaseDesk AI - Main FastAPI Application
Self-hosted document and case management with AI support
"""
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

from deps import db, client

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background sync instance
bg_sync = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global bg_sync
    
    logger.info("CaseDesk AI starting up...")
    
    # Ensure indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.cases.create_index("user_id")
    await db.documents.create_index("user_id")
    await db.documents.create_index([
        ("ocr_text", "text"),
        ("display_name", "text"),
        ("original_filename", "text"),
        ("tags", "text"),
        ("ai_summary", "text")
    ], default_language="german", name="document_fulltext")
    await db.tasks.create_index("user_id")
    await db.events.create_index("user_id")
    await db.emails.create_index("user_id")
    await db.chat_messages.create_index([("user_id", 1), ("session_id", 1)])
    await db.audit_logs.create_index("user_id")
    
    # Start background email sync
    from background_sync import BackgroundEmailSync, NightlyOptimizer
    bg_sync = BackgroundEmailSync(db)
    await bg_sync.start()
    nightly = NightlyOptimizer(db)
    await nightly.start()
    
    yield
    
    # Shutdown
    logger.info("CaseDesk AI shutting down...")
    if bg_sync:
        await bg_sync.stop()
    if nightly:
        await nightly.stop()
    client.close()


app = FastAPI(
    title="CaseDesk AI",
    description="Self-hosted document and case management with AI support",
    version="1.5.1",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
api_router = APIRouter(prefix="/api")

# Include all domain routers
from routers.auth import router as auth_router
from routers.cases import router as cases_router
from routers.documents import router as documents_router
from routers.tasks import router as tasks_router
from routers.events import router as events_router
from routers.ai import router as ai_router
from routers.emails import router as emails_router
from routers.settings import router as settings_router
from routers.correspondence import router as correspondence_router
from routers.system import router as system_router

api_router.include_router(auth_router, tags=["Auth & Users"])
api_router.include_router(cases_router, tags=["Cases"])
api_router.include_router(documents_router, tags=["Documents"])
api_router.include_router(tasks_router, tags=["Tasks"])
api_router.include_router(events_router, tags=["Events"])
api_router.include_router(ai_router, tags=["AI"])
api_router.include_router(emails_router, tags=["Emails"])
api_router.include_router(settings_router, tags=["Settings"])
api_router.include_router(correspondence_router, tags=["Correspondence"])
api_router.include_router(system_router, tags=["System"])

app.include_router(api_router)


# Health endpoint - directly on app for visibility and Docker healthcheck
@app.get("/api/health")
async def health_check():
    """Health check endpoint used by Docker Compose healthcheck"""
    return {"status": "healthy", "service": "casedesk-backend", "version": "1.5.1"}
