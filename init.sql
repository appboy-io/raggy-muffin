-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Main table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    content TEXT,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT now()
);

-- Optional: example test row (you can remove this)
-- INSERT INTO embeddings (id, tenant_id, content, embedding)
-- VALUES ('00000000-0000-0000-0000-000000000001', 'test_tenant', 'Example text.', '[0.0, 0.1, ..., 0.768]');
