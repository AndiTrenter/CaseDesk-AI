"""
CaseDesk AI - Main FastAPI Application
Standalone self-hosted document and case management with AI support
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import hashlib
import jwt
import httpx
import aiofiles
import json

from models import (
    User, UserCreate, UserInDB, UserRole,
    SystemSettings, UserSettings, AIProviderType, InternetAccessLevel,
    MailAccount, MailAccountCreate,
    Case, CaseCreate, CaseStatus,
    Document, DocumentCreate, DocumentType,
    EmailMessage,
    Task, TaskCreate, TaskPriority, TaskStatus,
    Event, EventCreate,
    Draft, DraftCreate,
    ChatMessage, AuditLog,
    Token, SetupStatus
)

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'casedesk')]

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# File uploads
UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', './uploads'))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# OCR Service
OCR_SERVICE_URL = os.environ.get('OCR_SERVICE_URL', 'http://localhost:8002')

# OpenAI (optional)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("CaseDesk AI starting up...")
    # Ensure indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.cases.create_index("user_id")
    await db.documents.create_index("user_id")
    # Full-text search index for documents
    await db.documents.create_index([
        ("ocr_text", "text"),
        ("display_name", "text"),
        ("original_filename", "text"),
        ("tags", "text"),
        ("ai_summary", "text")
    ], default_language="german", name="document_fulltext")
    await db.tasks.create_index("user_id")
    await db.events.create_index("user_id")
    yield
    # Shutdown
    logger.info("CaseDesk AI shutting down...")
    client.close()


app = FastAPI(
    title="CaseDesk AI",
    description="Self-hosted document and case management with AI support",
    version="1.0.0",
    lifespan=lifespan
)

api_router = APIRouter(prefix="/api")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create JWT access token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current authenticated user from JWT token"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require authentication - raises 401 if not authenticated"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require admin role"""
    if user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def log_action(user_id: str, action: str, resource_type: str, resource_id: str = None, details: dict = None):
    """Create audit log entry"""
    log = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(log)


# ==================== Health & Setup ====================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "casedesk-backend", "version": "1.0.0"}


@api_router.get("/setup/status", response_model=SetupStatus)
async def get_setup_status():
    """Check if initial setup has been completed"""
    settings = await db.system_settings.find_one({}, {"_id": 0})
    admin_count = await db.users.count_documents({"role": UserRole.ADMIN})
    return SetupStatus(
        setup_completed=settings.get("setup_completed", False) if settings else False,
        has_admin=admin_count > 0,
        version="1.0.0"
    )


@api_router.post("/setup/init")
async def initialize_setup(
    language: str = Form("en"),
    admin_email: str = Form(...),
    admin_username: str = Form(...),
    admin_password: str = Form(...),
    admin_full_name: str = Form(None),
    ai_provider: str = Form("disabled"),
    openai_api_key: str = Form(None),
    internet_access: str = Form("denied")
):
    """Initial setup - create admin and system settings"""
    # Check if already setup
    existing_admin = await db.users.count_documents({"role": UserRole.ADMIN})
    if existing_admin > 0:
        raise HTTPException(status_code=400, detail="Setup already completed")
    
    # Create admin user
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    admin_user = {
        "id": user_id,
        "email": admin_email,
        "username": admin_username,
        "full_name": admin_full_name,
        "password_hash": hash_password(admin_password),
        "role": UserRole.ADMIN,
        "is_active": True,
        "language": language,
        "created_at": now,
        "updated_at": now,
        "last_login": None
    }
    
    await db.users.insert_one(admin_user)
    
    # Create system settings
    settings = {
        "id": str(uuid.uuid4()),
        "setup_completed": True,
        "default_language": language,
        "ai_provider": ai_provider,
        "openai_api_key": openai_api_key if ai_provider == "openai" else None,
        "internet_access": internet_access,
        "allow_external_ai": ai_provider == "openai",
        "created_at": now,
        "updated_at": now
    }
    
    await db.system_settings.insert_one(settings)
    
    # Log action
    await log_action(user_id, "setup_completed", "system", details={"language": language})
    
    # Create token
    token = create_access_token(user_id, admin_email, UserRole.ADMIN)
    
    return {
        "success": True,
        "message": "Setup completed successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": admin_email,
            "username": admin_username,
            "full_name": admin_full_name,
            "role": UserRole.ADMIN,
            "language": language
        }
    }


# ==================== Authentication ====================

@api_router.post("/auth/login", response_model=Token)
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    """User login"""
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    token = create_access_token(user["id"], user["email"], user["role"])
    
    # Remove sensitive data
    user.pop("password_hash", None)
    
    return Token(access_token=token, user=User(**user))


@api_router.get("/auth/me")
async def get_current_user_info(user: dict = Depends(require_auth)):
    """Get current user information"""
    return user


@api_router.post("/auth/logout")
async def logout(user: dict = Depends(require_auth)):
    """User logout (client should discard token)"""
    await log_action(user["id"], "logout", "auth")
    return {"success": True, "message": "Logged out successfully"}


# ==================== Users ====================

@api_router.get("/users", response_model=List[User])
async def list_users(user: dict = Depends(require_admin)):
    """List all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users


@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, admin: dict = Depends(require_admin)):
    """Create new user (admin only)"""
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    new_user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "is_active": True,
        "language": user_data.language,
        "created_at": now,
        "updated_at": now,
        "last_login": None
    }
    
    await db.users.insert_one(new_user)
    await log_action(admin["id"], "create_user", "user", user_id)
    
    new_user.pop("password_hash")
    return User(**new_user)


@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    """Delete user (admin only)"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_action(admin["id"], "delete_user", "user", user_id)
    return {"success": True, "message": "User deleted"}


# ==================== User Invitations ====================

@api_router.post("/users/invite")
async def invite_user(
    email: str = Form(...),
    role: str = Form("user"),
    admin: dict = Depends(require_admin)
):
    """Invite a new user via email (admin only)"""
    # Check if email already exists
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="E-Mail ist bereits registriert")
    
    # Check for existing pending invitation
    existing_invitation = await db.invitations.find_one({
        "email": email,
        "status": "pending",
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    })
    if existing_invitation:
        raise HTTPException(status_code=400, detail="Einladung für diese E-Mail existiert bereits")
    
    # Create invitation token
    invitation_id = str(uuid.uuid4())
    token = hashlib.sha256(f"{invitation_id}-{email}-{datetime.now()}".encode()).hexdigest()
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=7)).isoformat()
    
    invitation = {
        "id": invitation_id,
        "token": token,
        "email": email,
        "role": role,
        "invited_by": admin["email"],
        "invited_by_id": admin["id"],
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": expires_at
    }
    
    await db.invitations.insert_one(invitation)
    await log_action(admin["id"], "invite_user", "invitation", invitation_id, {"email": email})
    
    # Generate invitation URL (frontend URL)
    # In production, this should be configured via environment variable
    base_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    invitation_url = f"{base_url}/register/{token}"
    
    # Try to send email if SMTP is configured
    email_sent = False
    try:
        email_sent = await send_invitation_email(email, invitation_url, admin["full_name"] or admin["email"])
    except Exception as e:
        logger.warning(f"Failed to send invitation email: {e}")
    
    return {
        "success": True,
        "invitation_id": invitation_id,
        "invitation_url": invitation_url,
        "email_sent": email_sent,
        "expires_at": expires_at
    }


async def send_invitation_email(to_email: str, invitation_url: str, invited_by: str) -> bool:
    """Send invitation email via configured SMTP"""
    # Get admin's mail account with SMTP settings
    mail_account = await db.mail_accounts.find_one({
        "smtp_server": {"$exists": True, "$ne": ""}
    })
    
    if not mail_account:
        return False
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Decrypt password
        from cryptography.fernet import Fernet
        fernet_key = os.environ.get('FERNET_KEY', 'default-key-change-me-in-production').encode()
        # Pad or hash the key to 32 bytes for Fernet
        fernet_key = hashlib.sha256(fernet_key).digest()
        import base64
        fernet_key = base64.urlsafe_b64encode(fernet_key)
        fernet = Fernet(fernet_key)
        password = fernet.decrypt(mail_account["encrypted_password"].encode()).decode()
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Einladung zu CaseDesk AI'
        msg['From'] = mail_account["email"]
        msg['To'] = to_email
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Einladung zu CaseDesk AI</h2>
            <p>Hallo,</p>
            <p>{invited_by} hat Sie eingeladen, CaseDesk AI beizutreten.</p>
            <p>Klicken Sie auf den folgenden Link, um Ihr Konto zu erstellen:</p>
            <p style="margin: 20px 0;">
                <a href="{invitation_url}" style="background-color: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                    Konto erstellen
                </a>
            </p>
            <p style="color: #666; font-size: 12px;">
                Dieser Link ist 7 Tage gültig.<br>
                Falls Sie diese E-Mail nicht erwartet haben, können Sie sie ignorieren.
            </p>
        </body>
        </html>
        """
        
        text_body = f"""
        Einladung zu CaseDesk AI
        
        {invited_by} hat Sie eingeladen, CaseDesk AI beizutreten.
        
        Klicken Sie auf den folgenden Link, um Ihr Konto zu erstellen:
        {invitation_url}
        
        Dieser Link ist 7 Tage gültig.
        """
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        smtp_server = mail_account.get("smtp_server")
        smtp_port = mail_account.get("smtp_port", 587)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(mail_account["email"], password)
            server.sendmail(mail_account["email"], to_email, msg.as_string())
        
        return True
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return False


@api_router.get("/users/invitations")
async def list_invitations(admin: dict = Depends(require_admin)):
    """List all pending invitations (admin only)"""
    invitations = await db.invitations.find(
        {"status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return invitations


@api_router.delete("/users/invitations/{invitation_id}")
async def cancel_invitation(invitation_id: str, admin: dict = Depends(require_admin)):
    """Cancel a pending invitation (admin only)"""
    result = await db.invitations.update_one(
        {"id": invitation_id, "status": "pending"},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")
    
    return {"success": True}


@api_router.get("/auth/invitation/{token}")
async def validate_invitation(token: str):
    """Validate an invitation token (public endpoint)"""
    invitation = await db.invitations.find_one(
        {"token": token},
        {"_id": 0}
    )
    
    if not invitation:
        return {"valid": False, "error": "Einladung nicht gefunden"}
    
    if invitation["status"] != "pending":
        return {"valid": False, "error": "Einladung wurde bereits verwendet oder storniert"}
    
    if datetime.fromisoformat(invitation["expires_at"]) < datetime.now(timezone.utc):
        return {"valid": False, "error": "Einladung ist abgelaufen"}
    
    return {
        "valid": True,
        "email": invitation["email"],
        "role": invitation["role"],
        "invited_by": invitation["invited_by"]
    }


@api_router.post("/auth/register/{token}")
async def register_with_invitation(
    token: str,
    full_name: str = Form(...),
    password: str = Form(...)
):
    """Register a new user with an invitation token"""
    invitation = await db.invitations.find_one({"token": token})
    
    if not invitation:
        raise HTTPException(status_code=400, detail="Einladung nicht gefunden")
    
    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail="Einladung wurde bereits verwendet")
    
    if datetime.fromisoformat(invitation["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Einladung ist abgelaufen")
    
    # Check if email already exists (double check)
    existing = await db.users.find_one({"email": invitation["email"]})
    if existing:
        raise HTTPException(status_code=400, detail="E-Mail ist bereits registriert")
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    username = invitation["email"].split("@")[0] + "_" + str(uuid.uuid4())[:4]
    
    new_user = {
        "id": user_id,
        "email": invitation["email"],
        "username": username,
        "full_name": full_name,
        "password_hash": hash_password(password),
        "role": invitation.get("role", "user"),
        "is_active": True,
        "language": "de",
        "created_at": now,
        "updated_at": now,
        "last_login": None,
        "invited_by": invitation["invited_by_id"]
    }
    
    await db.users.insert_one(new_user)
    
    # Mark invitation as used
    await db.invitations.update_one(
        {"id": invitation["id"]},
        {"$set": {"status": "accepted", "accepted_at": now, "user_id": user_id}}
    )
    
    await log_action(user_id, "register", "user", user_id, {"invited_by": invitation["invited_by_id"]})
    
    return {"success": True, "message": "Konto erfolgreich erstellt"}


# ==================== Cases ====================

@api_router.get("/cases", response_model=List[Case])
async def list_cases(
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """List cases for current user"""
    query = {"user_id": user["id"]}
    if status:
        query["status"] = status
    
    cases = await db.cases.find(query, {"_id": 0}).sort("updated_at", -1).to_list(1000)
    return cases


@api_router.post("/cases", response_model=Case)
async def create_case(case_data: CaseCreate, user: dict = Depends(require_auth)):
    """Create new case"""
    case_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    new_case = {
        "id": case_id,
        "user_id": user["id"],
        **case_data.model_dump(),
        "document_ids": [],
        "email_ids": [],
        "created_at": now,
        "updated_at": now
    }
    
    await db.cases.insert_one(new_case)
    await log_action(user["id"], "create_case", "case", case_id)
    
    return Case(**new_case)


@api_router.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str, user: dict = Depends(require_auth)):
    """Get case details"""
    case = await db.cases.find_one({"id": case_id, "user_id": user["id"]}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return Case(**case)


@api_router.put("/cases/{case_id}", response_model=Case)
async def update_case(case_id: str, case_data: CaseCreate, user: dict = Depends(require_auth)):
    """Update case"""
    case = await db.cases.find_one({"id": case_id, "user_id": user["id"]})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    update_data = case_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.cases.update_one({"id": case_id}, {"$set": update_data})
    await log_action(user["id"], "update_case", "case", case_id)
    
    updated = await db.cases.find_one({"id": case_id}, {"_id": 0})
    return Case(**updated)


@api_router.delete("/cases/{case_id}")
async def delete_case(case_id: str, user: dict = Depends(require_auth)):
    """Delete case"""
    result = await db.cases.delete_one({"id": case_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")
    
    await log_action(user["id"], "delete_case", "case", case_id)
    return {"success": True, "message": "Case deleted"}


# ==================== Documents ====================

@api_router.get("/documents")
async def list_documents(
    case_id: Optional[str] = None,
    document_type: Optional[DocumentType] = None,
    search: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """List documents for current user with full-text search"""
    if search:
        # Full-text search across document content, name, and tags
        pipeline = [
            {
                "$match": {
                    "user_id": user["id"],
                    "$text": {"$search": search}
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "textScore"}
                }
            },
            {
                "$sort": {"score": -1}
            },
            {
                "$project": {"_id": 0}
            },
            {
                "$limit": 100
            }
        ]
        
        if case_id:
            pipeline[0]["$match"]["case_id"] = case_id
        if document_type:
            pipeline[0]["$match"]["document_type"] = document_type
        
        documents = await db.documents.aggregate(pipeline).to_list(100)
        return documents
    else:
        # Normal listing
        query = {"user_id": user["id"]}
        if case_id:
            query["case_id"] = case_id
        if document_type:
            query["document_type"] = document_type
        
        documents = await db.documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return documents


@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    document_type: str = Form("other"),
    auto_process: bool = Form(True),
    user: dict = Depends(require_auth)
):
    """Upload and auto-process document with OCR and AI analysis"""
    from ai_service import AIService, DocumentAnalyzer, get_ai_service
    
    content = await file.read()
    
    # Generate unique filename
    doc_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower()
    storage_filename = f"{doc_id}{file_ext}"
    storage_path = UPLOAD_DIR / user["id"] / storage_filename
    
    # Ensure user directory exists
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file
    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(content)
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Create initial document record
    document = {
        "id": doc_id,
        "user_id": user["id"],
        "case_id": case_id,
        "filename": storage_filename,
        "original_filename": file.filename,
        "display_name": file.filename,  # Will be updated after AI analysis
        "mime_type": file.content_type,
        "size": len(content),
        "storage_path": str(storage_path),
        "document_type": document_type,
        "ocr_text": None,
        "ocr_processed": False,
        "ai_analyzed": False,
        "ai_summary": None,
        "tags": [],
        "metadata": {},
        "sender": None,
        "recipient": None,
        "document_date": None,
        "deadline": None,
        "deadlines": [],
        "importance": "mittel",
        "created_at": now,
        "updated_at": now
    }
    
    await db.documents.insert_one(document)
    
    # Link to case if provided
    if case_id:
        await db.cases.update_one(
            {"id": case_id, "user_id": user["id"]},
            {"$push": {"document_ids": doc_id}}
        )
    
    await log_action(user["id"], "upload_document", "document", doc_id)
    
    # Auto-process document (OCR + AI analysis)
    if auto_process:
        try:
            # Step 1: OCR
            ocr_text = ""
            try:
                async with httpx.AsyncClient(timeout=120.0) as http_client:
                    with open(storage_path, "rb") as f:
                        files = {"file": (file.filename, f, file.content_type)}
                        response = await http_client.post(f"{OCR_SERVICE_URL}/ocr", files=files)
                
                if response.status_code == 200:
                    ocr_result = response.json()
                    ocr_text = ocr_result.get("text", "")
            except Exception as e:
                logger.warning(f"OCR processing failed: {e}")
            
            # Step 2: AI Analysis
            if ocr_text:
                try:
                    ai_service = await get_ai_service(db)
                    analyzer = DocumentAnalyzer(ai_service)
                    
                    analysis = await analyzer.analyze_document(ocr_text, file.filename)
                    
                    if analysis.get("success"):
                        metadata = analysis.get("metadata", {})
                        
                        # Generate new display name
                        new_display_name = analyzer.generate_filename(metadata, file_ext)
                        
                        # Update document with AI analysis
                        update_data = {
                            "ocr_text": ocr_text,
                            "ocr_processed": True,
                            "ai_analyzed": True,
                            "display_name": new_display_name,
                            "document_type": metadata.get("dokumenttyp", document_type).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue"),
                            "tags": metadata.get("tags", []),
                            "ai_summary": metadata.get("zusammenfassung"),
                            "sender": metadata.get("absender"),
                            "importance": metadata.get("wichtigkeit", "mittel"),
                            "deadlines": metadata.get("fristen", []),
                            "metadata": metadata,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        # Parse document date
                        if metadata.get("datum") and metadata["datum"] != "null":
                            try:
                                update_data["document_date"] = metadata["datum"]
                            except:
                                pass
                        
                        await db.documents.update_one({"id": doc_id}, {"$set": update_data})
                        
                        # Update document dict for response
                        document.update(update_data)
                        
                        # Create tasks for deadlines
                        for deadline in metadata.get("fristen", []):
                            try:
                                task = {
                                    "id": str(uuid.uuid4()),
                                    "user_id": user["id"],
                                    "title": f"Frist: {metadata.get('kurzthema', 'Dokument')}",
                                    "description": f"Automatisch erkannte Frist aus: {new_display_name}",
                                    "priority": "high",
                                    "status": "todo",
                                    "due_date": deadline,
                                    "case_id": case_id,
                                    "document_id": doc_id,
                                    "created_at": now,
                                    "updated_at": now
                                }
                                await db.tasks.insert_one(task)
                            except:
                                pass
                    else:
                        # AI analysis failed, just save OCR text
                        await db.documents.update_one(
                            {"id": doc_id},
                            {"$set": {
                                "ocr_text": ocr_text,
                                "ocr_processed": True,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        document["ocr_text"] = ocr_text
                        document["ocr_processed"] = True
                        
                except Exception as e:
                    logger.error(f"AI analysis failed: {e}")
                    # Save OCR text even if AI fails
                    await db.documents.update_one(
                        {"id": doc_id},
                        {"$set": {
                            "ocr_text": ocr_text,
                            "ocr_processed": True,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
        except Exception as e:
            logger.error(f"Document processing error: {e}")
    
    document.pop("_id", None)
    return {"success": True, "document": document}


@api_router.post("/documents/{document_id}/reprocess")
async def reprocess_document(document_id: str, user: dict = Depends(require_auth)):
    """Re-process document with OCR and AI analysis"""
    from ai_service import AIService, DocumentAnalyzer, get_ai_service
    
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Run OCR
    ocr_text = ""
    try:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            with open(document["storage_path"], "rb") as f:
                files = {"file": (document["original_filename"], f, document["mime_type"])}
                response = await http_client.post(f"{OCR_SERVICE_URL}/ocr", files=files)
        
        if response.status_code == 200:
            ocr_result = response.json()
            ocr_text = ocr_result.get("text", "")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OCR service error: {str(e)}")
    
    if not ocr_text:
        raise HTTPException(status_code=400, detail="No text could be extracted from document")
    
    # AI Analysis
    ai_service = await get_ai_service(db)
    analyzer = DocumentAnalyzer(ai_service)
    
    file_ext = Path(document["original_filename"]).suffix.lower()
    analysis = await analyzer.analyze_document(ocr_text, document["original_filename"])
    
    if analysis.get("success"):
        metadata = analysis.get("metadata", {})
        new_display_name = analyzer.generate_filename(metadata, file_ext)
        
        update_data = {
            "ocr_text": ocr_text,
            "ocr_processed": True,
            "ai_analyzed": True,
            "display_name": new_display_name,
            "tags": metadata.get("tags", []),
            "ai_summary": metadata.get("zusammenfassung"),
            "sender": metadata.get("absender"),
            "importance": metadata.get("wichtigkeit", "mittel"),
            "deadlines": metadata.get("fristen", []),
            "metadata": metadata,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if metadata.get("datum") and metadata["datum"] != "null":
            update_data["document_date"] = metadata["datum"]
        
        await db.documents.update_one({"id": document_id}, {"$set": update_data})
        
        return {
            "success": True,
            "display_name": new_display_name,
            "tags": metadata.get("tags", []),
            "summary": metadata.get("zusammenfassung"),
            "metadata": metadata
        }
    else:
        # Save OCR text even if AI fails
        await db.documents.update_one(
            {"id": document_id},
            {"$set": {
                "ocr_text": ocr_text,
                "ocr_processed": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {
            "success": False,
            "ocr_text": ocr_text[:500] + "...",
            "error": analysis.get("error", "AI analysis failed")
        }


@api_router.post("/documents/{document_id}/ocr")
async def process_document_ocr(document_id: str, user: dict = Depends(require_auth)):
    """Process document with OCR only (legacy endpoint)"""
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            with open(document["storage_path"], "rb") as f:
                files = {"file": (document["original_filename"], f, document["mime_type"])}
                response = await http_client.post(f"{OCR_SERVICE_URL}/ocr", files=files)
        
        if response.status_code == 200:
            ocr_result = response.json()
            
            await db.documents.update_one(
                {"id": document_id},
                {"$set": {
                    "ocr_text": ocr_result.get("text", ""),
                    "ocr_processed": True,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {"success": True, "text": ocr_result.get("text", "")}
        else:
            raise HTTPException(status_code=500, detail="OCR processing failed")
            
    except httpx.RequestError as e:
        logger.error(f"OCR service error: {e}")
        raise HTTPException(status_code=503, detail="OCR service unavailable")


@api_router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str, user: dict = Depends(require_auth)):
    """Get document details"""
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return Document(**document)


@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str, user: dict = Depends(require_auth)):
    """Delete document"""
    document = await db.documents.find_one({"id": document_id, "user_id": user["id"]})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    try:
        os.remove(document["storage_path"])
    except OSError:
        pass
    
    # Remove from case
    if document.get("case_id"):
        await db.cases.update_one(
            {"id": document["case_id"]},
            {"$pull": {"document_ids": document_id}}
        )
    
    await db.documents.delete_one({"id": document_id})
    await log_action(user["id"], "delete_document", "document", document_id)
    
    return {"success": True, "message": "Document deleted"}


# ==================== Tasks ====================

@api_router.get("/tasks", response_model=List[Task])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    case_id: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """List tasks for current user"""
    query = {"user_id": user["id"]}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if case_id:
        query["case_id"] = case_id
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("due_date", 1).to_list(1000)
    return tasks


@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, user: dict = Depends(require_auth)):
    """Create new task"""
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    new_task = {
        "id": task_id,
        "user_id": user["id"],
        **task_data.model_dump(),
        "document_id": None,
        "email_id": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None
    }
    
    # Convert due_date to string if present
    if new_task.get("due_date"):
        new_task["due_date"] = new_task["due_date"].isoformat() if isinstance(new_task["due_date"], datetime) else new_task["due_date"]
    
    await db.tasks.insert_one(new_task)
    await log_action(user["id"], "create_task", "task", task_id)
    
    return Task(**new_task)


@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_data: TaskCreate, user: dict = Depends(require_auth)):
    """Update task"""
    task = await db.tasks.find_one({"id": task_id, "user_id": user["id"]})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Handle completion
    if task_data.status == TaskStatus.DONE and task.get("status") != TaskStatus.DONE:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert due_date to string if present
    if update_data.get("due_date"):
        update_data["due_date"] = update_data["due_date"].isoformat() if isinstance(update_data["due_date"], datetime) else update_data["due_date"]
    
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    await log_action(user["id"], "update_task", "task", task_id)
    
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return Task(**updated)


@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(require_auth)):
    """Delete task"""
    result = await db.tasks.delete_one({"id": task_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await log_action(user["id"], "delete_task", "task", task_id)
    return {"success": True, "message": "Task deleted"}


# ==================== Events/Calendar ====================

@api_router.get("/events", response_model=List[Event])
async def list_events(
    start: Optional[str] = None,
    end: Optional[str] = None,
    case_id: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """List events for current user"""
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    
    # Date filtering would be applied here
    
    events = await db.events.find(query, {"_id": 0}).sort("start_time", 1).to_list(1000)
    return events


@api_router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, user: dict = Depends(require_auth)):
    """Create new event"""
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    new_event = {
        "id": event_id,
        "user_id": user["id"],
        **event_data.model_dump(),
        "document_id": None,
        "is_deadline": False,
        "reminder_minutes": None,
        "created_at": now,
        "updated_at": now
    }
    
    # Convert datetimes to strings
    for field in ["start_time", "end_time"]:
        if new_event.get(field) and isinstance(new_event[field], datetime):
            new_event[field] = new_event[field].isoformat()
    
    await db.events.insert_one(new_event)
    await log_action(user["id"], "create_event", "event", event_id)
    
    return Event(**new_event)


@api_router.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventCreate, user: dict = Depends(require_auth)):
    """Update event"""
    event = await db.events.find_one({"id": event_id, "user_id": user["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert datetimes to strings
    for field in ["start_time", "end_time"]:
        if update_data.get(field) and isinstance(update_data[field], datetime):
            update_data[field] = update_data[field].isoformat()
    
    await db.events.update_one({"id": event_id}, {"$set": update_data})
    await log_action(user["id"], "update_event", "event", event_id)
    
    updated = await db.events.find_one({"id": event_id}, {"_id": 0})
    return Event(**updated)


@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, user: dict = Depends(require_auth)):
    """Delete event"""
    result = await db.events.delete_one({"id": event_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await log_action(user["id"], "delete_event", "event", event_id)
    return {"success": True, "message": "Event deleted"}


# ==================== Drafts ====================

@api_router.get("/drafts", response_model=List[Draft])
async def list_drafts(
    case_id: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """List drafts for current user"""
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    
    drafts = await db.drafts.find(query, {"_id": 0}).sort("updated_at", -1).to_list(1000)
    return drafts


@api_router.post("/drafts", response_model=Draft)
async def create_draft(draft_data: DraftCreate, user: dict = Depends(require_auth)):
    """Create new draft"""
    draft_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    new_draft = {
        "id": draft_id,
        "user_id": user["id"],
        **draft_data.model_dump(),
        "ai_generated": False,
        "is_sent": False,
        "created_at": now,
        "updated_at": now
    }
    
    await db.drafts.insert_one(new_draft)
    await log_action(user["id"], "create_draft", "draft", draft_id)
    
    return Draft(**new_draft)


@api_router.put("/drafts/{draft_id}", response_model=Draft)
async def update_draft(draft_id: str, draft_data: DraftCreate, user: dict = Depends(require_auth)):
    """Update draft"""
    draft = await db.drafts.find_one({"id": draft_id, "user_id": user["id"]})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    update_data = draft_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.drafts.update_one({"id": draft_id}, {"$set": update_data})
    await log_action(user["id"], "update_draft", "draft", draft_id)
    
    updated = await db.drafts.find_one({"id": draft_id}, {"_id": 0})
    return Draft(**updated)


@api_router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str, user: dict = Depends(require_auth)):
    """Delete draft"""
    result = await db.drafts.delete_one({"id": draft_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    await log_action(user["id"], "delete_draft", "draft", draft_id)
    return {"success": True, "message": "Draft deleted"}


# ==================== AI Chat ====================

@api_router.post("/ai/chat")
async def ai_chat(
    message: str = Form(...),
    session_id: str = Form(None),
    case_id: str = Form(None),
    user: dict = Depends(require_auth)
):
    """AI Chat endpoint with Ollama (local) and OpenAI support"""
    from ai_service import get_ai_service, ChatAssistant
    
    # Get system settings
    settings = await db.system_settings.find_one({}, {"_id": 0})
    
    # Check internet access for external AI
    if settings and settings.get("internet_access") == "denied" and settings.get("ai_provider") == "openai":
        return {
            "success": False,
            "error": "Externe KI benötigt Internetzugriff. Bitte aktivieren Sie den Internetzugriff oder nutzen Sie die lokale KI (Ollama).",
            "response": None
        }
    
    session_id = session_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Save user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "session_id": session_id,
        "role": "user",
        "content": message,
        "case_id": case_id,
        "document_ids": [],
        "created_at": now
    }
    await db.chat_messages.insert_one(user_msg)
    
    # Prepare context
    context = {}
    
    # Always include user's recent documents for context awareness
    all_docs = await db.documents.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "display_name": 1, "original_filename": 1, "ocr_text": 1, 
         "ai_summary": 1, "tags": 1, "document_type": 1, "case_id": 1, "sender": 1, 
         "document_date": 1}
    ).sort("created_at", -1).to_list(100)
    
    # Get all cases for context
    all_cases = await db.cases.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "status": 1, "reference_number": 1}
    ).to_list(50)
    
    context["all_documents"] = all_docs
    context["all_cases"] = all_cases
    
    if case_id:
        case = await db.cases.find_one({"id": case_id, "user_id": user["id"]}, {"_id": 0})
        if case:
            context["current_case"] = case
            # Get linked documents with full content
            if case.get("document_ids"):
                docs = await db.documents.find(
                    {"id": {"$in": case["document_ids"]}, "user_id": user["id"]},
                    {"_id": 0}
                ).to_list(20)
                context["case_documents"] = docs
    
    # Get open tasks
    open_tasks = await db.tasks.find(
        {"user_id": user["id"], "status": {"$ne": "done"}},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "due_date": 1, "priority": 1, "case_id": 1}
    ).sort("due_date", 1).to_list(20)
    context["open_tasks"] = open_tasks
    
    # Get upcoming events
    now = datetime.now(timezone.utc).isoformat()
    upcoming_events = await db.events.find(
        {"user_id": user["id"], "start_date": {"$gte": now}},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "start_date": 1, "end_date": 1}
    ).sort("start_date", 1).to_list(10)
    context["upcoming_events"] = upcoming_events
    
    # Determine user's language preference (user_settings takes priority over user doc)
    user_settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    user_language = (user_settings or {}).get("language") or user.get("language") or "de"
    
    # Get AI service and generate response
    try:
        ai_service = await get_ai_service(db)
        assistant = ChatAssistant(ai_service)
        
        ai_response = await assistant.chat(
            message=message,
            context=context,
            language=user_language
        )
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        ai_response = f"KI-Fehler: {str(e)}"
    
    # Save AI response
    ai_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "session_id": session_id,
        "role": "assistant",
        "content": ai_response,
        "case_id": case_id,
        "document_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(ai_msg)
    
    return {
        "success": True,
        "response": ai_response,
        "session_id": session_id
    }


@api_router.get("/ai/status")
async def get_ai_status(user: dict = Depends(require_auth)):
    """Check AI service availability"""
    from ai_service import AIService
    
    ai = AIService(provider="ollama")
    status = await ai.check_availability()
    
    settings = await db.system_settings.find_one({}, {"_id": 0})
    
    return {
        "configured_provider": settings.get("ai_provider", "ollama") if settings else "ollama",
        "ollama": status["ollama"],
        "openai": status["openai"],
        "internet_access": settings.get("internet_access", "denied") if settings else "denied"
    }


@api_router.get("/ai/history")
async def get_chat_history(
    session_id: str,
    user: dict = Depends(require_auth)
):
    """Get chat history for session"""
    messages = await db.chat_messages.find(
        {"user_id": user["id"], "session_id": session_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    return {"messages": messages}


# ==================== Settings ====================

@api_router.get("/settings/system")
async def get_system_settings(user: dict = Depends(require_admin)):
    """Get system settings (admin only)"""
    settings = await db.system_settings.find_one({}, {"_id": 0})
    if settings:
        # Mask API key
        if settings.get("openai_api_key"):
            settings["openai_api_key"] = "***configured***"
    return settings or {}


@api_router.put("/settings/system")
async def update_system_settings(
    ai_provider: str = Form(None),
    openai_api_key: str = Form(None),
    internet_access: str = Form(None),
    default_language: str = Form(None),
    user: dict = Depends(require_admin)
):
    """Update system settings (admin only)"""
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


@api_router.get("/settings/user")
async def get_user_settings(user: dict = Depends(require_auth)):
    """Get current user's settings"""
    settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return settings or {"user_id": user["id"], "language": "de", "theme": "dark"}


@api_router.put("/settings/user")
async def update_user_settings(
    language: str = Form(None),
    theme: str = Form(None),
    notifications_enabled: bool = Form(None),
    user: dict = Depends(require_auth)
):
    """Update current user's settings"""
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
    
    # Also sync language to user document for consistency
    if language is not None:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"language": language, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"success": True, "message": "Settings updated"}


# ==================== Mail Accounts ====================

@api_router.get("/mail/accounts")
async def list_mail_accounts(user: dict = Depends(require_auth)):
    """List mail accounts for current user"""
    accounts = await db.mail_accounts.find(
        {"user_id": user["id"]},
        {"_id": 0, "password": 0}
    ).to_list(100)
    return accounts


@api_router.post("/mail/accounts")
async def create_mail_account(
    email: str = Form(...),
    display_name: str = Form(...),
    imap_server: str = Form(...),
    imap_port: int = Form(993),
    imap_use_ssl: bool = Form(True),
    password: str = Form(...),
    smtp_server: str = Form(None),
    smtp_port: int = Form(587),
    user: dict = Depends(require_auth)
):
    """Add mail account"""
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
        "password": password,  # Should be encrypted in production
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "smtp_use_tls": True,
        "is_active": True,
        "last_sync": None,
        "created_at": now
    }
    
    await db.mail_accounts.insert_one(account)
    await log_action(user["id"], "create_mail_account", "mail_account", account_id)
    
    account.pop("password")
    return {"success": True, "account": account}


@api_router.delete("/mail/accounts/{account_id}")
async def delete_mail_account(account_id: str, user: dict = Depends(require_auth)):
    """Delete mail account"""
    result = await db.mail_accounts.delete_one({"id": account_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mail account not found")
    
    await log_action(user["id"], "delete_mail_account", "mail_account", account_id)
    return {"success": True, "message": "Mail account deleted"}


# ==================== Dashboard Stats ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(require_auth)):
    """Get dashboard statistics"""
    user_id = user["id"]
    
    # Count various items
    cases_count = await db.cases.count_documents({"user_id": user_id})
    open_cases = await db.cases.count_documents({"user_id": user_id, "status": CaseStatus.OPEN})
    documents_count = await db.documents.count_documents({"user_id": user_id})
    pending_tasks = await db.tasks.count_documents({"user_id": user_id, "status": {"$ne": TaskStatus.DONE}})
    emails_count = await db.emails.count_documents({"user_id": user_id})
    
    # Upcoming events
    upcoming_events = await db.events.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("start_time", 1).limit(5).to_list(5)
    
    # Recent documents
    recent_documents = await db.documents.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Urgent tasks
    urgent_tasks = await db.tasks.find(
        {"user_id": user_id, "status": {"$ne": TaskStatus.DONE}},
        {"_id": 0}
    ).sort("due_date", 1).limit(5).to_list(5)
    
    # Recent emails
    recent_emails = await db.emails.find(
        {"user_id": user_id},
        {"_id": 0}
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


# ==================== Email Operations ====================

@api_router.get("/emails")
async def list_emails(
    case_id: Optional[str] = None,
    unread_only: bool = False,
    user: dict = Depends(require_auth)
):
    """List emails for current user"""
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    if unread_only:
        query["is_read"] = False
    
    emails = await db.emails.find(query, {"_id": 0}).sort("received_at", -1).to_list(500)
    return emails


@api_router.get("/emails/{email_id}")
async def get_email(email_id: str, user: dict = Depends(require_auth)):
    """Get email details"""
    email_doc = await db.emails.find_one(
        {"id": email_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Mark as read
    if not email_doc.get("is_read"):
        await db.emails.update_one(
            {"id": email_id},
            {"$set": {"is_read": True}}
        )
    
    return email_doc


@api_router.post("/emails/fetch/{account_id}")
async def fetch_emails(account_id: str, user: dict = Depends(require_auth)):
    """Fetch new emails from mail account"""
    from email_service import EmailService
    
    email_service = EmailService(db)
    result = await email_service.fetch_emails(account_id, user["id"])
    
    if result.get("success"):
        await log_action(user["id"], "fetch_emails", "mail_account", account_id, 
                        {"fetched_count": result.get("fetched_count", 0)})
    
    return result


@api_router.post("/emails/{email_id}/process")
async def process_email(email_id: str, user: dict = Depends(require_auth)):
    """Process email with AI for summary and deadlines"""
    from email_service import EmailService
    from ai_service import get_ai_service
    
    email_service = EmailService(db)
    ai_service = await get_ai_service(db)
    
    result = await email_service.process_email_with_ai(email_id, user["id"], ai_service)
    return result


@api_router.post("/emails/{email_id}/link")
async def link_email_to_case(
    email_id: str,
    case_id: str = Form(...),
    user: dict = Depends(require_auth)
):
    """Link email to a case"""
    from email_service import EmailService
    
    email_service = EmailService(db)
    result = await email_service.link_email_to_case(email_id, case_id, user["id"])
    
    if result.get("success"):
        await log_action(user["id"], "link_email", "email", email_id, {"case_id": case_id})
    
    return result


@api_router.post("/emails/{email_id}/import-attachment/{attachment_id}")
async def import_attachment(
    email_id: str,
    attachment_id: str,
    case_id: str = Form(None),
    user: dict = Depends(require_auth)
):
    """Import email attachment as document"""
    from email_service import EmailService
    
    email_service = EmailService(db)
    result = await email_service.import_attachment_as_document(
        email_id, attachment_id, user["id"], case_id
    )
    
    if result.get("success"):
        await log_action(user["id"], "import_attachment", "document", result.get("document_id"))
    
    return result


@api_router.delete("/emails/{email_id}")
async def delete_email(email_id: str, user: dict = Depends(require_auth)):
    """Delete email"""
    result = await db.emails.delete_one({"id": email_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Email not found")
    
    await log_action(user["id"], "delete_email", "email", email_id)
    return {"success": True, "message": "Email deleted"}


# ==================== Document Preview ====================

@api_router.get("/documents/{document_id}/preview")
async def get_document_preview(document_id: str, user: dict = Depends(require_auth)):
    """Get document preview data"""
    document = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    preview_data = {
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
    
    return preview_data


@api_router.get("/documents/{document_id}/download")
async def download_document(document_id: str, user: dict = Depends(require_auth)):
    """Get document file for download"""
    from fastapi.responses import FileResponse
    
    document = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]},
        {"_id": 0}
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


# ==================== Data Export ====================

@api_router.get("/export/all")
async def export_all_data(user: dict = Depends(require_auth)):
    """Export all user data as JSON"""
    user_id = user["id"]
    
    # Gather all user data
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "username": user.get("username"),
            "full_name": user.get("full_name")
        },
        "cases": await db.cases.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "documents": [],
        "tasks": await db.tasks.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "events": await db.events.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "drafts": await db.drafts.find({"user_id": user_id}, {"_id": 0}).to_list(10000),
        "emails": await db.emails.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    }
    
    # Documents without OCR text (too large)
    docs = await db.documents.find({"user_id": user_id}, {"_id": 0, "ocr_text": 0}).to_list(10000)
    export_data["documents"] = docs
    
    await log_action(user_id, "export_data", "user", user_id)
    
    return export_data


@api_router.get("/export/case/{case_id}")
async def export_case(case_id: str, user: dict = Depends(require_auth)):
    """Export single case with all related data"""
    user_id = user["id"]
    
    case = await db.cases.find_one({"id": case_id, "user_id": user_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get related documents
    documents = await db.documents.find(
        {"case_id": case_id, "user_id": user_id},
        {"_id": 0, "ocr_text": 0}
    ).to_list(1000)
    
    # Get related tasks
    tasks = await db.tasks.find(
        {"case_id": case_id, "user_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Get related emails
    emails = await db.emails.find(
        {"case_id": case_id, "user_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Get related events
    events = await db.events.find(
        {"case_id": case_id, "user_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "case": case,
        "documents": documents,
        "tasks": tasks,
        "emails": emails,
        "events": events
    }
    
    return export_data


# ==================== Response Generation ====================

@api_router.get("/cases/{case_id}/analyze")
async def analyze_case(case_id: str, user: dict = Depends(require_auth)):
    """Analyze case and determine requirements for response"""
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    result = await response_service.analyze_case_requirements(case_id, user["id"])
    return result


@api_router.post("/cases/{case_id}/generate-response")
async def generate_case_response(
    case_id: str,
    response_type: str = Form(...),
    recipient: str = Form(...),
    subject: str = Form(...),
    instructions: str = Form(None),
    document_ids: str = Form(None),
    output_format: str = Form("txt"),
    user: dict = Depends(require_auth)
):
    """Generate AI response for a case with attached documents"""
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    # Parse document IDs
    doc_ids = json.loads(document_ids) if document_ids else []
    
    result = await response_service.generate_response(
        case_id=case_id,
        user_id=user["id"],
        response_type=response_type,
        recipient=recipient,
        subject=subject,
        instructions=instructions,
        include_document_ids=doc_ids
    )
    
    if result.get("success"):
        await log_action(user["id"], "generate_response", "correspondence", result.get("correspondence_id"),
                        {"case_id": case_id, "type": response_type})
    
    return result


@api_router.get("/correspondence")
async def list_correspondence(
    case_id: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """List correspondence for user or case"""
    query = {"user_id": user["id"]}
    if case_id:
        query["case_id"] = case_id
    
    correspondence = await db.correspondence.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return correspondence


@api_router.get("/correspondence/{correspondence_id}")
async def get_correspondence(correspondence_id: str, user: dict = Depends(require_auth)):
    """Get correspondence details"""
    corr = await db.correspondence.find_one(
        {"id": correspondence_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not corr:
        raise HTTPException(status_code=404, detail="Correspondence not found")
    return corr


@api_router.put("/correspondence/{correspondence_id}")
async def update_correspondence(
    correspondence_id: str,
    content: str = Form(None),
    subject: str = Form(None),
    status: str = Form(None),
    user: dict = Depends(require_auth)
):
    """Update correspondence content"""
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    result = await response_service.update_correspondence(
        correspondence_id, user["id"], content, subject, status
    )
    
    if result.get("success"):
        await log_action(user["id"], "update_correspondence", "correspondence", correspondence_id)
    
    return result


@api_router.delete("/correspondence/{correspondence_id}")
async def delete_correspondence(correspondence_id: str, user: dict = Depends(require_auth)):
    """Delete correspondence"""
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    result = await response_service.delete_correspondence(correspondence_id, user["id"])
    
    if result.get("success"):
        await log_action(user["id"], "delete_correspondence", "correspondence", correspondence_id)
    
    return result


@api_router.get("/correspondence/{correspondence_id}/download")
async def download_correspondence_package(correspondence_id: str, user: dict = Depends(require_auth)):
    """Download correspondence as ZIP with attachments"""
    from fastapi.responses import FileResponse
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    result = await response_service.create_download_package(correspondence_id, user["id"])
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    await log_action(user["id"], "download_package", "correspondence", correspondence_id)
    
    return FileResponse(
        result["zip_path"],
        filename=result["filename"],
        media_type="application/zip"
    )


@api_router.post("/correspondence/{correspondence_id}/send")
async def send_correspondence(
    correspondence_id: str,
    mail_account_id: str = Form(...),
    recipient_email: str = Form(...),
    user: dict = Depends(require_auth)
):
    """Send correspondence via email"""
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    result = await response_service.send_via_email(
        correspondence_id, user["id"], mail_account_id, recipient_email
    )
    
    if result.get("success"):
        await log_action(user["id"], "send_correspondence", "correspondence", correspondence_id,
                        {"recipient": recipient_email})
    
    return result


@api_router.get("/cases/{case_id}/history")
async def get_case_history(case_id: str, user: dict = Depends(require_auth)):
    """Get audit history for a case"""
    # Get correspondence history
    correspondence = await db.correspondence.find(
        {"case_id": case_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get audit logs for this case
    audit_logs = await db.audit_logs.find(
        {"resource_id": case_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "correspondence": correspondence,
        "audit_logs": audit_logs
    }


@api_router.put("/documents/{document_id}")
async def update_document(
    document_id: str,
    display_name: str = Form(None),
    document_type: str = Form(None),
    tags: str = Form(None),
    case_id: str = Form(None),
    user: dict = Depends(require_auth)
):
    """Update document metadata"""
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
    
    # Handle case change
    old_case_id = document.get("case_id")
    if case_id is not None and case_id != old_case_id:
        update_data["case_id"] = case_id if case_id else None
        
        # Remove from old case
        if old_case_id:
            await db.cases.update_one(
                {"id": old_case_id},
                {"$pull": {"document_ids": document_id}}
            )
        
        # Add to new case
        if case_id:
            await db.cases.update_one(
                {"id": case_id, "user_id": user["id"]},
                {"$addToSet": {"document_ids": document_id}}
            )
    
    await db.documents.update_one({"id": document_id}, {"$set": update_data})
    await log_action(user["id"], "update_document", "document", document_id)
    
    updated = await db.documents.find_one({"id": document_id}, {"_id": 0})
    return {"success": True, "document": updated}


@api_router.get("/cases/{case_id}/documents")
async def get_case_documents(case_id: str, user: dict = Depends(require_auth)):
    """Get all documents for a case"""
    documents = await db.documents.find(
        {"case_id": case_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    return documents


# ==================== Proactive AI Assistant ====================

@api_router.post("/ai/suggest-documents")
async def suggest_documents_for_case(
    case_title: str = Form(...),
    case_description: str = Form(None),
    user: dict = Depends(require_auth)
):
    """Suggest relevant documents when creating a case"""
    from ai_service import get_ai_service, ProactiveAssistant
    
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    
    result = await assistant.suggest_documents_for_case(
        user["id"], case_title, case_description
    )
    return result


@api_router.get("/cases/{case_id}/proactive-analysis")
async def get_proactive_case_analysis(case_id: str, user: dict = Depends(require_auth)):
    """Get proactive AI analysis for a case"""
    from ai_service import get_ai_service, ProactiveAssistant
    
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    
    result = await assistant.analyze_case_proactively(user["id"], case_id)
    return result


@api_router.get("/documents/{document_id}/auto-link")
async def auto_link_document(document_id: str, user: dict = Depends(require_auth)):
    """Automatically find links for a document"""
    from ai_service import get_ai_service, ProactiveAssistant
    
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    
    result = await assistant.auto_link_documents(user["id"], document_id)
    return result


@api_router.get("/ai/daily-briefing")
async def get_daily_briefing(user: dict = Depends(require_auth)):
    """Get daily briefing with important items"""
    from ai_service import get_ai_service, ProactiveAssistant
    
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    
    result = await assistant.get_daily_briefing(user["id"])
    return result


# Include router
app.include_router(api_router)


# Serve API docs
@app.get("/api/docs", include_in_schema=False)
async def api_docs():
    return {"message": "Visit /docs for Swagger UI or /redoc for ReDoc"}
