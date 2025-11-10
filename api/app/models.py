from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ARRAY, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
import uuid

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)  # Vector embedding
    meta_data = Column(JSONB, default={})  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # PDF, CSV, Excel, Text
    file_size = Column(Integer, nullable=False)  # Size in bytes
    status = Column(String, default='processing')  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)  # For widget sessions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    message_type = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    meta_data = Column(JSONB, default={})  # Sources, confidence, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TenantUsage(Base):
    __tablename__ = "tenant_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    queries_count = Column(Integer, default=0)
    documents_count = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, unique=True, index=True)
    company_name = Column(String, nullable=False)
    company_website = Column(String, nullable=True)
    company_logo_url = Column(String, nullable=True)  # URL to uploaded logo
    contact_email = Column(String, nullable=False)
    contact_name = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    allowed_domains = Column(JSONB, default=[])  # List of domains that can embed their widget
    subscription_plan = Column(String, default="starter")  # starter, pro, enterprise
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WidgetConfig(Base):
    __tablename__ = "widget_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, unique=True, index=True)
    widget_title = Column(String, default="Chat Assistant")
    widget_subtitle = Column(String, default="How can I help you?")
    primary_color = Column(String, default="#0066cc")
    secondary_color = Column(String, default="#666666")
    avatar_url = Column(String, nullable=True)
    welcome_message = Column(Text, default="Hello! How can I assist you today?")
    placeholder_text = Column(String, default="Type your message...")
    is_enabled = Column(Boolean, default=True)
    rate_limit_per_hour = Column(Integer, default=100)
    allowed_domains = Column(JSONB, default=["*"])  # Domains that can embed this widget
    custom_css = Column(Text, nullable=True)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AgentConfig(Base):
    __tablename__ = "agent_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, unique=True, index=True)
    agent_name = Column(String, default="Assistant")
    agent_role = Column(String, default="helpful assistant")
    personality_traits = Column(JSONB, default=[])  # ["friendly", "professional", "empathetic"]
    greeting_message = Column(Text, default="Hello! How can I help you today?")
    system_prompt = Column(Text, nullable=True)  # Custom system prompt override
    custom_instructions = Column(Text, nullable=True)  # Additional guidelines
    response_style = Column(String, default="conversational")  # conversational, professional, technical
    industry = Column(String, default="general")
    example_interactions = Column(JSONB, default=[])  # Few-shot examples
    formatting_rules = Column(JSONB, default={})  # Response formatting preferences
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# =====================================================
# SUPERADMIN MODELS
# =====================================================

class SuperAdmin(Base):
    __tablename__ = "superadmins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # First superadmin
    requires_password_change = Column(Boolean, default=False)
    ip_whitelist = Column(JSONB, default=[])
    settings = Column(JSONB, default={})
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sessions = relationship("SuperAdminSession", back_populates="superadmin", cascade="all, delete-orphan")
    audit_logs = relationship("SuperAdminAuditLog", back_populates="superadmin")
    notifications = relationship("SuperAdminNotification", back_populates="superadmin", cascade="all, delete-orphan")

class SuperAdminSession(Base):
    __tablename__ = "superadmin_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    superadmin_id = Column(UUID(as_uuid=True), ForeignKey("superadmins.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    superadmin = relationship("SuperAdmin", back_populates="sessions")

class SuperAdminAuditLog(Base):
    __tablename__ = "superadmin_audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    superadmin_id = Column(UUID(as_uuid=True), ForeignKey("superadmins.id"), nullable=True)
    action = Column(String, nullable=False, index=True)  # e.g., 'customer.view', 'system.setup'
    entity_type = Column(String, nullable=True)  # e.g., 'customer', 'document'
    entity_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True, index=True)
    details = Column(JSONB, default={})
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    superadmin = relationship("SuperAdmin", back_populates="audit_logs")

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    key = Column(String, primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SuperAdminNotification(Base):
    __tablename__ = "superadmin_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    superadmin_id = Column(UUID(as_uuid=True), ForeignKey("superadmins.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # 'alert', 'warning', 'info'
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    data = Column(JSONB, default={})
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    superadmin = relationship("SuperAdmin", back_populates="notifications")