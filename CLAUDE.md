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