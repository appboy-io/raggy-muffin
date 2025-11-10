# Raggy Muffin Architecture Documentation Index

## Overview

This directory contains comprehensive architecture documentation for the Raggy Muffin multi-tenant RAG platform. These documents serve as the foundation for understanding the system design, planning the microservices migration, and onboarding new team members.

## Documents Included

### 1. ARCHITECTURE.md (18 KB)
**Comprehensive architecture documentation**

The definitive guide to the Raggy Muffin platform architecture. Includes:
- Detailed component breakdown (frontend, backend, services)
- Complete directory structure mapping
- Database schema documentation (17 tables)
- All API routers and endpoints
- Core processing pipelines (document processing, chat query flow)
- Background workers and async tasks
- Authentication and security implementation
- Docker deployment configurations
- Technology stack summary
- Key features and capabilities
- Performance characteristics
- Known technical debt and TODOs
- Ready-to-implement feature roadmap

**Best for**: Architects, technical leads, comprehensive system understanding

### 2. ARCHITECTURE_DIAGRAM.txt (17 KB)
**Visual ASCII diagrams of the system**

Multi-layered ASCII diagrams showing:
- Complete system architecture (frontend → API → services → data)
- All 8 services and their relationships
- 17 database tables organized by function
- Document processing pipeline (flow diagram)
- Chat query pipeline with filtering stages
- Multi-tenancy security model (7 isolation levels)
- Deployment structure and Docker services
- Key technologies and dependencies
- Multi-tenant data isolation visualization

**Best for**: Visual learners, system design discussions, presentations

### 3. QUICK_REFERENCE.md (8.2 KB)
**Developer cheat sheet and quick lookup guide**

Fast reference for developers working on the platform:
- At-a-glance component table (8 main components)
- Key files organized by function
- Complete API endpoint reference (35+ endpoints)
- Environment variables guide
- Practical example: Chat query data flow walkthrough
- Multi-tenant isolation explanation
- Performance metrics and optimization targets
- Common development commands
- Database connection info
- Monitoring and debugging guide
- Troubleshooting table (5 common issues)
- Important architectural notes
- Microservices migration recommendations

**Best for**: Daily development, debugging, API integration, quick lookups

### 4. ARCHITECTURE_EXPLORATION_SUMMARY.txt (9.4 KB)
**Executive summary of the exploration project**

High-level summary document covering:
- Project scope and deliverables
- Key architectural findings
- Technology stack summary
- API surface area overview
- Database schema overview
- Performance characteristics
- Multi-tenancy architecture
- Deployment variations
- Architectural decisions (strengths and weaknesses)
- Readiness assessment for microservices migration
- Next steps and recommended timeline
- Files generated and locations

**Best for**: Project management, stakeholder updates, quick overview

## How to Use These Documents

### For Understanding the System
1. Start with **ARCHITECTURE_DIAGRAM.txt** for visual overview
2. Read **QUICK_REFERENCE.md** for key components and endpoints
3. Dive into **ARCHITECTURE.md** for detailed information
4. Refer to **ARCHITECTURE_EXPLORATION_SUMMARY.txt** for context

### For Development Work
- Use **QUICK_REFERENCE.md** daily for:
  - Endpoint lookup
  - Environment variables
  - Development commands
  - Debugging guides
- Reference **ARCHITECTURE.md** for:
  - Detailed API documentation
  - Database schema details
  - Processing pipeline logic

### For Architecture Decisions
- Consult **ARCHITECTURE.md** for:
  - Current design rationale
  - Known limitations
  - Performance characteristics
  - Technical debt assessment
- Review **ARCHITECTURE_EXPLORATION_SUMMARY.txt** for:
  - Microservices readiness
  - Service boundary recommendations
  - Migration planning

### For Onboarding
1. Read **ARCHITECTURE_EXPLORATION_SUMMARY.txt** (5 min)
2. Study **ARCHITECTURE_DIAGRAM.txt** (10 min)
3. Reference **QUICK_REFERENCE.md** for API details (15 min)
4. Deep dive into **ARCHITECTURE.md** as needed (30+ min)

## Key Insights

### System Characteristics
- **Monolithic architecture**: Single FastAPI backend with clear separation of concerns
- **Multi-tenant design**: Database-enforced tenant isolation with 7 security layers
- **Production-ready**: Comprehensive security, rate limiting, audit logging
- **White-label capable**: Flexible branding and domain configuration
- **Performance bottleneck**: Self-hosted Ollama (planned migration to Groq + Voyage)

### Microservices Readiness
The platform is well-suited for decomposition into 8 independent services:
1. Auth Service
2. Document Service
3. Embedding Service
4. RAG/Chat Service
5. Widget Service
6. Admin Service
7. Super Admin Service
8. Analytics Service

See **ARCHITECTURE_EXPLORATION_SUMMARY.txt** for detailed migration strategy.

### Technology Stack
- Backend: FastAPI, SQLAlchemy, PostgreSQL+pgvector
- Frontend: React, TailwindCSS, React Query
- Infrastructure: Docker, Ollama, Redis, AWS Cognito
- Total codebase: ~15,000 Python LOC + ~5,000 React LOC

## Quick Facts

- **Main API Port**: 8000
- **Frontend Ports**: 3000 (admin), 3001 (widget), 3003 (super-admin)
- **Database Tables**: 17
- **API Endpoints**: 35+
- **Docker Services**: 8 (production), 5 (development)
- **Environment Configurations**: 5 different docker-compose files
- **Development Setup**: `docker compose -f docker-compose.dev.yml up`
- **Current Performance**: 3-5 second response time
- **Target Performance**: 200-500ms (post-Groq migration)

## File Organization in Repository

```
/home/cleona_app/raggy-muffin/
├── DOCUMENTATION_INDEX.md           (This file)
├── ARCHITECTURE.md                  (Comprehensive guide)
├── ARCHITECTURE_DIAGRAM.txt         (Visual diagrams)
├── QUICK_REFERENCE.md               (Developer cheat sheet)
├── ARCHITECTURE_EXPLORATION_SUMMARY.txt (Executive summary)
├── api/                             (FastAPI backend)
├── admin-ui/                        (React admin dashboard)
├── frontend-ui/                     (React chat widget)
├── super-admin-ui/                  (React platform admin)
├── app/                             (Legacy Streamlit)
├── docker-compose*.yml              (5 configurations)
└── init.sql                         (Database schema)
```

## Document Statistics

| Document | Size | Lines | Focus |
|----------|------|-------|-------|
| ARCHITECTURE.md | 18 KB | 600+ | Complete reference |
| ARCHITECTURE_DIAGRAM.txt | 17 KB | 350+ | Visual overview |
| QUICK_REFERENCE.md | 8.2 KB | 250+ | Developer guide |
| ARCHITECTURE_EXPLORATION_SUMMARY.txt | 9.4 KB | 280+ | Executive summary |

## Navigation Tips

- All documents use standard markdown and text formatting
- Tables for quick reference information
- Code blocks for configuration and commands
- Clear section headings for easy searching
- Cross-references between documents
- Line-of-code counts for complexity estimation

## Next Steps

1. **For New Team Members**: Start with ARCHITECTURE_EXPLORATION_SUMMARY.txt, then QUICK_REFERENCE.md
2. **For Architecture Planning**: Review all documents, then ARCHITECTURE_EXPLORATION_SUMMARY.txt's microservices section
3. **For Development Work**: Keep QUICK_REFERENCE.md open while coding
4. **For System Deep Dive**: Study ARCHITECTURE.md section by section
5. **For Presentations**: Use ARCHITECTURE_DIAGRAM.txt for visual aids

## Questions or Updates?

These documents were generated through comprehensive codebase analysis on 2025-11-04.

Key findings are based on:
- Manual code review (routers, models, configuration)
- Docker Compose file analysis
- Database schema inspection
- Dependency analysis
- Performance profiling data from CLAUDE.md

For the most current information, always refer back to the actual source code.

---

**Generated**: 2025-11-04
**Architecture Snapshot**: Complete system analysis
**Maintenance**: Update when major architectural changes occur
