-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if they exist (for clean recreation)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS widget_configs CASCADE;
DROP TABLE IF EXISTS customer_profiles CASCADE;
DROP TABLE IF EXISTS tenant_usage CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS embeddings CASCADE;

-- Embeddings table for vector search
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for embeddings
CREATE INDEX idx_embeddings_tenant_id ON embeddings(tenant_id);
CREATE INDEX idx_embeddings_meta_data ON embeddings USING GIN(meta_data);

-- Documents table for file management
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    status TEXT DEFAULT 'processing',
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for documents
CREATE INDEX idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_meta_data ON documents USING GIN(meta_data);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for chat sessions
CREATE INDEX idx_chat_sessions_tenant_id ON chat_sessions(tenant_id);
CREATE INDEX idx_chat_sessions_session_id ON chat_sessions(session_id);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    tenant_id TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for chat messages
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_tenant_id ON chat_messages(tenant_id);
CREATE INDEX idx_chat_messages_meta_data ON chat_messages USING GIN(meta_data);

-- Tenant usage tracking table
CREATE TABLE tenant_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    queries_count INTEGER DEFAULT 0,
    documents_count INTEGER DEFAULT 0,
    storage_used_mb FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for tenant usage
CREATE INDEX idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
CREATE INDEX idx_tenant_usage_date ON tenant_usage(date);

-- Customer profiles table
CREATE TABLE customer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    company_website TEXT,
    contact_email TEXT NOT NULL,
    contact_name TEXT,
    industry TEXT,
    allowed_domains JSONB DEFAULT '[]',
    subscription_plan TEXT DEFAULT 'starter',
    is_active BOOLEAN DEFAULT true,
    onboarding_completed BOOLEAN DEFAULT false,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for customer profiles
CREATE UNIQUE INDEX idx_customer_profiles_tenant_id ON customer_profiles(tenant_id);
CREATE INDEX idx_customer_profiles_meta_data ON customer_profiles USING GIN(meta_data);

-- Widget configurations table
CREATE TABLE widget_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL UNIQUE,
    widget_title TEXT DEFAULT 'Chat Assistant',
    widget_subtitle TEXT DEFAULT 'How can I help you?',
    primary_color TEXT DEFAULT '#0066cc',
    secondary_color TEXT DEFAULT '#666666',
    avatar_url TEXT,
    welcome_message TEXT DEFAULT 'Hello! How can I assist you today?',
    placeholder_text TEXT DEFAULT 'Type your message...',
    is_enabled BOOLEAN DEFAULT true,
    rate_limit_per_hour INTEGER DEFAULT 100,
    allowed_domains JSONB DEFAULT '["*"]',
    custom_css TEXT,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for widget configs
CREATE UNIQUE INDEX idx_widget_configs_tenant_id ON widget_configs(tenant_id);
CREATE INDEX idx_widget_configs_meta_data ON widget_configs USING GIN(meta_data);

-- Performance Optimization: Composite Indexes for Common Query Patterns
-- These indexes significantly improve query performance for multi-tenant operations

-- High Priority Composite Indexes

-- 1. Embeddings vector search with tenant filtering (Most Critical for RAG performance)
CREATE INDEX idx_embeddings_tenant_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 2. Chat session compound lookup (tenant + session_id)
CREATE INDEX idx_chat_sessions_tenant_session ON chat_sessions(tenant_id, session_id);

-- 3. Chat messages by session and time (for message history)
CREATE INDEX idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- 4. Chat sessions by tenant and activity (for session listing)
CREATE INDEX idx_chat_sessions_tenant_activity ON chat_sessions(tenant_id, last_activity DESC);

-- Medium Priority Composite Indexes

-- 5. Document status by tenant (for filtering)
CREATE INDEX idx_documents_tenant_status ON documents(tenant_id, status);

-- 6. Tenant usage time series (for analytics)
CREATE INDEX idx_tenant_usage_tenant_date ON tenant_usage(tenant_id, date DESC);

-- 7. Chat messages by tenant and type (for analytics)
CREATE INDEX idx_chat_messages_tenant_type ON chat_messages(tenant_id, message_type, created_at);

-- Additional Performance Indexes

-- 8. Document ordering by tenant and creation time
CREATE INDEX idx_documents_tenant_created ON documents(tenant_id, created_at DESC);

-- 9. Embeddings with document metadata filtering
CREATE INDEX idx_embeddings_tenant_meta ON embeddings(tenant_id) WHERE meta_data ? 'document_id';
