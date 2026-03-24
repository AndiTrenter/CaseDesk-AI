"""
CaseDesk AI - Shared Dependencies
Database, authentication, utilities shared across all routers
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
import hashlib
import jwt
import uuid
import logging

from models import UserRole

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB
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

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def create_access_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
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
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    if user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def log_action(user_id: str, action: str, resource_type: str, resource_id: str = None, details: dict = None):
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(log_entry)


async def get_user_language(user: dict) -> str:
    """Get user's preferred language from settings"""
    user_settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return (user_settings or {}).get("language") or user.get("language") or "de"
