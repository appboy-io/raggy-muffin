# Raggy Muffin Project Notes

This file contains development notes, future features, and technical documentation for the Raggy Muffin RAG platform.

## Performance Optimization - API Provider Migration

### Current Performance Issues
- Chat API responses taking 3-5+ seconds
- Ollama running on same machine competing for resources
- Excessive embedding calls (20-40 per chat request due to semantic filtering)
- Sequential processing without proper batching

### Selected Architecture (Production Ready)
**LLM Provider: Groq**
- Model: `llama3-70b-8192` or `mixtral-8x7b-32768`
- Speed: 500+ tokens/second (fastest in industry)
- Pricing: ~$0.10/1M tokens
- Benefits: Near-instant responses, excellent for customer-facing chat

**Embedding Provider: Voyage AI**
- Model: `voyage-02` (1024 dimensions) or `voyage-lite-02` for budget
- Speed: 30-50ms per request
- Pricing: $0.00002 per query
- Benefits: Purpose-built for RAG, superior retrieval performance

### Implementation Plan
1. **Phase 1 - Embedding Migration**
   - Replace Ollama embeddings with Voyage AI
   - Update `embed_query_async()` and `embed_chunks_async()` 
   - Batch embedding requests where possible
   - Add Redis caching layer for embeddings

2. **Phase 2 - LLM Migration**
   - Replace Ollama chat with Groq API
   - Update `generate_answer()` and streaming functions
   - Implement proper async/await patterns
   - Add fallback to Ollama for outages

3. **Phase 3 - Optimization**
   - Disable expensive semantic filtering (save 2-3 seconds)
   - Pre-compute and cache category embeddings
   - Implement response caching for common queries
   - Add connection pooling for PostgreSQL

### Cost Estimates (10K queries/day)
- LLM (Groq): ~$3/day (~$90/month)
- Embeddings (Voyage): ~$2/day (~$60/month)
- **Total: ~$150/month** (vs. current server costs and poor performance)

### Environment Variables Needed
```bash
# Groq Configuration
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama3-70b-8192
GROQ_MAX_TOKENS=2048
GROQ_TEMPERATURE=0.7

# Voyage AI Configuration
VOYAGE_API_KEY=your_api_key_here
VOYAGE_MODEL=voyage-02
VOYAGE_BATCH_SIZE=128

# Fallback Configuration
OLLAMA_HOST=http://localhost:11434  # Keep as backup
USE_OLLAMA_FALLBACK=true
```

### Expected Performance Improvements
- **Current**: 3-5+ seconds per response
- **After Migration**: 200-500ms per response (10-20x faster)
- **With Caching**: <100ms for repeated queries

### Migration Notes
- Keep Ollama running as fallback during transition
- Test with small subset of tenants first
- Monitor API costs daily during rollout
- Consider implementing rate limiting per tenant

---

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

### Session-based Multi-lingual Support with Auto-Detection
**Status**: Not implemented  
**Priority**: Medium-High  
**Description**: Automatically detect user's language and respond in the same language, with intelligent session-based language persistence.

**Implementation Approach**:
- **Automatic Language Detection**:
  - Detect language from user's first message in a session
  - Use lightweight library (langdetect or polyglot) for accurate detection
  - Support for 50+ languages out of the box
  - No user configuration required - just start typing

- **Session Intelligence**:
  - Remember detected language for entire chat session
  - Allow language switching mid-conversation if detected
  - Graceful fallback to English when language cannot be determined
  - Store language preference in chat session metadata

- **Smart Response Handling**:
  - Respond in user's detected language
  - Keep document quotes in original language
  - Translate system messages and errors
  - Mix languages appropriately (e.g., English documents, Spanish responses)

**Technical Implementation**:
```python
# Backend changes
class ChatSession:
    detected_language: str = None
    language_confidence: float = 0.0
    
    async def process_message(self, message: str):
        # First message: detect and store language
        if not self.detected_language:
            self.detected_language = detect(message)
            self.language_confidence = detect_confidence(message)
        
        # Add to system prompt
        system_prompt += f"\nUser language: {self.detected_language}"
        system_prompt += f"\nRespond in {self.detected_language}."
        system_prompt += "\nKeep document quotes in their original language."

# Database schema addition
chat_sessions: 
  - Add: detected_language VARCHAR(10)
  - Add: language_confidence FLOAT
```

**Widget UI Adaptation**:
- Auto-translate welcome message based on detected language
- Dynamically update placeholder text
- Translate error messages and system notifications
- Show subtle language indicator (flag or code)

**Advanced Features**:
- **Mixed Language Support**: Handle users who switch between languages
- **Regional Dialects**: Detect regional variations (es-MX vs es-ES)
- **RTL Support**: Automatically adjust UI for Arabic, Hebrew, etc.
- **Confidence Threshold**: Only auto-detect when confidence > 80%

**Benefits**:
- Zero configuration for users - just start chatting
- Natural multi-lingual conversations
- Improved accessibility for global users
- Better engagement with non-English speakers
- Maintains document integrity while localizing responses

**Use Cases**:
- Spanish-speaking user asks about English documentation
- Multi-lingual support teams serving global customers
- International businesses with diverse client base
- Educational platforms with students worldwide

**Dependencies**:
- Python langdetect or polyglot library
- LLM models already support multi-lingual responses
- Frontend RTL CSS support for Arabic/Hebrew
- Session storage for language persistence

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

### Semantic Context Filtering (RAG Improvement)
**Status**: Not implemented  
**Priority**: High (Next Development Task)  
**Description**: Improve RAG response accuracy by filtering context chunks based on semantic relevance to the user's query, preventing the LLM from pulling irrelevant information from mixed-content chunks.

**Current Problem**: 
- Large context chunks contain mixed information (e.g., physical therapy providers mixed with mental health providers)
- LLM sometimes selects wrong information from context (e.g., returning grief counseling phone number when asked about physical therapy)
- No keyword-based filtering needed - must scale automatically for any business type

**Implementation Approach**:
```python
async def filter_context_by_semantic_relevance(query: str, chunks: List[str], threshold: float = 0.7) -> List[str]:
    query_embedding = await embed_query_async(query)
    relevant_chunks = []
    
    for chunk in chunks:
        # Split chunk into sections (by bullets, paragraphs, etc.)
        sections = split_into_sections(chunk)
        for section in sections:
            section_embedding = await embed_query_async(section[:200])  # First 200 chars
            similarity = cosine_similarity(query_embedding, section_embedding)
            if similarity > threshold:
                relevant_chunks.append(section)
    
    return relevant_chunks[:3]  # Return top 3 most relevant
```

**Integration Points**:
- Modify `retrieve_relevant_chunks()` in `/api/app/core/rag.py`
- Add semantic filtering between similarity search and LLM generation
- Use existing embedding infrastructure (`embed_query_async`)

**Benefits**:
- **Zero maintenance** - Works automatically for any business type (restaurants, legal, medical, etc.)
- **Leverages existing infrastructure** - Uses current embedding system
- **Improves accuracy** - Prevents LLM from using irrelevant context information
- **Scalable** - No keyword lists to maintain as platform grows

**Technical Requirements**:
- Add section splitting logic (split by bullet points, paragraphs, headers)
- Implement cosine similarity calculation for embeddings  
- Add semantic relevance threshold configuration
- Integration with existing `retrieve_relevant_chunks` function

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