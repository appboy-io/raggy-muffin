from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
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