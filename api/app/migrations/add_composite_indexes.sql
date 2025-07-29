-- Performance optimization: Add composite indexes for common query patterns
-- This migration adds composite indexes to improve query performance

-- High Priority Indexes (Performance Critical)

-- 1. Embeddings vector search with tenant filtering (Most Critical)
-- This is the primary performance bottleneck for RAG queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_tenant_vector 
ON embeddings(tenant_id) INCLUDE (embedding, content);

-- 2. Chat session compound lookup (tenant + session_id)
-- Used for session retrieval and validation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_sessions_tenant_session 
ON chat_sessions(tenant_id, session_id);

-- 3. Chat messages by session and time (for message history)
-- Critical for chat history display
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_messages_session_created 
ON chat_messages(session_id, created_at);

-- 4. Chat sessions by tenant and activity (for session listing)
-- Used for dashboard and session management
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_sessions_tenant_activity 
ON chat_sessions(tenant_id, last_activity DESC);

-- Medium Priority Indexes (Query Optimization)

-- 5. Document status by tenant (for filtering)
-- Used for document management and status tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_tenant_status 
ON documents(tenant_id, status);

-- 6. Tenant usage time series (for analytics)
-- Used for usage tracking and billing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_usage_tenant_date 
ON tenant_usage(tenant_id, date DESC);

-- 7. Chat messages by tenant and type (for analytics)
-- Used for message analytics and filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_messages_tenant_type 
ON chat_messages(tenant_id, message_type, created_at);

-- Additional Performance Indexes

-- 8. Document ordering by tenant and creation time
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_tenant_created 
ON documents(tenant_id, created_at DESC);

-- 9. Embeddings with document metadata filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_tenant_meta 
ON embeddings(tenant_id) 
WHERE meta_data ? 'document_id';

-- Analysis queries to check index usage after deployment:
-- 
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
-- FROM pg_stat_user_indexes 
-- WHERE indexname LIKE 'idx_%tenant%' 
-- ORDER BY idx_scan DESC;
--
-- SELECT query, calls, total_time, mean_time 
-- FROM pg_stat_statements 
-- WHERE query LIKE '%tenant_id%' 
-- ORDER BY total_time DESC 
-- LIMIT 10;