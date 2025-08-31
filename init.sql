-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table for vector search
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for embeddings
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant_id ON embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_meta_data ON embeddings USING GIN(meta_data);

-- Documents table for file management
CREATE TABLE IF NOT EXISTS documents (
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
CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_meta_data ON documents USING GIN(meta_data);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for chat sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant_id ON chat_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    tenant_id TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for chat messages
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_tenant_id ON chat_messages(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_meta_data ON chat_messages USING GIN(meta_data);

-- Tenant usage tracking table
CREATE TABLE IF NOT EXISTS tenant_usage (
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
CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_date ON tenant_usage(date);

-- Customer profiles table
CREATE TABLE IF NOT EXISTS customer_profiles (
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
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_customer_profiles_tenant_id') THEN
        CREATE UNIQUE INDEX idx_customer_profiles_tenant_id ON customer_profiles(tenant_id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_customer_profiles_meta_data ON customer_profiles USING GIN(meta_data);

-- Widget configurations table
CREATE TABLE IF NOT EXISTS widget_configs (
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
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_widget_configs_tenant_id') THEN
        CREATE UNIQUE INDEX idx_widget_configs_tenant_id ON widget_configs(tenant_id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_widget_configs_meta_data ON widget_configs USING GIN(meta_data);

-- Performance Optimization: Composite Indexes for Common Query Patterns
-- These indexes significantly improve query performance for multi-tenant operations

-- High Priority Composite Indexes

-- 1. Embeddings vector search with tenant filtering (Most Critical for RAG performance)
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 2. Chat session compound lookup (tenant + session_id)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant_session ON chat_sessions(tenant_id, session_id);

-- 3. Chat messages by session and time (for message history)
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- 4. Chat sessions by tenant and activity (for session listing)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant_activity ON chat_sessions(tenant_id, last_activity DESC);

-- Medium Priority Composite Indexes

-- 5. Document status by tenant (for filtering)
CREATE INDEX IF NOT EXISTS idx_documents_tenant_status ON documents(tenant_id, status);

-- 6. Tenant usage time series (for analytics)
CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_date ON tenant_usage(tenant_id, date DESC);

-- 7. Chat messages by tenant and type (for analytics)
CREATE INDEX IF NOT EXISTS idx_chat_messages_tenant_type ON chat_messages(tenant_id, message_type, created_at);

-- Additional Performance Indexes

-- 8. Document ordering by tenant and creation time
CREATE INDEX IF NOT EXISTS idx_documents_tenant_created ON documents(tenant_id, created_at DESC);

-- 9. Embeddings with document metadata filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant_meta ON embeddings(tenant_id) WHERE meta_data ? 'document_id';

-- =====================================================
-- SUPERADMIN TABLES
-- =====================================================

-- Superadmins table (separate from tenant users)
CREATE TABLE IF NOT EXISTS superadmins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false, -- Mark the first/primary superadmin
    requires_password_change BOOLEAN DEFAULT false,
    ip_whitelist JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for superadmins
CREATE INDEX IF NOT EXISTS idx_superadmins_username ON superadmins(username);
CREATE INDEX IF NOT EXISTS idx_superadmins_email ON superadmins(email);
CREATE INDEX IF NOT EXISTS idx_superadmins_is_active ON superadmins(is_active);

-- Superadmin sessions table for token management
CREATE TABLE IF NOT EXISTS superadmin_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    superadmin_id UUID NOT NULL REFERENCES superadmins(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    ip_address TEXT,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for sessions
CREATE INDEX IF NOT EXISTS idx_superadmin_sessions_token ON superadmin_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_superadmin_sessions_expires ON superadmin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_superadmin_sessions_superadmin ON superadmin_sessions(superadmin_id);

-- Audit log for superadmin actions
CREATE TABLE IF NOT EXISTS superadmin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    superadmin_id UUID REFERENCES superadmins(id),
    action TEXT NOT NULL, -- e.g., 'customer.view', 'customer.suspend', 'system.configure'
    entity_type TEXT, -- e.g., 'customer', 'document', 'system'
    entity_id TEXT, -- ID of the affected entity
    tenant_id TEXT, -- Affected tenant if applicable
    details JSONB DEFAULT '{}', -- Additional context about the action
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_superadmin ON superadmin_audit_log(superadmin_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON superadmin_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON superadmin_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON superadmin_audit_log(created_at DESC);

-- System configuration table for global settings
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Initialize system configuration
INSERT INTO system_config (key, value, description) VALUES
    ('setup_complete', 'false'::jsonb, 'Whether initial superadmin setup is complete'),
    ('system_locked', 'false'::jsonb, 'Emergency system lock'),
    ('maintenance_mode', 'false'::jsonb, 'System maintenance mode'),
    ('allowed_registration_domains', '[]'::jsonb, 'Email domains allowed for self-registration'),
    ('global_rate_limits', '{"api": 1000, "widget": 100}'::jsonb, 'Global rate limits per hour'),
    ('system_version', '"1.0.0"'::jsonb, 'Current system version')
ON CONFLICT (key) DO NOTHING;

-- Superadmin notifications table
CREATE TABLE IF NOT EXISTS superadmin_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    superadmin_id UUID REFERENCES superadmins(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- 'alert', 'warning', 'info'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_superadmin ON superadmin_notifications(superadmin_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON superadmin_notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON superadmin_notifications(created_at DESC);
