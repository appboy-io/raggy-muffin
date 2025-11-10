# Raggy Muffin - Microservices Architecture on AWS

## Executive Summary

Migration from monolithic FastAPI application to microservices architecture on AWS, replacing self-hosted Ollama with managed API services (Groq + Voyage AI) for improved performance, scalability, and cost efficiency.

**Expected Performance**: 200-500ms responses (vs current 3-5+ seconds)
**Expected Cost**: ~$150/month for APIs + AWS infrastructure
**Migration Timeline**: 6-8 weeks (phased rollout)

---

## Architecture Overview

### Core Principles
1. **Service Independence**: Each microservice owns its domain and data
2. **API Gateway**: Single entry point for all client requests
3. **Event-Driven**: Async communication via SQS/EventBridge where appropriate
4. **Cloud-Native**: Leverage managed AWS services (no Ollama, no Redis self-hosting)
5. **Multi-Tenancy**: Tenant isolation at every layer

### High-Level Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   CloudFront    │
                                    │   (CDN + WAF)   │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
            ┌───────▼────────┐      ┌───────▼────────┐      ┌───────▼────────┐
            │  Admin UI      │      │  Widget UI     │      │ SuperAdmin UI  │
            │  (S3 + CF)     │      │  (S3 + CF)     │      │  (S3 + CF)     │
            └────────────────┘      └────────────────┘      └────────────────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   API Gateway   │
                                    │   (REST + WS)   │
                                    └────────┬────────┘
                                             │
                ┌────────────────────────────┼────────────────────────────┐
                │                            │                            │
        ┌───────▼────────┐          ┌───────▼────────┐          ┌───────▼────────┐
        │  Auth Service  │          │  Chat Service  │          │ Admin Service  │
        │   (ECS/Lambda) │◄────────►│   (ECS/Lambda) │◄────────►│   (ECS/Lambda) │
        └───────┬────────┘          └───────┬────────┘          └───────┬────────┘
                │                            │                            │
        ┌───────▼────────┐          ┌───────▼────────┐          ┌───────▼────────┐
        │ Document Svc   │          │ Embedding Svc  │          │ Analytics Svc  │
        │   (ECS/Lambda) │          │   (Lambda)     │          │   (Lambda)     │
        └───────┬────────┘          └───────┬────────┘          └───────┬────────┘
                │                            │                            │
                │                   ┌────────▼────────┐                  │
                │                   │  Voyage AI API  │                  │
                │                   │   (External)    │                  │
                │                   └─────────────────┘                  │
                │                   ┌─────────────────┐                  │
                │                   │   Groq API      │                  │
                │                   │   (External)    │                  │
                │                   └─────────────────┘                  │
                │                                                         │
        ┌───────▼─────────────────────────────────────────────────┬─────▼─────┐
        │                     RDS Aurora PostgreSQL               │           │
        │                     (Multi-AZ, pgvector)                │  S3       │
        │                                                          │  (Docs)   │
        └──────────────────────────────────────────────────────────┴───────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  ElastiCache    │
                                    │  (Redis)        │
                                    └─────────────────┘
```

---

## Microservices Breakdown

### 1. **Auth Service**
**Responsibility**: Authentication, authorization, tenant validation
**Technology**: ECS Fargate (Python FastAPI) or Lambda (serverless)
**Database**: RDS Aurora (shared) - tables: `customer_profiles`, `superadmins`, `superadmin_sessions`

**API Endpoints**:
- `POST /auth/login` - Customer login
- `POST /auth/register` - New customer registration
- `POST /auth/validate` - JWT token validation
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - Session termination
- `POST /auth/superadmin/login` - Super admin login

**Key Features**:
- JWT token generation and validation
- AWS Cognito integration (optional replacement)
- Rate limiting per tenant
- Session management
- Audit logging for authentication events

**Dependencies**:
- RDS Aurora (customer_profiles, superadmins)
- ElastiCache (session storage, token blacklist)

**Scaling**: Auto-scale on CPU (ECS) or concurrent executions (Lambda)

---

### 2. **Document Service**
**Responsibility**: Document upload, storage, processing, chunking, metadata management
**Technology**: ECS Fargate (Python FastAPI)
**Database**: RDS Aurora - tables: `documents`, `document_metadata`
**Storage**: S3 bucket (documents)

**API Endpoints**:
- `POST /documents/{tenant_id}/upload` - Upload documents
- `GET /documents/{tenant_id}` - List documents
- `GET /documents/{tenant_id}/{doc_id}` - Get document details
- `PUT /documents/{tenant_id}/{doc_id}` - Update document
- `DELETE /documents/{tenant_id}/{doc_id}` - Delete document
- `POST /documents/{tenant_id}/{doc_id}/process` - Trigger reprocessing

**Key Features**:
- File upload to S3 with presigned URLs
- Document parsing (PDF, DOCX, TXT, MD)
- Chunking with configurable strategies (semantic, fixed-size, recursive)
- Metadata extraction
- Document versioning
- Emit events to SQS for embedding generation

**Dependencies**:
- S3 (document storage)
- RDS Aurora (metadata)
- SQS (emit events to Embedding Service)
- Auth Service (token validation)

**Scaling**: Auto-scale on document processing queue depth

---

### 3. **Embedding Service**
**Responsibility**: Generate embeddings for documents and queries, vector storage
**Technology**: Lambda (event-driven, cost-effective)
**Database**: RDS Aurora - tables: `document_embeddings`, `cached_embeddings`
**External API**: Voyage AI (embeddings)

**API Endpoints**:
- `POST /embeddings/generate` - Generate embeddings (internal)
- `POST /embeddings/batch` - Batch embedding generation
- `GET /embeddings/search` - Vector similarity search

**Event Handlers**:
- SQS Queue: `document-uploaded` → Generate embeddings for chunks
- SQS Queue: `document-deleted` → Remove embeddings

**Key Features**:
- Voyage AI API integration (`voyage-02` model)
- Batch processing (128 embeddings per request)
- Embedding caching (ElastiCache)
- Retry logic with exponential backoff
- Cost optimization (cache frequent queries)

**Dependencies**:
- Voyage AI API (external)
- RDS Aurora (vector storage with pgvector)
- ElastiCache (embedding cache)
- SQS (event consumption)

**Scaling**: Lambda concurrent executions (auto-scales)

---

### 4. **Chat Service (RAG Core)**
**Responsibility**: Query processing, context retrieval, answer generation, streaming
**Technology**: ECS Fargate (Python FastAPI with WebSocket support)
**Database**: RDS Aurora - tables: `chat_sessions`, `chat_messages`, `agent_configs`
**External API**: Groq (LLM), Voyage AI (query embeddings)

**API Endpoints**:
- `POST /chat/{tenant_id}/query` - Standard chat query
- `GET /chat/{tenant_id}/stream` - Streaming chat (SSE)
- `POST /chat/{tenant_id}/sessions` - Create chat session
- `GET /chat/{tenant_id}/sessions/{session_id}/history` - Chat history
- `DELETE /chat/{tenant_id}/sessions/{session_id}` - End session

**Key Features**:
- Query embedding via Embedding Service
- Vector similarity search (pgvector)
- Context retrieval with semantic filtering
- LLM generation via Groq API (`llama3-70b-8192`)
- Streaming responses (Server-Sent Events)
- Agent configuration (system prompts, temperature)
- Response caching for common queries

**Dependencies**:
- Groq API (LLM generation)
- Embedding Service (query embeddings)
- RDS Aurora (chat history, agent configs)
- ElastiCache (response cache)
- Auth Service (tenant validation)

**Scaling**: Auto-scale on request rate, optimize for streaming connections

---

### 5. **Widget Service**
**Responsibility**: Widget configuration, embed script generation, public chat interface
**Technology**: Lambda (serverless, low traffic)
**Database**: RDS Aurora - tables: `widget_configs`

**API Endpoints**:
- `GET /widget/{tenant_id}/config` - Get widget configuration
- `PUT /widget/{tenant_id}/config` - Update widget settings
- `GET /widget/{tenant_id}/embed.js` - Generate embed script
- `POST /widget/{tenant_id}/cors` - Update CORS whitelist

**Key Features**:
- Widget customization (colors, branding, position)
- CORS configuration per tenant
- Dynamic embed script generation
- Widget analytics tracking
- Rate limiting per domain

**Dependencies**:
- RDS Aurora (widget_configs)
- Chat Service (proxies chat requests)
- CloudFront (serves widget frontend)

**Scaling**: Lambda auto-scales (minimal cost)

---

### 6. **Admin Service**
**Responsibility**: Admin panel operations, tenant management, usage monitoring
**Technology**: ECS Fargate (Python FastAPI)
**Database**: RDS Aurora - tables: `customer_profiles`, `tenant_usage`

**API Endpoints**:
- `GET /admin/{tenant_id}/profile` - Get tenant profile
- `PUT /admin/{tenant_id}/profile` - Update tenant profile
- `GET /admin/{tenant_id}/usage` - Usage statistics
- `GET /admin/{tenant_id}/analytics` - Analytics dashboard
- `POST /admin/{tenant_id}/api-keys` - Generate API keys

**Key Features**:
- Tenant profile management
- Usage tracking and limits
- API key generation
- Analytics dashboard data
- Document management integration

**Dependencies**:
- RDS Aurora (tenant data)
- Document Service (document operations)
- Widget Service (widget configuration)
- Analytics Service (usage data)

**Scaling**: Auto-scale on request rate

---

### 7. **Super Admin Service**
**Responsibility**: Platform administration, customer management, system configuration
**Technology**: ECS Fargate (Python FastAPI)
**Database**: RDS Aurora - tables: `superadmins`, `superadmin_audit_log`, `system_config`, `superadmin_notifications`

**API Endpoints**:
- `GET /superadmin/customers` - List all customers
- `GET /superadmin/customers/{tenant_id}` - Customer details
- `POST /superadmin/customers/{tenant_id}/suspend` - Suspend customer
- `GET /superadmin/analytics` - Platform-wide analytics
- `GET /superadmin/system/health` - System health check
- `POST /superadmin/system/config` - Update system config

**Key Features**:
- Customer lifecycle management
- Platform-wide analytics
- System configuration
- Audit logging (all actions)
- Impersonation with audit trail
- Health monitoring

**Dependencies**:
- RDS Aurora (all tables for read access)
- All services (health checks)
- Analytics Service (platform metrics)

**Scaling**: Minimal traffic, single instance or Lambda

---

### 8. **Analytics Service**
**Responsibility**: Usage tracking, metrics aggregation, reporting
**Technology**: Lambda (event-driven) + Athena/QuickSight (reporting)
**Database**: RDS Aurora (aggregated data), S3 (raw logs)

**API Endpoints**:
- `POST /analytics/track` - Track events (internal)
- `GET /analytics/{tenant_id}/usage` - Tenant usage stats
- `GET /analytics/platform/metrics` - Platform-wide metrics

**Event Handlers**:
- SQS Queue: `chat-query-completed` → Track usage
- SQS Queue: `document-uploaded` → Track document count
- EventBridge: Hourly aggregation job

**Key Features**:
- Real-time usage tracking
- Cost tracking (API calls to Groq/Voyage)
- Query performance metrics
- Customer engagement analytics
- S3 data lake for long-term storage
- Athena queries for reporting

**Dependencies**:
- SQS (event consumption)
- S3 (data lake)
- RDS Aurora (aggregated metrics)
- EventBridge (scheduled jobs)

**Scaling**: Lambda auto-scales, batch processing for aggregations

---

## Data Architecture

### Database Strategy

#### Option 1: **Shared Database (Recommended for Phase 1)**
- **Single RDS Aurora cluster** with logical separation by service
- **Pros**: Simpler migrations, ACID transactions, cost-effective
- **Cons**: Tight coupling, scaling limitations
- **Schema Organization**:
  - `auth_schema.*` (Auth Service)
  - `documents_schema.*` (Document Service)
  - `chat_schema.*` (Chat Service)
  - `analytics_schema.*` (Analytics Service)

#### Option 2: **Database per Service (Long-term Goal)**
- Separate RDS Aurora instances per service
- **Pros**: True service independence, optimized scaling
- **Cons**: Complex transactions, higher cost, migration overhead
- **Transition Plan**: Start with shared DB, migrate services individually

### Database Tables by Service

| Service | Tables |
|---------|--------|
| **Auth** | customer_profiles, superadmins, superadmin_sessions |
| **Document** | documents, document_metadata |
| **Embedding** | document_embeddings, cached_embeddings |
| **Chat** | chat_sessions, chat_messages, agent_configs |
| **Widget** | widget_configs |
| **Admin** | tenant_usage |
| **Super Admin** | superadmin_audit_log, superadmin_notifications, system_config |
| **Analytics** | usage_metrics, query_logs (aggregated) |

### Caching Strategy
- **ElastiCache Redis Cluster** (Multi-AZ)
- **Use Cases**:
  - JWT token validation cache (Auth Service)
  - Session storage (Auth Service)
  - Embedding cache (Embedding Service)
  - Query response cache (Chat Service)
  - Widget config cache (Widget Service)

---

## AWS Service Selection

### Compute Options

| Service | Use Case | Cost | Scaling |
|---------|----------|------|---------|
| **ECS Fargate** | Long-running services (Chat, Admin) | Medium | Auto-scale on metrics |
| **Lambda** | Event-driven, bursty (Embedding, Analytics) | Low (pay per use) | Instant, 10K concurrent |
| **App Runner** | Simpler alternative to ECS | Medium-High | Auto-scale (simpler config) |

**Recommendation**:
- **ECS Fargate** for Chat Service (WebSocket support)
- **Lambda** for Embedding, Analytics, Widget Services
- **ECS or Lambda** for Auth, Document, Admin Services (flexible)

### Database
- **RDS Aurora PostgreSQL** (Serverless v2)
  - Multi-AZ for HA
  - pgvector extension for embeddings
  - Read replicas for analytics queries
  - Automatic backups
  - **Cost**: ~$100-300/month (variable scaling)

### Storage
- **S3** for document storage
  - Separate buckets per tenant or folder structure
  - Lifecycle policies (archive old docs to Glacier)
  - Presigned URLs for secure uploads
  - **Cost**: ~$20/month for 100GB

### Caching
- **ElastiCache Redis** (Cluster Mode)
  - Multi-AZ with automatic failover
  - **Cost**: ~$50-150/month (depends on cache size)

### Networking
- **API Gateway** (REST API + WebSocket API)
  - Single entry point
  - Request throttling and rate limiting
  - API key management
  - CORS configuration
  - **Cost**: $3.50 per million requests

- **VPC** with private subnets
  - NAT Gateway for outbound traffic
  - Security groups for service isolation

### Frontend Hosting
- **S3 + CloudFront**
  - Static hosting for React apps
  - CDN for global distribution
  - WAF for security
  - **Cost**: ~$20-50/month

### Messaging
- **SQS** for async communication
  - `document-uploaded-queue` (Document → Embedding)
  - `document-deleted-queue` (Document → Embedding)
  - `analytics-events-queue` (All → Analytics)
  - **Cost**: First 1M requests free, $0.40 per million after

- **EventBridge** for scheduled jobs
  - Hourly analytics aggregation
  - Daily usage reports
  - **Cost**: Minimal (~$1/month)

### Monitoring & Logging
- **CloudWatch**
  - Logs from all services
  - Metrics and alarms
  - Dashboards
  - **Cost**: ~$30-50/month

- **X-Ray** for distributed tracing
  - Request tracing across services
  - Performance bottleneck identification

### Secrets Management
- **AWS Secrets Manager**
  - API keys (Groq, Voyage AI)
  - Database credentials
  - JWT signing keys
  - **Cost**: $0.40 per secret/month

---

## Communication Patterns

### 1. **Synchronous (REST)**
- Client → API Gateway → Services
- Auth Service ← → All Services (token validation)
- Chat Service → Embedding Service (query embeddings)
- Admin Service → Document Service (document operations)

**When to use**: Real-time requests requiring immediate response

### 2. **Asynchronous (SQS Events)**
- Document Service → Embedding Service (document uploaded)
- All Services → Analytics Service (usage tracking)
- Document Service → Embedding Service (document deleted)

**When to use**: Fire-and-forget operations, decoupling services

### 3. **Streaming (WebSocket/SSE)**
- Client → API Gateway → Chat Service (streaming responses)

**When to use**: Real-time chat responses

---

## API Gateway Configuration

### REST API Routes

```
/auth/*                  → Auth Service
/documents/*             → Document Service
/embeddings/*            → Embedding Service (internal only)
/chat/*                  → Chat Service
/widget/*                → Widget Service
/admin/*                 → Admin Service
/superadmin/*            → Super Admin Service
/analytics/*             → Analytics Service
```

### WebSocket API (Chat Streaming)
```
ws://api.raggy-muffin.com/chat/stream
  - Connection: Authenticate via JWT
  - Messages: Send queries, receive streaming chunks
  - Disconnection: Clean up session
```

### Rate Limiting
- **Per Tenant**: 100 requests/minute (configurable)
- **Per IP**: 1000 requests/hour (DDoS protection)
- **API Gateway Throttling**: Burst 5000, steady 2000 req/sec

### CORS Configuration
- **Admin UI**: Specific origin (admin.raggy-muffin.com)
- **Widget**: Tenant-specific whitelist (stored in widget_configs)
- **Super Admin**: Specific origin (superadmin.raggy-muffin.com)

---

## Security Architecture

### Multi-Tenant Isolation

1. **Authentication Layer** (API Gateway + Auth Service)
   - JWT token with embedded `tenant_id`
   - Token validation on every request
   - Token expiry and refresh

2. **Authorization Layer** (Each Service)
   - Extract `tenant_id` from JWT
   - Validate tenant has access to resource
   - Database queries filtered by `tenant_id`

3. **Database Layer** (RDS Aurora)
   - Row-level security policies
   - All tables have `tenant_id` column
   - Indexes on `tenant_id` for performance

4. **Network Layer** (VPC + Security Groups)
   - Services in private subnets
   - Only API Gateway has public access
   - Service-to-service communication via private IPs

5. **Data Layer** (S3)
   - Folder structure: `s3://bucket/{tenant_id}/documents/`
   - IAM policies scoped to tenant folders
   - Encryption at rest (SSE-S3 or KMS)

### API Security
- **WAF** on CloudFront and API Gateway
  - SQL injection protection
  - XSS protection
  - Rate limiting by IP
  - Geo-blocking (optional)

- **Secrets Management**
  - No hardcoded credentials
  - AWS Secrets Manager for all secrets
  - Automatic secret rotation

- **Audit Logging**
  - All API calls logged to CloudWatch
  - All admin actions logged to `superadmin_audit_log`
  - Retention: 90 days (configurable)

---

## Deployment Strategy

### Infrastructure as Code (IaC)
**Recommended**: **AWS CDK (Python)** or **Terraform**

**Why CDK?**
- Write infrastructure in Python (same language as backend)
- Type-safe, IDE autocomplete
- Higher-level constructs (less boilerplate)
- Native AWS integration

**Repository Structure**:
```
/infrastructure/
  /cdk/
    app.py                    # CDK app entry point
    /stacks/
      network_stack.py        # VPC, subnets, security groups
      database_stack.py       # RDS Aurora
      compute_stack.py        # ECS clusters, Lambda functions
      api_gateway_stack.py    # API Gateway
      frontend_stack.py       # S3 + CloudFront
      monitoring_stack.py     # CloudWatch, X-Ray
```

### CI/CD Pipeline
**Recommended**: **GitHub Actions** or **AWS CodePipeline**

**Workflow**:
1. **Code Push** → GitHub
2. **Build** → Docker images for ECS services, Lambda deployment packages
3. **Test** → Unit tests, integration tests
4. **Deploy to Staging** → Automatic deployment
5. **Smoke Tests** → Automated health checks
6. **Deploy to Production** → Manual approval or automatic

**Multi-Environment Strategy**:
- **Development**: Local Docker Compose (current setup)
- **Staging**: AWS (full microservices)
- **Production**: AWS (full microservices)

---

## Migration Plan

### Phase 1: **API Provider Migration** (2 weeks)
**Goal**: Replace Ollama with Groq + Voyage AI (no microservices yet)

**Steps**:
1. Add environment variables for Groq and Voyage AI
2. Update `embed_query_async()` and `embed_chunks_async()` to use Voyage AI
3. Update `generate_answer()` to use Groq API
4. Implement caching layer (Redis) for embeddings
5. Deploy to staging with new providers
6. Test performance and accuracy
7. Gradual rollout to production (10% → 50% → 100%)

**Expected Outcome**: 10-20x faster responses, predictable costs

---

### Phase 2: **Infrastructure Setup** (1-2 weeks)
**Goal**: Set up AWS infrastructure using CDK

**Steps**:
1. Create CDK project with stacks (network, database, compute, etc.)
2. Deploy VPC with private/public subnets
3. Deploy RDS Aurora PostgreSQL with pgvector
4. Deploy ElastiCache Redis cluster
5. Set up S3 buckets for documents and frontend hosting
6. Deploy API Gateway (placeholder routes)
7. Configure CloudWatch logging and monitoring
8. Deploy CloudFront distributions for frontends

**Expected Outcome**: AWS infrastructure ready for service deployment

---

### Phase 3: **Service Extraction** (3-4 weeks)
**Goal**: Extract services from monolith one by one

**Order** (least to most critical):
1. **Analytics Service** (low risk, decoupled)
   - Extract analytics logic to Lambda
   - Set up SQS event queue
   - Deploy and test independently

2. **Widget Service** (low risk, isolated)
   - Extract widget logic to Lambda
   - Deploy widget frontend to S3 + CloudFront
   - Test embed script and CORS

3. **Auth Service** (medium risk, foundational)
   - Extract authentication logic to ECS/Lambda
   - Set up JWT validation middleware
   - Test with all frontends

4. **Document Service** (medium risk, high value)
   - Extract document upload/processing to ECS
   - Set up S3 integration
   - Emit events to Embedding Service

5. **Embedding Service** (medium risk, performance critical)
   - Extract embedding logic to Lambda
   - Integrate with Voyage AI (already done in Phase 1)
   - Set up event-driven processing

6. **Chat Service** (high risk, core functionality)
   - Extract RAG logic to ECS
   - Set up streaming support
   - Integrate with Groq API (already done in Phase 1)

7. **Admin Service** (low risk, orchestration)
   - Extract admin panel logic to ECS/Lambda
   - Integrate with other services

8. **Super Admin Service** (low risk, isolated)
   - Extract super admin logic to ECS/Lambda
   - Deploy super admin frontend to S3 + CloudFront

**Strategy for Each Service**:
- Create new service repository (or monorepo with service folders)
- Set up Docker container (ECS) or Lambda handler
- Deploy to staging
- Run integration tests with other services
- Deploy to production with gradual rollout
- Monitor for 1 week before moving to next service

---

### Phase 4: **Optimization & Cleanup** (1 week)
**Goal**: Optimize performance, remove monolith

**Steps**:
1. Fine-tune auto-scaling policies
2. Optimize database queries and indexes
3. Set up CloudWatch alarms and dashboards
4. Implement cost optimization (reserved instances, savings plans)
5. Remove old monolithic application
6. Update documentation

---

## Cost Estimate

### Monthly AWS Costs (Estimated for 10K queries/day)

| Service | Cost |
|---------|------|
| **ECS Fargate** (4 services, 2 tasks each) | $100-150 |
| **Lambda** (Embedding, Analytics, Widget) | $20-40 |
| **RDS Aurora Serverless v2** | $100-200 |
| **ElastiCache Redis** | $50-100 |
| **S3** (storage + requests) | $20-30 |
| **CloudFront** (CDN) | $20-40 |
| **API Gateway** | $30-50 |
| **CloudWatch** (logs + metrics) | $30-50 |
| **NAT Gateway** | $30-45 |
| **Secrets Manager** | $5 |
| **Data Transfer** | $20-40 |
| **Groq API** | $90 |
| **Voyage AI API** | $60 |
| **TOTAL** | **$575-900/month** |

**Cost Optimization Strategies**:
- Use Lambda for bursty workloads (pay per use)
- Reserved instances for ECS (40% savings)
- S3 lifecycle policies (archive to Glacier)
- ElastiCache right-sizing
- CloudWatch log retention policies (30 days)

**Comparison to Current Setup**:
- Current: Self-hosted server + slow performance
- AWS: Higher cost but 10-20x faster, scalable, managed

---

## Monitoring & Observability

### CloudWatch Dashboards
1. **API Performance**
   - Request rate per service
   - P50, P95, P99 latencies
   - Error rates (4xx, 5xx)

2. **Service Health**
   - CPU, memory utilization (ECS)
   - Lambda concurrent executions
   - Database connections

3. **Business Metrics**
   - Total queries per tenant
   - Document uploads per tenant
   - API costs (Groq, Voyage AI)

### Alarms
- **Critical**:
  - API Gateway 5xx errors > 1%
  - RDS CPU > 80%
  - Lambda errors > 5%
  - ElastiCache connection failures

- **Warning**:
  - API Gateway 4xx errors > 5%
  - RDS storage > 80%
  - S3 bucket size > 1TB
  - Monthly API costs > $200

### Distributed Tracing (X-Ray)
- Trace requests across all services
- Identify bottlenecks (e.g., slow database queries)
- Visualize service dependencies

---

## Disaster Recovery & High Availability

### RDS Aurora
- **Multi-AZ** deployment (automatic failover in 30-120 seconds)
- **Automated backups** (retained for 7-35 days)
- **Point-in-time recovery** (restore to any second in retention period)
- **Read replicas** for disaster recovery in different region

### ECS Fargate
- **Multiple availability zones** (tasks spread across 3 AZs)
- **Auto-scaling** (replace unhealthy tasks automatically)
- **Health checks** (ALB health checks every 30 seconds)

### Lambda
- **Inherently multi-AZ** (AWS manages availability)
- **Automatic retries** for failed invocations

### S3
- **99.999999999% durability** (11 nines)
- **Cross-region replication** (optional for critical data)
- **Versioning** (protect against accidental deletes)

### ElastiCache
- **Multi-AZ with automatic failover**
- **Daily automated backups**
- **Snapshot to S3** for long-term retention

### Recovery Objectives
- **RTO (Recovery Time Objective)**: 30 minutes (restore from backups)
- **RPO (Recovery Point Objective)**: 5 minutes (point-in-time recovery)

---

## Alternative Architectures

### Option A: **Serverless-First** (Lowest Cost)
- Replace ECS with Lambda for all services
- Use API Gateway HTTP API (cheaper than REST API)
- Use Aurora Serverless v2 (scales to zero)
- **Pros**: Pay per use, auto-scaling, minimal ops
- **Cons**: Cold starts, 15-minute Lambda timeout, complex WebSocket handling

### Option B: **Kubernetes (EKS)** (Enterprise Scale)
- Use EKS instead of ECS
- Deploy services as Kubernetes Deployments
- Use Istio for service mesh
- **Pros**: Portability, advanced orchestration, strong ecosystem
- **Cons**: Higher complexity, higher cost, steeper learning curve

### Option C: **App Runner** (Simplicity)
- Use AWS App Runner instead of ECS
- Simpler deployment (no VPC, no load balancer config)
- **Pros**: Dead simple, auto-scaling, cost-effective
- **Cons**: Less control, limited networking options

**Recommendation**: Start with **ECS + Lambda hybrid** (proposed architecture) for balance of cost, simplicity, and control. Migrate to EKS if enterprise features needed.

---

## Next Steps

### Immediate Actions
1. **Decision Meeting**: Review this architecture with team
2. **API Provider Testing**: Sign up for Groq + Voyage AI, test performance
3. **AWS Account Setup**: Create AWS organization, set up billing alerts
4. **CDK Project Setup**: Initialize CDK project for infrastructure

### Week 1-2: API Provider Migration
- Implement Groq + Voyage AI integration
- Deploy to staging
- Performance testing

### Week 3-4: Infrastructure Setup
- Deploy VPC, RDS, ElastiCache, S3 via CDK
- Set up CI/CD pipeline

### Week 5-8: Service Extraction
- Extract services one by one (Analytics → Widget → Auth → Document → Embedding → Chat → Admin → Super Admin)
- Test and monitor each service

### Week 9: Go Live
- Gradual rollout to production
- Monitor performance and costs
- Iterate and optimize

---

## Questions for Discussion

1. **Compute Strategy**: ECS Fargate vs Lambda vs App Runner for each service?
2. **Database Strategy**: Shared database (Phase 1) vs Database per service (long-term)?
3. **Monorepo vs Multi-repo**: One repo with all services or separate repos?
4. **AWS Region**: Which region(s) for deployment? Multi-region?
5. **Cost Budget**: What's the acceptable monthly AWS cost?
6. **Migration Timeline**: 6-8 weeks feasible? Need faster/slower?
7. **Team Size**: How many developers? Need DevOps support?
8. **Risk Tolerance**: Big bang migration or gradual rollout?

---

## Conclusion

This architecture provides a clear path from the current monolithic application to a scalable, cloud-native microservices platform on AWS. The migration from Ollama to Groq + Voyage AI removes the need for self-hosted ML infrastructure and unlocks 10-20x performance improvements.

**Key Benefits**:
- **Performance**: 200-500ms responses (vs 3-5+ seconds)
- **Scalability**: Auto-scaling for any traffic level
- **Reliability**: Multi-AZ, automatic failover, 99.9% uptime
- **Cost Predictability**: Pay-as-you-go with clear cost monitoring
- **Developer Experience**: Independent services, faster development cycles

**Recommended Next Step**: Start with Phase 1 (API Provider Migration) to prove out performance improvements, then proceed with full microservices migration.
