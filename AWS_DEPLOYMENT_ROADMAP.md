# AWS Deployment Roadmap - Raggy Muffin

## Timeline Overview (6-8 Weeks)

```
Week 1-2: API Provider Migration (Groq + Voyage AI)
Week 3-4: AWS Infrastructure Setup
Week 5-8: Service Extraction & Migration
Week 9: Production Rollout & Optimization
```

---

## Phase 1: API Provider Migration (Week 1-2)

### Objectives
- Replace Ollama with Groq (LLM) and Voyage AI (embeddings)
- Achieve 10-20x performance improvement
- Keep monolithic architecture (microservices come later)

### Tasks

#### Day 1-2: Setup & Configuration
- [ ] Sign up for Groq API (https://console.groq.com)
- [ ] Sign up for Voyage AI API (https://www.voyageai.com)
- [ ] Add API keys to `.env`:
  ```bash
  GROQ_API_KEY=your_groq_api_key
  GROQ_MODEL=llama3-70b-8192
  GROQ_MAX_TOKENS=2048
  GROQ_TEMPERATURE=0.7

  VOYAGE_API_KEY=your_voyage_api_key
  VOYAGE_MODEL=voyage-02
  VOYAGE_BATCH_SIZE=128
  ```
- [ ] Test API connectivity (simple curl requests)

#### Day 3-5: Embedding Service Migration
- [ ] Update `/api/app/core/embeddings.py`:
  - Replace `embed_query_async()` to call Voyage AI
  - Replace `embed_chunks_async()` to call Voyage AI with batching
  - Add retry logic with exponential backoff
  - Add error handling and fallback to Ollama
- [ ] Test embedding generation with sample documents
- [ ] Verify embedding dimensions match (1024 for voyage-02)
- [ ] Update database schema if needed (embedding dimension)

#### Day 6-8: LLM Service Migration
- [ ] Update `/api/app/core/rag.py`:
  - Replace `generate_answer()` to call Groq API
  - Update streaming function to use Groq streaming
  - Add retry logic and error handling
  - Keep Ollama as fallback option
- [ ] Test chat responses with sample queries
- [ ] Test streaming responses
- [ ] Verify response quality and latency

#### Day 9-10: Performance Optimization
- [ ] Add Redis caching for embeddings:
  - Cache query embeddings (5-minute TTL)
  - Cache frequent queries' responses (10-minute TTL)
- [ ] Implement batch embedding for document uploads
- [ ] Disable expensive semantic filtering (save 2-3 seconds)
- [ ] Add monitoring for API costs and latency

#### Day 11-12: Testing & Deployment
- [ ] Run integration tests with all endpoints
- [ ] Performance testing (measure latency improvement)
- [ ] Deploy to staging environment
- [ ] Smoke tests on staging
- [ ] Gradual production rollout:
  - 10% of traffic (1 day)
  - 50% of traffic (1 day)
  - 100% of traffic
- [ ] Monitor error rates, latency, costs

### Success Metrics
- ✅ Average response time: < 500ms (down from 3-5 seconds)
- ✅ Error rate: < 1%
- ✅ Daily API costs: ~$5/day for 10K queries
- ✅ Embedding generation: < 50ms per request

### Rollback Plan
- Keep Ollama running as fallback
- Environment variable: `USE_OLLAMA_FALLBACK=true`
- If Groq/Voyage API fails, automatically fallback to Ollama

---

## Phase 2: AWS Infrastructure Setup (Week 3-4)

### Objectives
- Deploy AWS infrastructure using CDK
- Set up networking, databases, caching, and storage
- No application code changes yet

### Prerequisites
- AWS Account with admin access
- AWS CLI installed and configured
- Python 3.11+ and AWS CDK installed
- GitHub repository for infrastructure code

### Tasks

#### Day 1-3: AWS Account & CDK Setup
- [ ] Create AWS Organization (if not exists)
- [ ] Set up billing alerts ($100, $500, $1000)
- [ ] Create IAM users for developers
- [ ] Install AWS CDK:
  ```bash
  npm install -g aws-cdk
  cdk --version
  ```
- [ ] Initialize CDK project:
  ```bash
  mkdir infrastructure/cdk
  cd infrastructure/cdk
  cdk init app --language python
  ```
- [ ] Create CDK stacks:
  - `network_stack.py` (VPC)
  - `database_stack.py` (RDS Aurora)
  - `cache_stack.py` (ElastiCache)
  - `storage_stack.py` (S3)
  - `api_gateway_stack.py` (API Gateway)
  - `compute_stack.py` (ECS, Lambda - placeholder)
  - `frontend_stack.py` (S3 + CloudFront)
  - `monitoring_stack.py` (CloudWatch)

#### Day 4-6: Networking
- [ ] Deploy VPC stack:
  - 3 public subnets (across 3 AZs)
  - 3 private subnets (across 3 AZs)
  - Internet Gateway (public subnet access)
  - NAT Gateway (private subnet outbound)
  - Route tables
- [ ] Deploy Security Groups:
  - `api-gateway-sg` (allow inbound 443)
  - `ecs-services-sg` (allow from API Gateway)
  - `lambda-sg` (allow from API Gateway)
  - `rds-sg` (allow from ECS/Lambda)
  - `redis-sg` (allow from ECS/Lambda)
- [ ] Test connectivity (deploy test EC2 instance)

#### Day 7-9: Database & Caching
- [ ] Deploy RDS Aurora PostgreSQL stack:
  - Engine: PostgreSQL 14+
  - Instance: Serverless v2 (0.5-2 ACU)
  - Multi-AZ: Yes
  - Backup retention: 7 days
  - Enable pgvector extension
  - Create database: `raggy_muffin`
- [ ] Deploy ElastiCache Redis stack:
  - Node type: cache.t3.micro (start small)
  - Multi-AZ: Yes
  - Automatic failover: Enabled
- [ ] Run database migrations:
  ```bash
  # Export connection string
  export DATABASE_URL="postgresql://user:pass@aurora-endpoint:5432/raggy_muffin"

  # Run Alembic migrations
  cd /home/cleona_app/raggy-muffin/api
  alembic upgrade head
  ```
- [ ] Verify pgvector extension:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  SELECT * FROM pg_extension WHERE extname = 'vector';
  ```

#### Day 10-12: Storage & API Gateway
- [ ] Deploy S3 buckets:
  - `raggy-muffin-documents-{env}` (private, versioning enabled)
  - `raggy-muffin-admin-ui-{env}` (public, static website)
  - `raggy-muffin-widget-ui-{env}` (public, static website)
  - `raggy-muffin-superadmin-ui-{env}` (public, static website)
  - `raggy-muffin-logs-{env}` (private, lifecycle policy)
- [ ] Set up S3 lifecycle policies:
  - Archive documents to Glacier after 90 days
  - Delete logs after 30 days
- [ ] Deploy API Gateway:
  - REST API: `/api/*`
  - WebSocket API: `/chat/stream`
  - Enable CORS
  - Set up rate limiting (1000 req/sec)
  - Custom domain: `api.raggy-muffin.com`
- [ ] Deploy CloudFront distributions:
  - `admin.raggy-muffin.com` → S3 admin UI bucket
  - `widget.raggy-muffin.com` → S3 widget UI bucket
  - `superadmin.raggy-muffin.com` → S3 superadmin UI bucket
  - Enable WAF (SQL injection, XSS protection)

#### Day 13-14: Monitoring & Secrets
- [ ] Deploy CloudWatch stack:
  - Log groups for each service
  - Retention: 30 days
  - Create dashboards (placeholder)
- [ ] Set up X-Ray for distributed tracing
- [ ] Deploy Secrets Manager secrets:
  - `raggy-muffin/database` (RDS credentials)
  - `raggy-muffin/groq-api-key`
  - `raggy-muffin/voyage-api-key`
  - `raggy-muffin/jwt-secret`
- [ ] Set up CloudWatch alarms:
  - RDS CPU > 80%
  - ElastiCache memory > 80%
  - API Gateway 5xx errors > 1%

### Success Metrics
- ✅ All infrastructure deployed successfully
- ✅ VPC has public/private subnets in 3 AZs
- ✅ RDS Aurora accessible from private subnets
- ✅ ElastiCache accessible from private subnets
- ✅ S3 buckets created with proper permissions
- ✅ API Gateway and CloudFront accessible via custom domains
- ✅ CloudWatch logs collecting data

### Cost Estimate (Phase 2)
- **Infrastructure only** (no application traffic): ~$200-300/month
- RDS Aurora Serverless v2 (idle): ~$50
- ElastiCache (t3.micro): ~$15
- NAT Gateway: ~$30
- S3 (empty): ~$1
- CloudFront (no traffic): ~$1

---

## Phase 3: Service Extraction (Week 5-8)

### Objectives
- Extract services from monolith one by one
- Deploy to AWS using ECS Fargate or Lambda
- Maintain backward compatibility during migration

### Service Extraction Order

#### Week 5: Low-Risk Services
**Analytics Service** (Day 1-2)
- [ ] Extract analytics logic to Lambda
- [ ] Set up SQS queue: `analytics-events-queue`
- [ ] Deploy Lambda function to staging
- [ ] Test event processing
- [ ] Deploy to production
- [ ] Monitor for 2 days

**Widget Service** (Day 3-4)
- [ ] Extract widget logic to Lambda
- [ ] Update API Gateway routes: `/widget/*`
- [ ] Deploy to staging
- [ ] Test embed script generation
- [ ] Deploy to production
- [ ] Monitor for 2 days

**Super Admin Service** (Day 5-7)
- [ ] Extract super admin logic to ECS Fargate
- [ ] Create Dockerfile for super admin service
- [ ] Deploy to ECS (1 task, auto-scaling disabled)
- [ ] Update API Gateway routes: `/superadmin/*`
- [ ] Deploy super admin UI to S3 + CloudFront
- [ ] Test all super admin features
- [ ] Deploy to production

#### Week 6: Foundational Services
**Auth Service** (Day 1-3)
- [ ] Extract authentication logic to ECS Fargate
- [ ] Create shared JWT validation middleware
- [ ] Deploy to staging
- [ ] Test with admin UI, widget, super admin UI
- [ ] Update all services to call Auth Service
- [ ] Deploy to production
- [ ] Monitor authentication success rate

**Document Service** (Day 4-7)
- [ ] Extract document upload/processing to ECS Fargate
- [ ] Set up S3 integration (presigned URLs)
- [ ] Set up SQS queue: `document-uploaded-queue`
- [ ] Deploy to staging
- [ ] Test document upload, processing, deletion
- [ ] Deploy to production
- [ ] Monitor document processing times

#### Week 7: Performance-Critical Services
**Embedding Service** (Day 1-3)
- [ ] Extract embedding logic to Lambda
- [ ] Set up event processing (SQS: `document-uploaded-queue`)
- [ ] Integrate with Voyage AI (already done in Phase 1)
- [ ] Deploy to staging
- [ ] Test embedding generation for documents and queries
- [ ] Deploy to production
- [ ] Monitor embedding generation latency

**Chat Service** (Day 4-7)
- [ ] Extract RAG logic to ECS Fargate
- [ ] Set up WebSocket support (API Gateway WebSocket API)
- [ ] Integrate with Groq API (already done in Phase 1)
- [ ] Deploy to staging
- [ ] Test chat queries, streaming, session management
- [ ] Performance testing (load testing with 100 concurrent users)
- [ ] Deploy to production
- [ ] Monitor chat latency and error rates

#### Week 8: Orchestration & Cleanup
**Admin Service** (Day 1-2)
- [ ] Extract admin panel logic to ECS Fargate
- [ ] Integrate with Document, Widget, Auth services
- [ ] Deploy to staging
- [ ] Test all admin panel features
- [ ] Deploy admin UI to S3 + CloudFront
- [ ] Deploy to production

**Final Testing & Cleanup** (Day 3-5)
- [ ] End-to-end testing of all services
- [ ] Load testing (simulate 1000 concurrent users)
- [ ] Security testing (penetration testing)
- [ ] Remove old monolithic application
- [ ] Update documentation

### Service Deployment Template

For each service, follow this process:

1. **Code Extraction**
   ```bash
   # Create service directory
   mkdir -p services/{service-name}
   cd services/{service-name}

   # Extract relevant code from /api/app/routers/{service}.py
   # Create Dockerfile (ECS) or handler.py (Lambda)
   ```

2. **Containerization (ECS Services)**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **CDK Deployment**
   ```python
   # infrastructure/cdk/stacks/{service}_stack.py
   from aws_cdk import (
       aws_ecs as ecs,
       aws_ecs_patterns as ecs_patterns,
   )

   # For ECS Fargate
   service = ecs_patterns.ApplicationLoadBalancedFargateService(
       self, "{Service}Service",
       task_image_options=...,
       desired_count=2,
       cpu=256,
       memory_limit_mib=512,
   )
   ```

4. **API Gateway Integration**
   ```python
   # Update API Gateway routes
   api.add_routes(
       path="/{service}/*",
       integration=HttpNlbIntegration(
           listener=service.listener,
       ),
   )
   ```

5. **Testing**
   ```bash
   # Deploy to staging
   cdk deploy {Service}Stack --profile staging

   # Run integration tests
   pytest tests/integration/test_{service}.py

   # Deploy to production
   cdk deploy {Service}Stack --profile production
   ```

### Success Metrics
- ✅ All 8 services deployed and operational
- ✅ Zero downtime during migration
- ✅ API response times: < 500ms (P95)
- ✅ Error rates: < 1%
- ✅ All tests passing (unit, integration, E2E)

---

## Phase 4: Production Rollout (Week 9)

### Objectives
- Gradual rollout to production
- Monitor performance and costs
- Optimize and iterate

### Tasks

#### Day 1-2: Gradual Rollout
- [ ] Deploy 10% of traffic to new microservices
  - Use API Gateway weighted routing
- [ ] Monitor CloudWatch metrics:
  - Request latency (should be < 500ms)
  - Error rates (should be < 1%)
  - API costs (should be ~$5/day)
- [ ] Compare with old monolith performance

#### Day 3: 50% Rollout
- [ ] Increase traffic to 50%
- [ ] Monitor for 24 hours
- [ ] Check for any anomalies

#### Day 4: 100% Rollout
- [ ] Route all traffic to microservices
- [ ] Keep monolith running for 1 week as backup
- [ ] Monitor for 48 hours

#### Day 5-7: Optimization
- [ ] Fine-tune auto-scaling policies
  - ECS: Scale on CPU > 70%
  - Lambda: Adjust concurrent execution limits
- [ ] Optimize database queries
  - Add missing indexes
  - Optimize slow queries (use pg_stat_statements)
- [ ] Set up cost optimization
  - Purchase reserved instances for ECS (40% savings)
  - Set up S3 lifecycle policies
  - Enable ElastiCache compression
- [ ] Create CloudWatch dashboards
  - API performance dashboard
  - Service health dashboard
  - Business metrics dashboard
  - Cost dashboard
- [ ] Set up alarms for all critical metrics
- [ ] Document runbooks for common issues

### Success Metrics
- ✅ 99.9% uptime (< 43 minutes downtime/month)
- ✅ P95 latency < 500ms
- ✅ Error rate < 1%
- ✅ Daily costs within budget (~$20-30/day)
- ✅ All alarms configured and tested
- ✅ Team trained on new architecture

---

## Rollback Procedures

### During Phase 1 (API Provider Migration)
**If Groq/Voyage API fails or performance is poor:**
1. Set environment variable: `USE_OLLAMA_FALLBACK=true`
2. Restart application
3. Traffic automatically routes to Ollama
4. Investigate issues with Groq/Voyage AI

### During Phase 3 (Service Extraction)
**If a new microservice fails:**
1. Update API Gateway routes to point back to monolith
2. Disable auto-scaling for failed service
3. Investigate logs in CloudWatch
4. Fix issues and redeploy
5. Re-route traffic when stable

### Emergency Rollback (Complete)
**If entire microservices architecture fails:**
1. Update DNS to point back to old server
2. Start monolithic application on old server
3. Traffic routes back to monolith
4. Investigate and fix issues
5. Plan re-migration

---

## Daily Checklist (During Migration)

### Every Morning
- [ ] Check CloudWatch alarms (any alerts overnight?)
- [ ] Review API Gateway metrics (request counts, latencies, errors)
- [ ] Check API costs (Groq + Voyage AI daily spend)
- [ ] Review ECS/Lambda logs for errors
- [ ] Check RDS performance (CPU, memory, connections)

### Every Evening
- [ ] Review day's deployment (any incidents?)
- [ ] Update migration status (Notion, Jira, etc.)
- [ ] Plan next day's tasks
- [ ] Notify team of progress and blockers

---

## Team Responsibilities

### Backend Developer(s)
- Extract services from monolith
- Write Dockerfiles and Lambda handlers
- Update API integrations
- Write tests (unit, integration)

### DevOps/Infrastructure Engineer
- Write CDK code for infrastructure
- Set up CI/CD pipelines
- Configure monitoring and alarms
- Manage AWS resources

### Frontend Developer(s)
- Update frontend apps to call API Gateway
- Deploy frontends to S3 + CloudFront
- Test UI with new backend services

### QA Engineer
- Write and execute test plans
- Performance testing (load testing)
- Security testing
- Document test results

### Project Manager
- Track progress (Gantt chart, Kanban board)
- Daily standups
- Risk management
- Stakeholder communication

---

## Risk Mitigation

### High-Risk Areas

1. **Database Migration**
   - **Risk**: Data loss or corruption during migration
   - **Mitigation**:
     - Full database backup before migration
     - Test migrations on staging first
     - Verify data integrity after migration

2. **Service Dependencies**
   - **Risk**: Service A depends on Service B, deployment order matters
   - **Mitigation**:
     - Deploy services in correct order (Auth → Document → Embedding → Chat)
     - Use feature flags to gradually enable new services

3. **Performance Regression**
   - **Risk**: New architecture is slower than expected
   - **Mitigation**:
     - Load testing on staging before production
     - Keep monolith running as backup
     - Gradual rollout (10% → 50% → 100%)

4. **Cost Overruns**
   - **Risk**: AWS costs exceed budget
   - **Mitigation**:
     - Set up billing alerts ($100, $500, $1000)
     - Daily cost reviews
     - Right-size resources (start small, scale up)

5. **Security Vulnerabilities**
   - **Risk**: Misconfigured security groups, exposed secrets
   - **Mitigation**:
     - Security review of CDK code
     - Use AWS Secrets Manager (no hardcoded secrets)
     - Enable WAF on API Gateway and CloudFront

---

## Success Criteria

### Technical Metrics
- ✅ **Performance**: P95 latency < 500ms (10x improvement)
- ✅ **Reliability**: 99.9% uptime (< 43 min downtime/month)
- ✅ **Scalability**: Handle 10x traffic without code changes
- ✅ **Cost**: Total monthly cost < $1000 (AWS + APIs)

### Business Metrics
- ✅ **User Experience**: Positive feedback on speed
- ✅ **Zero Downtime**: No customer-facing outages during migration
- ✅ **Team Velocity**: Faster feature development (independent services)

### Operational Metrics
- ✅ **Monitoring**: All critical metrics alarmed
- ✅ **Documentation**: Complete runbooks for all services
- ✅ **Team Training**: All team members trained on new architecture

---

## Next Steps (Post-Migration)

### Month 2: Feature Development
- Implement media responses (image search)
- Add multi-lingual support
- Widget streaming chat

### Month 3: Advanced Features
- A/B testing framework
- Advanced analytics (Athena + QuickSight)
- Customer usage dashboards

### Month 4: Optimization
- Multi-region deployment (if needed)
- Advanced caching strategies (CDN for chat responses)
- Cost optimization (spot instances, savings plans)

### Month 5: Enterprise Features
- SSO integration (SAML, OAuth)
- GDPR compliance tools
- SLA monitoring and reporting

---

## Resources

### AWS Documentation
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [ECS Fargate Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [RDS Aurora Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.BestPractices.html)

### API Providers
- [Groq Documentation](https://console.groq.com/docs)
- [Voyage AI Documentation](https://docs.voyageai.com/)

### Tools
- [AWS Calculator](https://calculator.aws/) - Estimate costs
- [Locust](https://locust.io/) - Load testing
- [k6](https://k6.io/) - Performance testing

---

## Conclusion

This roadmap provides a clear, week-by-week plan to migrate Raggy Muffin from a monolithic application to a scalable microservices architecture on AWS. By following this phased approach, you'll minimize risk, maintain uptime, and achieve significant performance improvements.

**Key Takeaways**:
1. Start with API provider migration (quick win)
2. Set up AWS infrastructure before extracting services
3. Extract services in order of risk (low → high)
4. Gradual production rollout (10% → 50% → 100%)
5. Monitor, optimize, and iterate

**Estimated Total Time**: 8-9 weeks
**Estimated Total Cost** (after migration): $575-900/month
**Expected Performance**: 10-20x faster responses
