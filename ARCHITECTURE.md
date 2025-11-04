# Raggy Muffin RAG Platform - Current Architecture Summary

## Overview
Raggy Muffin is a multi-tenant Retrieval-Augmented Generation (RAG) platform that enables businesses to upload documents and deploy AI-powered chat assistants via embeddable widgets. The platform features white-label support, Ollama-based embeddings and LLM, and comprehensive tenant isolation.

---

## 1. Main Application Components

### A. Backend API
- **Framework**: FastAPI (Python 3.11)
- **Type**: RESTful API with real-time streaming support
- **Port**: 8000 (internal)
- **Location**: `/home/cleona_app/raggy-muffin/api/app/`

### B. Frontend Applications (3 React UIs)
1. **Admin UI** - Tenant admin dashboard
   - Port: 3000
   - Location: `/admin-ui/`
   - Purpose: Document management, widget configuration, usage analytics

2. **Widget Frontend** - Public-facing chat widget
   - Port: 3001
   - Location: `/frontend-ui/`
   - Purpose: Customer-facing chat interface

3. **Super Admin UI** - Platform administration
   - Port: 3003 (dev) / 3000 (in prod)
   - Location: `/super-admin-ui/`
   - Purpose: Customer management, system configuration, billing, auditing

### C. Legacy Streamlit Dashboard
- **Port**: 8501
- **Location**: `/app/`
- **Status**: Legacy app, being deprecated in favor of React UI
- **Purpose**: Original document upload interface

---

## 2. Directory Structure

```
/home/cleona_app/raggy-muffin/
├── api/                              # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app setup
│   │   ├── models.py                # SQLAlchemy ORM models (17 tables)
│   │   ├── database.py              # Database initialization & pooling
│   │   ├── config.py                # Configuration management
│   │   ├── cache.py                 # Redis caching utilities
│   │   ├── auth/
│   │   │   ├── cognito.py          # AWS Cognito integration
│   │   │   ├── routes.py           # Authentication endpoints
│   │   │   └── dependencies.py     # JWT verification & tenant extraction
│   │   ├── core/                    # RAG core functionality
│   │   │   ├── rag.py              # Vector search, chunk filtering, LLM generation
│   │   │   ├── embedding.py        # Ollama embedding service
│   │   │   └── document_processor.py # PDF/CSV/Excel/Text extraction
│   │   ├── routers/                 # API endpoints (3,200 LOC total)
│   │   │   ├── chat.py             # Chat messaging & streaming (717 LOC)
│   │   │   ├── documents.py        # Document upload & management (288 LOC)
│   │   │   ├── widgets.py          # Widget configuration (641 LOC)
│   │   │   ├── customer.py         # Customer profile management (351 LOC)
│   │   │   ├── agent.py            # Agent personality configuration (329 LOC)
│   │   │   └── superadmin.py       # Super admin operations (886 LOC)
│   │   ├── utils/
│   │   │   └── rate_limit.py       # Rate limiting for endpoints
│   │   └── middleware/
│   │       └── setup_check.py      # Setup wizard enforcement
│   ├── Dockerfile                   # Multi-stage build
│   └── requirements.txt             # Python dependencies
│
├── admin-ui/                        # Admin dashboard React app
│   ├── src/
│   │   ├── pages/                  # Dashboard pages
│   │   ├── components/             # React components
│   │   ├── context/                # Context API for state
│   │   └── services/               # API client services
│   ├── Dockerfile & Dockerfile.dev
│   └── package.json
│
├── frontend-ui/                     # Customer-facing widget
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── context/
│   │   ├── services/
│   │   ├── utils/
│   │   └── hooks/
│   ├── Dockerfile
│   └── package.json
│
├── super-admin-ui/                  # Super admin platform dashboard
│   ├── src/
│   │   ├── pages/                  # Dashboard pages
│   │   ├── components/             # Admin components
│   │   └── services/               # Admin API clients
│   ├── Dockerfile
│   └── package.json
│
├── app/                             # Legacy Streamlit app (17 Python files)
│   ├── app.py                      # Main Streamlit entry point
│   ├── rag.py                      # Legacy RAG implementation
│   ├── upload_workflow.py           # Document processing workflow
│   ├── document_manager.py
│   ├── embedding.py
│   └── ... (other modules)
│
├── docker-compose.yml               # Base production compose
├── docker-compose.dev.yml           # Development multi-service setup
├── docker-compose.cleona.yml        # Cleona-specific deployment
├── docker-compose.frontend-dev.yml  # Frontend dev-only
├── docker-compose.client-example.yml # Example client setup
│
├── init.sql                         # Database schema initialization
├── redis.conf                       # Redis configuration
├── Dockerfile                       # Streamlit Dockerfile
├── Dockerfile.ollama                # Ollama container builder
│
├── requirements.txt                 # Streamlit app requirements
├── CLAUDE.md                        # Project documentation
├── CLAUDE.local.md                  # Local setup notes
├── README.md
└── .env.example                     # Environment variables template
```

---

## 3. Databases and External Services

### Database: PostgreSQL with pgvector
- **Image**: `ankane/pgvector` (PostgreSQL 14+ with pgvector extension)
- **Port**: 5432
- **Type**: Multi-tenant relational database
- **Key Features**:
  - pgvector for vector similarity search
  - JSONB columns for flexible metadata storage
  - Composite indexes for performance optimization

### Embedded Vector Store
- **Service**: Ollama (local LLM)
- **Image**: Custom build from `Dockerfile.ollama`
- **Port**: 11434
- **Models**:
  - Embedding: `nomic-embed-text` (768-dimensional vectors)
  - Chat: `llama3.2:3b-instruct-q4_0` (quantized 3B model)
- **Volume**: `ollama:/root/.ollama` (persistent model storage)

### Cache: Redis
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Configuration**: `redis.conf`
- **Volume**: `cleona_redis_data:/data`
- **Purpose**: Response caching, session management

### External Services
- **Authentication**: AWS Cognito (JWT-based)
- **File Storage**: Local `/app/static/avatars` or cloud integration

---

## 4. Database Schema (17 Tables)

### Core RAG Tables
1. **embeddings**
   - Vector embeddings for documents (pgvector 768-dim)
   - JSONB metadata (document_id, chunk_index, etc.)
   - Indexed for vector similarity search

2. **documents**
   - Uploaded files metadata (filename, type, size)
   - Status tracking (processing, completed, failed)
   - Chunk count tracking

3. **chat_sessions**
   - Conversation sessions per tenant
   - Session tracking with last_activity timestamp

4. **chat_messages**
   - Individual messages in conversations
   - Types: user, assistant, system
   - Metadata: sources, confidence scores

### Tenant Management
5. **customer_profiles**
   - Company information (name, website, logo)
   - Subscription plan tracking
   - Widget domain whitelist (CORS)
   - Onboarding status

6. **widget_configs**
   - Chat widget customization per tenant
   - Colors, title, welcome message
   - Rate limiting per widget
   - Custom CSS support

7. **agent_configs**
   - Agent personality (name, role, traits)
   - System prompt customization
   - Response style configuration
   - Few-shot examples

### Analytics and Usage
8. **tenant_usage**
   - Daily query counts per tenant
   - Document counts per tenant
   - Storage usage tracking (MB)

### Super Admin Tables
9. **superadmins**
   - Platform administrators
   - Password hashing (bcrypt)
   - IP whitelist support
   - Login tracking (last_login, failed_attempts, locked_until)

10. **superadmin_sessions**
    - Active admin sessions
    - Token-based access with expiration
    - IP and user agent tracking

11. **superadmin_audit_log**
    - Complete audit trail of admin actions
    - Action type (e.g., 'customer.view', 'system.setup')
    - IP/user agent logging

12. **superadmin_notifications**
    - Admin alerts and notifications
    - Types: alert, warning, info
    - Read/unread tracking

13. **system_config**
    - Platform-wide settings
    - Feature flags
    - System configuration (JSONB)

### Additional tables: migrations directory for schema versioning

---

## 5. API Routers and Endpoints

### Authentication Router (`/api/v1/auth`)
- User login/logout
- Token verification
- AWS Cognito integration

### Documents Router (`/api/v1/documents`)
- `GET /` - List documents (paginated)
- `POST /upload` - Upload new document
- `GET /{id}` - Get document details
- `DELETE /{id}` - Delete document
- Background processing with status tracking

### Chat Router (`/api/v1/chat`)
- `POST /query` - Query with RAG context
- `GET /stream` - Server-Sent Events streaming
- `GET /sessions/{session_id}` - Get conversation history
- CORS validation for widget domains
- Location-based filtering for results

### Widgets Router (`/api/v1/widgets`)
- `GET /config/{tenant_id}` - Get widget configuration
- `POST /config` - Update widget config
- Widget embed script generation
- Tenant-specific CORS configuration

### Customer Router (`/api/v1/customers`)
- `GET /profile` - Get customer profile
- `POST /profile` - Update profile
- `GET /usage` - Get usage analytics
- `POST /verify-domain` - CORS domain validation

### Agent Router (`/api/v1/agent`)
- `GET /config` - Get agent personality config
- `POST /config` - Update agent configuration
- System prompt customization

### Super Admin Router (`/superadmin`)
- **Customers**: List, view, suspend, activate
- **Analytics**: Platform-wide metrics
- **System Config**: Feature flags, settings
- **Audit Logs**: Complete action history
- **Superadmin Management**: Create/manage admin accounts

---

## 6. Core Processing Pipeline

### Document Processing Flow
```
Upload File
  ↓
Validate (file size, type)
  ↓
Extract Text (PDF/CSV/Excel/TXT)
  ↓
Chunk Text (adaptive 150-800 words/chunk with overlap)
  ↓
Generate Embeddings (Ollama nomic-embed-text)
  ↓
Store in PostgreSQL + pgvector
  ↓
Update Document Status → Complete
```

### Chat Query Flow
```
User Message
  ↓
Generate Query Embedding
  ↓
Vector Similarity Search (pgvector)
  ↓
Location-Based Filtering (if applicable)
  ↓
Semantic Relevance Filtering (upcoming feature)
  ↓
Generate Answer (Ollama llama3.2)
  ↓
Stream/Return Response with Sources
  ↓
Save to Chat History
```

---

## 7. Background Workers and Async Tasks

### Async Processing
- **Document embeddings**: Processed asynchronously after upload
- **Chat responses**: Optional SSE streaming for real-time feedback
- **Rate limiting**: Per-endpoint and per-tenant limits

### Job Processing
- No explicit task queue (Celery/RQ)
- Uses asyncio for concurrent operations
- Direct processing within FastAPI endpoints

### Caching Strategy
- Redis optional (not configured in dev)
- Function-level caching decorators available
- TTL-based cache invalidation

---

## 8. Authentication and Security

### Auth Flow
1. AWS Cognito user pool login
2. JWT token issued by Cognito
3. Token verification in FastAPI dependencies
4. Tenant ID extracted from token
5. Tenant isolation enforced at database query level

### Security Features
- HTTP Bearer token authentication
- Password hashing (bcrypt in superadmin)
- CORS validation per tenant
- Widget domain whitelist enforcement
- Rate limiting per endpoint/tenant
- IP whitelist support for super admins
- Admin session tracking and expiration

---

## 9. Docker and Deployment Configuration

### Development Setup (docker-compose.dev.yml)
Services:
- `dev_pgvector` (PostgreSQL)
- `dev_api` (FastAPI)
- `dev_admin_ui` (React)
- `dev_website` (Streamlit)
- `dev_super_admin_ui` (React)

### Production Setup (docker-compose.cleona.yml)
Services:
- `cleona_pgvector` (PostgreSQL)
- `cleona_redis` (Redis cache)
- `cleona_ollama` (Ollama LLM)
- `cleona_api` (FastAPI)
- `cleona_admin_ui` (React)
- `cleona_frontend_ui` (Widget)
- `cleona_super_admin_ui` (Platform admin)
- `cleona_streamlit` (Legacy app)

### Resource Limits (Production)
```
PostgreSQL:  2GB RAM, 1.0 CPU
Redis:       1GB RAM, 0.5 CPU
Ollama:      6GB RAM, 2.0 CPU (limits)
API:         2GB RAM, 1.0 CPU
UIs:         512MB-1GB RAM, 0.25-0.5 CPU
```

### Dockerfile Strategy
- Multi-stage builds for optimization
- Non-root user execution
- Health checks (Ollama)
- Volume mounting for development
- Static file serving

---

## 10. Technology Stack Summary

### Backend
- FastAPI 0.104
- SQLAlchemy 2.0 with async support
- PostgreSQL + pgvector
- Ollama for embeddings/LLM
- Redis for caching
- AWS Cognito for auth

### Frontend
- React with React Router
- TailwindCSS for styling
- React Query for data fetching
- Context API for state management

### Infrastructure
- Docker & Docker Compose
- Python 3.11
- Node.js 16+ (React apps)
- pgvector extension

### Key Libraries
- pdfplumber (PDF extraction)
- pandas (CSV/Excel processing)
- scikit-learn (vector operations)
- slowapi (rate limiting)
- nest_asyncio (async utilities)

---

## 11. Key Features and Capabilities

### Multi-Tenancy
- Tenant ID extracted from JWT token
- Database-level tenant isolation
- Separate document/embedding/chat storage per tenant
- CORS configuration per tenant

### White-Label Support
- Brand customization (name, colors, logo)
- Domain configuration per tenant
- Custom CSS for widgets
- Branding configuration via environment variables

### RAG Features
- Vector similarity search with pgvector
- Location-based context filtering
- Chunk-level metadata preservation
- Source citation tracking
- Few-shot learning via agent config

### Widget Integration
- Embeddable JavaScript widget
- Domain whitelist security
- Rate limiting per widget
- Real-time streaming support
- Custom styling and branding

### Admin Interface
- Document management dashboard
- Widget configuration UI
- Usage analytics and reporting
- Chat history review
- Tenant profile management

### Super Admin Platform
- Customer management (activate/suspend)
- System configuration
- Audit logging
- Platform analytics
- Admin account management
- Superadmin setup wizard

---

## 12. Performance Characteristics

### Current Limitations
- Chat responses: 3-5+ seconds (Ollama bottleneck)
- Embedding calls: 20-40 per query (location filtering)
- Sequential processing without batching
- Single machine deployment limitations

### Optimization Opportunities
- Groq API for LLM (500+ tokens/sec vs Ollama ~50 tokens/sec)
- Voyage AI for embeddings (superior RAG quality)
- Response caching for common queries
- Batch embedding requests
- Implement semantic filtering to reduce context size

---

## 13. Deployment Variations

### Base Production (docker-compose.yml)
- Simple setup: Postgres, Ollama, Streamlit
- No Redis, limited scaling
- Single API instance

### Development (docker-compose.dev.yml)
- All services: API, React UIs, Streamlit
- Hot reload for code changes
- Generous rate limits
- Extended token expiry (24 hours)

### Cleona-Specific (docker-compose.cleona.yml)
- Healthcare/government focused branding
- Redis caching enabled
- Resource limits enforced
- 6 containers total
- Custom domain configuration

### Client Example (docker-compose.client-example.yml)
- Template for white-label deployment
- Customizable environment variables
- Scalable architecture template

---

## 14. Known Technical Debt and TODOs

### From CLAUDE.md Notes:
1. **Semantic Context Filtering** - Filter chunks by semantic relevance to query
2. **Media Responses** - Image uploads and semantic image search
3. **Multi-lingual Support** - Auto-detect language and respond accordingly
4. **Widget Streaming** - Real-time response streaming in chat widget
5. **Performance Migration** - Switch from Ollama to Groq + Voyage AI

### Code Patterns to Be Aware Of:
- Legacy Streamlit app alongside modern React UIs
- Direct Ollama client usage instead of abstracted service layer
- Synchronous and async code mixed in some modules
- Incomplete semantic filtering implementation
- Optional Redis caching not fully integrated

---

## Summary for Microservices Migration

This is a **monolithic multi-tenant RAG platform** with clear separation of concerns:

1. **Frontend Layer**: 3 React apps (admin, widget, super-admin) + legacy Streamlit
2. **API Layer**: Single FastAPI app with 6 routers (3,200 LOC)
3. **Service Layer**: RAG core (embedding, chunking, answer generation)
4. **Data Layer**: PostgreSQL with pgvector, Redis cache
5. **LLM/Embedding**: Ollama (self-hosted)

**Key Characteristics:**
- Multi-tenant with strong isolation
- JWT-based authentication via AWS Cognito
- Domain-level CORS security
- Rate limiting per endpoint and tenant
- Vector search with metadata filtering
- Real-time streaming support

**Ready for Decomposition Into:**
- Auth microservice (Cognito wrapper)
- Document processing service
- Embedding service (Ollama abstraction)
- RAG/Chat service
- Widget service
- Super admin service
- Analytics service

