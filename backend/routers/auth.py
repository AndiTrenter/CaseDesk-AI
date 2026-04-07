"""Auth, Users & Invitations Router"""
from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, timezone, timedelta
from typing import List
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from deps import db, require_auth, require_admin, log_action, hash_password, verify_password, create_access_token
from models import User, UserCreate, UserRole, Token, SetupStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "casedesk-backend", "version": "1.1.4"}


@router.get("/setup/status", response_model=SetupStatus)
async def get_setup_status():
    admin_count = await db.users.count_documents({"role": "admin"})
    logger.info(f"Setup status check: admin_count={admin_count}")
    settings = await db.system_settings.find_one({}, {"_id": 0})
    return SetupStatus(
        is_configured=admin_count > 0,
        has_admin=admin_count > 0,
        version="1.1.4"
    )


@router.post("/setup/init")
async def initialize_setup(
    admin_email: str = Form(...),
    admin_username: str = Form(...),
    admin_password: str = Form(...),
    admin_full_name: str = Form(None),
    language: str = Form("de"),
    ai_provider: str = Form("ollama"),
    openai_api_key: str = Form(None),
    internet_access: str = Form("denied"),
    organization_name: str = Form(None),
):
    existing_admin = await db.users.count_documents({"role": UserRole.ADMIN})
    if existing_admin > 0:
        raise HTTPException(status_code=400, detail="Setup already completed")
    
    now = datetime.now(timezone.utc).isoformat()
    admin_id = str(uuid.uuid4())
    
    admin_user = {
        "id": admin_id,
        "email": admin_email,
        "username": admin_username,
        "full_name": admin_full_name or admin_username,
        "password_hash": hash_password(admin_password),
        "role": UserRole.ADMIN,
        "is_active": True,
        "language": language,
        "created_at": now,
        "updated_at": now,
        "last_login": now
    }
    await db.users.insert_one(admin_user)
    
    system_settings = {
        "id": str(uuid.uuid4()),
        "organization_name": organization_name or "CaseDesk",
        "ai_provider": ai_provider,
        "allow_external_ai": ai_provider == "openai",
        "openai_api_key": openai_api_key if ai_provider == "openai" else None,
        "internet_access": internet_access,
        "default_language": language,
        "created_at": now,
        "updated_at": now
    }
    await db.system_settings.insert_one(system_settings)
    
    await db.user_settings.insert_one({
        "user_id": admin_id,
        "language": language,
        "theme": "dark",
        "notifications_enabled": True
    })
    
    token = create_access_token(admin_id, admin_email, UserRole.ADMIN)
    
    return {
        "success": True,
        "message": "Setup completed successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": admin_id,
            "email": admin_email,
            "username": admin_username,
            "role": UserRole.ADMIN,
            "language": language,
            "full_name": admin_full_name or admin_username
        }
    }


@router.post("/auth/login")
async def login(email: str = Form(...), password: str = Form(...)):
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    token = create_access_token(user["id"], user["email"], user["role"])
    
    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/auth/me")
async def get_current_user_info(user: dict = Depends(require_auth)):
    return user


@router.post("/auth/logout")
async def logout(user: dict = Depends(require_auth)):
    await log_action(user["id"], "logout", "user", user["id"])
    return {"success": True, "message": "Logged out"}


@router.get("/users", response_model=List[User])
async def list_users(user: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [User(**u) for u in users]


@router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, admin: dict = Depends(require_admin)):
    existing = await db.users.find_one({"$or": [{"email": user_data.email}, {"username": user_data.username}]})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    user_id = str(uuid.uuid4())
    
    new_user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name or user_data.username,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "is_active": True,
        "language": user_data.language,
        "created_at": now,
        "updated_at": now
    }
    await db.users.insert_one(new_user)
    await log_action(admin["id"], "create_user", "user", user_id)
    return User(**new_user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_action(admin["id"], "delete_user", "user", user_id)
    return {"success": True, "message": "User deleted"}


@router.post("/users/invite")
async def invite_user(
    email: str = Form(...),
    role: str = Form("user"),
    admin: dict = Depends(require_admin)
):
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    existing_invite = await db.invitations.find_one({"email": email, "used": False})
    if existing_invite:
        await db.invitations.delete_one({"id": existing_invite["id"]})
    
    invitation_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    invitation = {
        "id": invitation_id,
        "email": email,
        "role": role,
        "token": token,
        "invited_by": admin["id"],
        "invited_by_name": admin.get("full_name", admin.get("username")),
        "used": False,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat()
    }
    await db.invitations.insert_one(invitation)
    
    invitation_url = f"/register/{token}"
    
    mail_accounts = await db.mail_accounts.find({"user_id": admin["id"]}).to_list(1)
    email_sent = False
    if mail_accounts:
        try:
            email_sent = await send_invitation_email(
                email, invitation_url, admin.get("full_name", admin.get("username")),
                mail_accounts[0]
            )
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}")
    
    await log_action(admin["id"], "invite_user", "invitation", invitation_id, {"email": email, "role": role})
    
    return {
        "success": True,
        "invitation_id": invitation_id,
        "token": token,
        "invitation_url": invitation_url,
        "email_sent": email_sent,
        "expires_at": invitation["expires_at"]
    }


async def send_invitation_email(to_email: str, invitation_url: str, invited_by: str, mail_account: dict) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = mail_account['email']
        msg['To'] = to_email
        msg['Subject'] = 'Einladung zu CaseDesk AI'
        
        body = f"""Hallo,

Sie wurden von {invited_by} zu CaseDesk AI eingeladen.

Klicken Sie auf den folgenden Link, um Ihren Account zu erstellen:
{invitation_url}

Diese Einladung ist 7 Tage gültig.

Mit freundlichen Grüßen,
CaseDesk AI"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        smtp_server = mail_account.get('smtp_server', mail_account.get('imap_server', '').replace('imap', 'smtp'))
        smtp_port = mail_account.get('smtp_port', 587)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if mail_account.get('smtp_use_tls', True):
                server.starttls()
            server.login(mail_account['email'], mail_account['password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


@router.get("/users/invitations")
async def list_invitations(admin: dict = Depends(require_admin)):
    invitations = await db.invitations.find(
        {"used": False}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return invitations


@router.delete("/users/invitations/{invitation_id}")
async def cancel_invitation(invitation_id: str, admin: dict = Depends(require_admin)):
    result = await db.invitations.delete_one({"id": invitation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    await log_action(admin["id"], "cancel_invitation", "invitation", invitation_id)
    return {"success": True, "message": "Invitation cancelled"}


@router.get("/auth/invitation/{token}")
async def validate_invitation(token: str):
    invitation = await db.invitations.find_one({"token": token, "used": False}, {"_id": 0})
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    now = datetime.now(timezone.utc).isoformat()
    if invitation.get("expires_at") and invitation["expires_at"] < now:
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    return {
        "valid": True,
        "email": invitation["email"],
        "role": invitation["role"],
        "invited_by": invitation.get("invited_by_name", "Admin")
    }


@router.post("/auth/register/{token}")
async def register_with_invitation(
    token: str,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None)
):
    invitation = await db.invitations.find_one({"token": token, "used": False}, {"_id": 0})
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    now_str = datetime.now(timezone.utc).isoformat()
    if invitation.get("expires_at") and invitation["expires_at"] < now_str:
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    existing = await db.users.find_one({"$or": [{"email": invitation["email"]}, {"username": username}]})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "email": invitation["email"],
        "username": username,
        "full_name": full_name or username,
        "password_hash": hash_password(password),
        "role": invitation.get("role", "user"),
        "is_active": True,
        "language": "de",
        "created_at": now_str,
        "updated_at": now_str
    }
    await db.users.insert_one(new_user)
    
    await db.invitations.update_one(
        {"token": token},
        {"$set": {"used": True, "used_at": now_str, "user_id": user_id}}
    )
    
    await db.user_settings.insert_one({
        "user_id": user_id,
        "language": "de",
        "theme": "dark",
        "notifications_enabled": True
    })
    
    access_token = create_access_token(user_id, invitation["email"], invitation.get("role", "user"))
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": invitation["email"],
            "username": username,
            "role": invitation.get("role", "user"),
            "full_name": full_name or username
        }
    }
