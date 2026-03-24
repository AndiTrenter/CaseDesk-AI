"""
CaseDesk AI - Database Models
SQLAlchemy models for PostgreSQL (Docker) with MongoDB fallback (development)
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    TEAM = "team"


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    CLOSED = "closed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class DocumentType(str, Enum):
    LETTER = "letter"
    INVOICE = "invoice"
    CONTRACT = "contract"
    FORM = "form"
    RECEIPT = "receipt"
    ID_DOCUMENT = "id_document"
    OTHER = "other"


class AIProviderType(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    DISABLED = "disabled"


class InternetAccessLevel(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"


# Base Models
class BaseDocument(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)


# User Models
class UserBase(BaseDocument):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    language: str = "de"


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    language: str = "de"


class User(UserBase):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_login: Optional[datetime] = None


class UserInDB(User):
    password_hash: str


# Settings Models
class SystemSettings(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    setup_completed: bool = False
    default_language: str = "de"
    ai_provider: AIProviderType = AIProviderType.DISABLED
    openai_api_key: Optional[str] = None
    internet_access: InternetAccessLevel = InternetAccessLevel.DENIED
    allow_external_ai: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class UserSettings(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    language: str = "de"
    theme: str = "dark"
    notifications_enabled: bool = True
    ai_provider_override: Optional[AIProviderType] = None
    internet_access_override: Optional[InternetAccessLevel] = None


# Mail Account Models
class MailAccountBase(BaseDocument):
    email: EmailStr
    display_name: str
    imap_server: str
    imap_port: int = 993
    imap_use_ssl: bool = True
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_use_tls: bool = True
    is_active: bool = True


class MailAccountCreate(MailAccountBase):
    password: str


class MailAccount(MailAccountBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    last_sync: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


# Case Models
class CaseBase(BaseDocument):
    title: str
    description: Optional[str] = None
    reference_number: Optional[str] = None
    status: CaseStatus = CaseStatus.OPEN
    tags: List[str] = []


class CaseCreate(CaseBase):
    pass


class Case(CaseBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    document_ids: List[str] = []
    email_ids: List[str] = []
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# Document Models
class DocumentBase(BaseDocument):
    filename: str
    original_filename: str
    mime_type: str
    size: int
    document_type: DocumentType = DocumentType.OTHER


class DocumentCreate(DocumentBase):
    case_id: Optional[str] = None


class Document(DocumentBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    case_id: Optional[str] = None
    storage_path: str
    ocr_text: Optional[str] = None
    ocr_processed: bool = False
    metadata: dict = {}
    sender: Optional[str] = None
    recipient: Optional[str] = None
    document_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# Email Models
class EmailMessageBase(BaseDocument):
    subject: str
    sender: str
    recipients: List[str] = []
    cc: List[str] = []
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime


class EmailMessage(EmailMessageBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    mail_account_id: str
    case_id: Optional[str] = None
    message_id: str  # IMAP message ID
    attachment_ids: List[str] = []
    is_read: bool = False
    is_processed: bool = False
    ai_summary: Optional[str] = None
    detected_deadlines: List[datetime] = []
    created_at: datetime = Field(default_factory=utc_now)


# Attachment Models
class Attachment(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    email_id: str
    document_id: Optional[str] = None  # Link to created document
    filename: str
    mime_type: str
    size: int
    storage_path: str


# Task Models
class TaskBase(BaseDocument):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    case_id: Optional[str] = None


class Task(TaskBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    email_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None


# Event Models
class EventBase(BaseDocument):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    location: Optional[str] = None


class EventCreate(EventBase):
    case_id: Optional[str] = None


class Event(EventBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    is_deadline: bool = False
    reminder_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# Draft Models
class DraftBase(BaseDocument):
    title: str
    content: str
    draft_type: str = "letter"  # letter, email, form
    language: str = "de"


class DraftCreate(DraftBase):
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    email_id: Optional[str] = None


class Draft(DraftBase):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    email_id: Optional[str] = None
    ai_generated: bool = False
    is_sent: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# AI Chat Models
class ChatMessage(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    session_id: str
    role: str  # user, assistant, system
    content: str
    case_id: Optional[str] = None
    document_ids: List[str] = []
    created_at: datetime = Field(default_factory=utc_now)


# Audit Log Models
class AuditLog(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: dict = {}
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


# AI Provider Config
class AIProviderConfig(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    provider: AIProviderType
    api_key: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    is_active: bool = True


# API Response Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class SetupStatus(BaseModel):
    is_configured: bool = False
    setup_completed: bool = False
    has_admin: bool
    version: str = "1.0.0"


# AI Memory / User Profile Models
class AIProfileFact(BaseDocument):
    key: str
    value: str
    source: str = "conversation"
    extracted_at: datetime = Field(default_factory=utc_now)


class AIProfile(BaseDocument):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    facts: List[AIProfileFact] = []
    summary: str = ""
    updated_at: datetime = Field(default_factory=utc_now)
