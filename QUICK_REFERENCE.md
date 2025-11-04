# Raggy Muffin Architecture - Quick Reference Guide

## At a Glance

| Component | Type | Location | Port | Language |
|-----------|------|----------|------|----------|
| FastAPI Backend | REST API | `/api/app/` | 8000 | Python 3.11 |
| Admin Dashboard | React UI | `/admin-ui/src/` | 3000 | JavaScript |
| Chat Widget | React UI | `/frontend-ui/src/` | 3001 | JavaScript |
| Super Admin UI | React UI | `/super-admin-ui/src/` | 3003 | JavaScript |
| Streamlit (Legacy) | Dashboard | `/app/` | 8501 | Python |
| PostgreSQL | Database | - | 5432 | SQL |
| Ollama | LLM Service | - | 11434 | - |
| Redis | Cache | - | 6379 | - |

## Key Files by Function

### API Core
- **Main**: `/api/app/main.py` (96 LOC) - FastAPI setup, routing
- **Models**: `/api/app/models.py` (206 LOC) - 13 SQLAlchemy tables
- **Database**: `/api/app/database.py` (58 LOC) - Connection pooling, sessions
- **Config**: `/api/app/config.py` (64 LOC) - Multi-tenant configuration

### Authentication
- `/api/app/auth/cognito.py` - AWS Cognito integration
- `/api/app/auth/dependencies.py` (56 LOC) - JWT verification, tenant extraction

### Routers (REST Endpoints)
- **Chat**: `routers/chat.py` (717 LOC) - Query, streaming, history
- **Widgets**: `routers/widgets.py` (641 LOC) - Widget config, CORS
- **Super Admin**: `routers/superadmin.py` (886 LOC) - Platform management
- **Customer**: `routers/customer.py` (351 LOC) - Profile, usage
- **Agent**: `routers/agent.py` (329 LOC) - Personality config
- **Documents**: `routers/documents.py` (288 LOC) - Upload, management

### RAG Core
- `/api/app/core/rag.py` - Vector search, answer generation, filtering
- `/api/app/core/embedding.py` - Ollama embedding, chunking
- `/api/app/core/document_processor.py` - PDF/CSV/Excel extraction

### Frontend Architecture
- **Admin UI**: Dashboard for document & widget management
- **Widget Frontend**: Public-facing embeddable chat widget
- **Super Admin**: Platform-wide customer & system management

### Database Schema (17 Tables)
```
Core RAG: embeddings, documents, chat_sessions, chat_messages
Tenant: customer_profiles, widget_configs, agent_configs
Usage: tenant_usage
Admin: superadmins, superadmin_sessions, superadmin_audit_log, 
       superadmin_notifications, system_config
```

## Docker Setup Files

| File | Purpose | Services |
|------|---------|----------|
| `docker-compose.yml` | Production base | postgres, ollama, streamlit |
| `docker-compose.dev.yml` | Full development | postgres, api, admin-ui, website, super-admin-ui |
| `docker-compose.cleona.yml` | Cleona production | postgres, redis, ollama, api, 4x UI |
| `docker-compose.frontend-dev.yml` | Frontend only | admin-ui, frontend-ui, super-admin-ui |
| `docker-compose.client-example.yml` | Template | Example client setup |

## Environment Variables (Key)

### Backend (API)
```bash
DATABASE_URL=postgresql://...
OLLAMA_HOST=http://ollama:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2:3b-instruct-q4_0
AWS_COGNITO_USER_POOL_ID=...
AWS_COGNITO_CLIENT_ID=...
AWS_COGNITO_CLIENT_SECRET=...
REDIS_URL=redis://...  # Optional
BRAND_NAME=YourBrand
PRIMARY_COLOR=#6366f1
SECONDARY_COLOR=#64748b
```

### Database
```bash
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=db
```

## Endpoints (API v1)

### Authentication
```
POST /api/v1/auth/login - Login with Cognito
POST /api/v1/auth/logout - Logout
POST /api/v1/auth/refresh - Refresh token
```

### Documents
```
GET  /api/v1/documents/ - List documents (paginated)
POST /api/v1/documents/upload - Upload & process document
GET  /api/v1/documents/{id} - Get document details
DELETE /api/v1/documents/{id} - Delete document
```

### Chat
```
POST /api/v1/chat/query - Query with RAG context
GET  /api/v1/chat/stream - SSE streaming response
GET  /api/v1/chat/sessions/{session_id} - Get conversation
GET  /api/v1/chat/history - Get all sessions
```

### Widgets
```
GET  /api/v1/widgets/config/{tenant_id} - Get widget config
POST /api/v1/widgets/config - Update widget config
GET  /api/v1/widgets/{tenant_id}/embed - Get embed script
```

### Customer
```
GET  /api/v1/customers/profile - Get customer profile
POST /api/v1/customers/profile - Update profile
GET  /api/v1/customers/usage - Get usage analytics
```

### Agent
```
GET  /api/v1/agent/config - Get agent personality
POST /api/v1/agent/config - Update agent config
```

### Super Admin (no /api/v1 prefix)
```
GET  /superadmin/customers - List all customers
GET  /superadmin/customers/{tenant_id} - Get customer
POST /superadmin/customers/{tenant_id}/suspend - Suspend
POST /superadmin/customers/{tenant_id}/activate - Activate
GET  /superadmin/analytics - Platform analytics
GET  /superadmin/audit-logs - Audit trail
GET  /superadmin/system-config - System settings
```

## Data Flow (Chat Query Example)

```
1. User types: "Where can I find housing assistance in Pierce County?"
2. Widget sends POST /api/v1/chat/query with JWT token
3. Backend extracts tenant_id from JWT
4. Embed query using Ollama (768-dim vector)
5. Search embeddings table for similar chunks:
   - SELECT TOP 10 WHERE tenant_id = X
   - Order by vector similarity
6. Filter chunks by location (Pierce County)
7. Generate prompt with top chunks as context
8. Call Ollama llama3.2 with context + system prompt
9. Stream response via SSE or return full response
10. Save message pair to chat_messages table
11. Return to widget with sources & metadata
```

## Multi-Tenant Isolation

```
User Registration → AWS Cognito → JWT with tenant_id
        ↓
FastAPI get_current_tenant_id() dependency
        ↓
Used in ALL database queries:
   - WHERE tenant_id = {tenant_id}
   - Embedded in query joins
   - Validated at API endpoint level
        ↓
CORS Domain validation per tenant
Rate limiting per tenant
Separate widget configs per tenant
```

## Performance Metrics

### Current (Ollama)
- Response time: 3-5+ seconds
- Embedding calls: 20-40 per query
- Throughput: ~50 tokens/sec

### Targets (Post-Migration to Groq + Voyage)
- Response time: 200-500ms
- Embedding calls: 1-2 per query
- Throughput: 500+ tokens/sec
- Cost: ~$150/month for 10K queries/day

## Development Commands

```bash
# Start full dev environment
docker compose -f docker-compose.dev.yml up

# Build API only
docker compose -f docker-compose.dev.yml up dev_api

# Run tests
pytest api/

# Format code
black api/app/

# Database migrations
alembic upgrade head

# Redis CLI
docker exec cleona_redis redis-cli
```

## Database Connection Info

```
Dev: postgresql://dev_user:dev_pass@localhost:5432/dev_db
Prod: postgresql://cleona_user:cleona_secure_pass_2024@localhost:5435/cleona_db
```

## Monitoring & Debugging

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:11434/api/tags  # Ollama
redis-cli ping  # Redis
```

### Logs
```bash
# API logs
docker logs cleona_api

# Ollama logs
docker logs cleona_ollama

# Database logs
docker logs cleona_pgvector
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "No embeddings" | Ollama not running | `docker restart cleona_ollama` |
| Connection timeout | DB not ready | Wait for container startup |
| Auth fails | Invalid JWT | Check Cognito config |
| CORS error | Domain not whitelisted | Add to allowed_domains |
| Slow queries | Missing indexes | Run init.sql again |

## Important Notes

1. **Tenant Isolation**: Critical - ALL queries must filter by tenant_id
2. **Embeddings**: 768-dimensional vectors from nomic-embed-text
3. **Chunking**: Adaptive 150-800 words with 50-word overlap
4. **Rate Limiting**: Per endpoint and per tenant
5. **Widget Security**: Domain whitelist (CORS) enforced
6. **Streaming**: SSE support for real-time responses
7. **Caching**: Redis optional (not required)
8. **Legacy**: Streamlit app deprecated, use React UIs

## For Microservices Migration

**Recommend separating into:**
1. Auth Service (Cognito wrapper)
2. Document Service (upload, processing)
3. Embedding Service (Ollama abstraction)
4. RAG/Chat Service (core logic)
5. Widget Service (config, embed script)
6. Super Admin Service (platform mgmt)
7. Analytics Service (usage tracking)
8. Admin Service (tenant dashboard)

**Shared resources:**
- PostgreSQL (multi-database or schema per service)
- Redis (cache layer)
- Ollama (could be separate service)

