import streamlit as st
import pandas as pd
from db import engine
from sqlalchemy import text
import json

def document_manager_page():
    """Document management and status viewing page"""
    st.title("📚 Document Manager")
    st.write("View and manage your uploaded documents and their processing status.")
    
    # Tenant selector
    tenant_id = st.text_input("Tenant ID", "default_tenant")
    
    if st.button("Load Documents", type="primary"):
        load_document_data(tenant_id)
    
    # Show document data if available
    if 'document_data' in st.session_state:
        show_document_dashboard(st.session_state.document_data)

def load_document_data(tenant_id):
    """Load document data from the database"""
    try:
        with engine.connect() as conn:
            # Get embedding data with aggregated stats
            result = conn.execute(
                text("""
                    SELECT 
                        content,
                        created_at,
                        LENGTH(content) as content_length,
                        (embedding IS NOT NULL) as has_embedding
                    FROM embeddings 
                    WHERE tenant_id = :tenant
                    ORDER BY created_at DESC
                """),
                {"tenant": tenant_id}
            )
            
            rows = result.fetchall()
            
            if rows:
                # Process the data
                documents = []
                current_doc = None
                
                for row in rows:
                    content = row[0]
                    created_at = row[1]
                    content_length = row[2]
                    has_embedding = row[3]
                    
                    # Try to identify separate documents by looking for document headers
                    if is_document_header(content):
                        # This looks like a new document
                        if current_doc:
                            documents.append(current_doc)
                        
                        current_doc = {
                            'title': extract_document_title(content),
                            'created_at': created_at,
                            'chunks': 1,
                            'total_length': content_length,
                            'has_embeddings': has_embedding,
                            'preview': content[:200] + "..." if len(content) > 200 else content
                        }
                    else:
                        # This is likely a chunk from the current document
                        if current_doc:
                            current_doc['chunks'] += 1
                            current_doc['total_length'] += content_length
                        else:
                            # Fallback - create a document entry
                            current_doc = {
                                'title': f"Document from {created_at.strftime('%Y-%m-%d %H:%M')}",
                                'created_at': created_at,
                                'chunks': 1,
                                'total_length': content_length,
                                'has_embeddings': has_embedding,
                                'preview': content[:200] + "..." if len(content) > 200 else content
                            }
                
                # Add the last document
                if current_doc:
                    documents.append(current_doc)
                
                st.session_state.document_data = documents
                st.success(f"Loaded {len(documents)} documents with {sum(d['chunks'] for d in documents)} total chunks")
            else:
                st.warning(f"No documents found for tenant: {tenant_id}")
                st.session_state.document_data = []
                
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
        st.session_state.document_data = []

def is_document_header(content):
    """Check if content looks like a document header/start"""
    # Look for structured data indicators or file-like headers
    indicators = [
        "CATEGORIES:",
        "CONTACT INFORMATION:", 
        "DESCRIPTION:",
        "File:",
        "Document:",
        "Title:",
        "Organization:"
    ]
    return any(indicator in content for indicator in indicators)

def extract_document_title(content):
    """Extract a meaningful title from document content"""
    lines = content.split('\n')
    
    # Look for title patterns
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and len(line) > 10 and len(line) < 100:
            # Skip pure category/contact lines
            if not any(skip in line for skip in ["CATEGORIES:", "CONTACT:", "Email:", "Phone:"]):
                return line
    
    # Fallback - use first meaningful text
    words = content.split()[:10]
    return ' '.join(words) + "..." if len(words) == 10 else ' '.join(words)

def show_document_dashboard(documents):
    """Display the document dashboard"""
    if not documents:
        st.info("No documents found. Upload some documents to get started!")
        return
    
    # Summary metrics
    st.subheader("📊 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    total_docs = len(documents)
    total_chunks = sum(d['chunks'] for d in documents)
    total_size = sum(d['total_length'] for d in documents)
    embedded_docs = sum(1 for d in documents if d['has_embeddings'])
    
    with col1:
        st.metric("Total Documents", total_docs)
    with col2:
        st.metric("Total Chunks", total_chunks)
    with col3:
        st.metric("Total Size", f"{total_size:,} chars")
    with col4:
        st.metric("Embedded", f"{embedded_docs}/{total_docs}")
    
    # Document list
    st.subheader("📋 Document List")
    
    # Create DataFrame for display
    display_data = []
    for i, doc in enumerate(documents):
        display_data.append({
            "Title": doc['title'][:50] + "..." if len(doc['title']) > 50 else doc['title'],
            "Uploaded": doc['created_at'].strftime('%Y-%m-%d %H:%M'),
            "Chunks": doc['chunks'],
            "Size": f"{doc['total_length']:,} chars",
            "Status": "✅ Embedded" if doc['has_embeddings'] else "⏳ Processing"
        })
    
    df = pd.DataFrame(display_data)
    
    # Add selection capability
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Show selected document details
    if hasattr(selected_indices, 'selection') and selected_indices.selection.rows:
        selected_idx = selected_indices.selection.rows[0]
        show_document_details(documents[selected_idx])

def show_document_details(document):
    """Show detailed view of a selected document"""
    st.subheader("🔍 Document Details")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Title:**", document['title'])
        st.write("**Preview:**")
        st.text_area("", document['preview'], height=150, disabled=True)
    
    with col2:
        st.write("**Metadata:**")
        st.write(f"• Uploaded: {document['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"• Chunks: {document['chunks']}")
        st.write(f"• Total Size: {document['total_length']:,} characters")
        st.write(f"• Status: {'✅ Embedded' if document['has_embeddings'] else '⏳ Processing'}")
        
        # Action buttons
        st.write("**Actions:**")
        if st.button("🗑️ Delete Document", key=f"delete_{document['created_at']}"):
            st.warning("Delete functionality coming soon!")
        
        if st.button("🔄 Re-process", key=f"reprocess_{document['created_at']}"):
            st.info("Re-processing functionality coming soon!")

def show_upload_statistics():
    """Show upload and processing statistics"""
    st.subheader("📈 Upload Statistics")
    
    # This could be expanded to show:
    # - Upload trends over time
    # - Processing success rates
    # - Most common document types
    # - Average processing times
    
    st.info("Detailed statistics coming soon!")

if __name__ == "__main__":
    document_manager_page()