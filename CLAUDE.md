# Raggy Muffin Project Notes

This file contains development notes, future features, and technical documentation for the Raggy Muffin RAG platform.

## Future Features

### Media Responses with Semantic Image Search
**Status**: Not implemented  
**Priority**: High (Next Feature)  
**Description**: Allow tenants to upload images (JPEGs, PNGs) that can be automatically categorized and returned as relevant media responses in chat queries.

**Implementation Approach**:
- **Upload Interface**: Admin panel for bulk image uploads with drag & drop
- **Auto-Processing Pipeline**: 
  - OCR text extraction from images
  - AI-generated titles and descriptions
  - Automatic categorization (events, pricing, staff, products, etc.)
  - Keyword extraction from filename, OCR text, and content
- **Semantic Search Integration**:
  - Vector embeddings for image metadata (title, description, OCR text)
  - Context-aware matching with query intent
  - Relevance scoring combining semantic similarity and category matching
- **Enhanced Chat Response**:
  - Return relevant images alongside text responses
  - Include image metadata (title, description, relevance score)
  - Support for multiple images per response

**Database Schema**:
```sql
media_files: id, tenant_id, filename, title, description, category, keywords, ocr_text, file_url, thumbnail_url
media_embeddings: media_id, embedding_type, embedding_vector
```

**API Endpoints**:
- `POST /media/{tenant_id}/upload` - Bulk image upload with auto-processing
- `GET /media/{tenant_id}/search` - Find relevant images for queries
- Enhanced chat response format with media array

**Use Cases**:
- Event brochures: "What events do you have this summer?" → Returns festival flyers
- Pricing information: "How much does it cost?" → Shows pricing charts/tables
- Staff information: "Who can help me?" → Displays team photos
- Product catalogs: "What services do you offer?" → Shows service brochures

**Benefits**:
- Rich, visual chat responses
- Automatic content processing (minimal admin work)
- Semantic search ensures relevant image matching
- Scalable for large image libraries
- Works with any type of visual content (brochures, charts, photos, documents)

**Technical Requirements**:
- OCR service integration (for text extraction)
- Image processing and thumbnail generation
- Vector embedding service for semantic search
- File storage solution (local or cloud)
- Enhanced chat widget to display images

---

### Widget Streaming Chat
**Status**: Not implemented  
**Priority**: Medium  
**Description**: Add real-time streaming responses to the chat widget for better user experience.

**Implementation Approach**:
- Use Server-Sent Events (SSE) with existing `/stream` endpoint
- Modify widget's `sendMessage()` function to use streaming
- Create real-time updating message bubbles
- Handle stream events: `chunk`, `complete`, `error`
- Add typing indicator during streaming
- Implement graceful fallback to regular `/query` endpoint

**Benefits**:
- Immediate user feedback as response streams in
- Better perceived performance 
- Professional ChatGPT-like experience
- Especially helpful for long/detailed responses

**Technical Requirements**:
- Update widget embed script in `/api/app/routers/widgets.py`
- Ensure CORS support for streaming endpoint (already implemented)
- Handle connection reliability and mobile compatibility
- Maintain existing rate limiting

**Dependencies**: 
- Streaming endpoint already exists and supports tenant-specific CORS
- Current widget infrastructure supports the necessary changes

---

## Super Admin Platform Development

### Next Development Priorities
**Current Status**: Infrastructure complete - authentication, setup wizard, database models, and API endpoints are functional.

#### Phase 1 (Immediate - 1-2 days)
1. **Customer Management UI**
   - **Status**: API endpoints exist, UI needs implementation
   - **Description**: Complete the customers page with real data integration
   - **Features**: View customer details, suspend/activate accounts, edit profiles
   - **API Endpoints**: Already implemented in `/api/app/routers/superadmin.py`

2. **System Health Dashboard**
   - **Status**: Mock data in place, needs real API integration  
   - **Description**: Connect actual metrics from API and database
   - **Features**: API health, database status, error rates, response times
   - **Location**: Dashboard component needs real data integration

3. **Platform Analytics Overview**
   - **Status**: Mock data in place, needs real API integration
   - **Description**: Platform overview with actual usage statistics
   - **Features**: Total customers, document counts, query volumes, growth trends
   - **Implementation**: Connect existing analytics endpoints

#### Phase 2 (Short-term - 3-5 days)
1. **Customer Support Tools**
   - **Status**: Not implemented
   - **Description**: Advanced customer support and debugging tools
   - **Features**: Customer impersonation (with audit trail), support ticketing, usage debugging
   - **Security**: Secure impersonation with comprehensive audit logging

2. **Advanced Analytics Dashboard**
   - **Status**: Basic structure exists
   - **Description**: Detailed customer insights and platform trends
   - **Features**: Customer usage patterns, revenue analytics, churn analysis
   - **Charts**: Interactive dashboards with filtering and date ranges

3. **Configuration Management**
   - **Status**: Basic system config exists
   - **Description**: Platform-wide settings and feature management
   - **Features**: Feature flags, system limits, maintenance mode
   - **Interface**: Settings page with real configuration options

#### Phase 3 (Medium-term - 1-2 weeks)
1. **Billing & Revenue Management**
   - **Status**: Not implemented
   - **Description**: Comprehensive subscription and payment management
   - **Features**: Subscription plans, billing cycles, usage tracking, revenue analytics
   - **Integration**: Payment processor integration, automated billing

2. **Advanced Platform Administration**
   - **Status**: Not implemented
   - **Description**: Sophisticated platform management tools
   - **Features**: Rate limiting per customer, feature rollouts, A/B testing
   - **Automation**: Automated scaling, performance optimization

3. **Compliance & Security Tools**
   - **Status**: Not implemented
   - **Description**: Data governance and compliance management
   - **Features**: Data export, GDPR compliance, security auditing, backup management
   - **Reporting**: Compliance reports, security dashboards

### Technical Infrastructure Completed
- ✅ Production-ready React application with proper routing (`/superadmin`)
- ✅ JWT-based authentication system with secure token management
- ✅ Initial setup wizard for superadmin account creation
- ✅ Comprehensive database models (SuperAdmin, AuditLog, SystemConfig)
- ✅ RESTful API endpoints for all core operations
- ✅ Audit logging system for all administrative actions
- ✅ Nginx reverse proxy configuration with websocket support
- ✅ Production build pipeline with static asset optimization

### Architecture Notes
- **Database**: PostgreSQL with proper indexing for audit logs and analytics
- **Authentication**: JWT tokens with session management and automatic expiry
- **Security**: BCrypt password hashing, audit trail for all actions
- **Frontend**: React with React Router, TailwindCSS, and React Query
- **API**: FastAPI with SQLAlchemy ORM, async/sync hybrid approach
- **Deployment**: Docker containers with production optimization

---

## Completed Features

### Tenant-Specific CORS Configuration
**Completed**: 2024  
**Description**: Each tenant can configure which domains are allowed to embed their chat widget through the admin profile page.

### Test Site Integration
**Completed**: 2024  
**Description**: Admin panel includes a test site page to preview how the chat widget appears on customer websites with responsive device testing.

### Functional Chat Widget
**Completed**: 2024  
**Description**: JavaScript embed widget with full chat interface, proper styling, and integration with the RAG backend.