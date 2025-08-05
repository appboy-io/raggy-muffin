import streamlit as st
import pdfplumber
import pandas as pd
import io
from embedding import chunk_text, embed_chunks
from db import insert_embeddings
from extraction import extract_structured_data, normalize_text
from llm_extraction import extract_structured_data_llm
from auth import CognitoAuth
import time

def upload_workflow_page():
    """Main upload workflow with paginated onboarding-style interface"""
    
    # Require authentication
    auth = CognitoAuth()
    if not auth.is_authenticated():
        st.warning("🔒 Please log in to upload documents.")
        st.info("👈 Use the navigation sidebar to sign in or create an account.")
        return
    
    # Initialize session state for workflow
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'workflow_data' not in st.session_state:
        st.session_state.workflow_data = {}
        # Automatically set tenant ID from authenticated user
        st.session_state.workflow_data['tenant_id'] = auth.get_tenant_id()
    
    # Progress bar
    total_steps = 5
    progress = (st.session_state.workflow_step - 1) / (total_steps - 1)
    st.progress(progress)
    
    # Step indicator
    step_names = ["Upload", "Configure", "Preview", "Confirm", "Complete"]
    st.write(f"**Step {st.session_state.workflow_step} of {total_steps}: {step_names[st.session_state.workflow_step - 1]}**")
    
    # Route to appropriate step
    if st.session_state.workflow_step == 1:
        step_1_upload()
    elif st.session_state.workflow_step == 2:
        step_2_configure()
    elif st.session_state.workflow_step == 3:
        step_3_preview()
    elif st.session_state.workflow_step == 4:
        step_4_confirm()
    elif st.session_state.workflow_step == 5:
        step_5_complete()

def step_1_upload():
    """Step 1: File Upload"""
    st.title("📁 Upload Your Document")
    st.write("Select and upload the document you want to process for your knowledge base.")
    
    # Show current user and tenant info
    tenant_id = st.session_state.workflow_data.get('tenant_id')
    username = st.session_state.get('username', 'Unknown')
    
    st.info(f"👤 **Logged in as:** {username}")
    st.info(f"🏢 **Your workspace:** {tenant_id[:8]}...") # Show first 8 chars of tenant ID for privacy
    
    # File upload with auto-detection
    st.info("📄 **Supported Formats:** PDF documents, CSV/Excel spreadsheets, and text files (TXT, MD, RST)")
    
    uploaded_file = st.file_uploader(
        "Choose your document",
        type=["pdf", "csv", "xlsx", "xls", "txt", "md", "rst"],
        help="Upload any supported document format - we'll automatically detect the type"
    )
    
    # Auto-detect file type from upload
    if uploaded_file:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == 'pdf':
            file_type = "PDF"
        elif file_extension == 'csv':
            file_type = "CSV"
        elif file_extension in ['xlsx', 'xls']:
            file_type = "Excel"
        else:  # txt, md, rst
            file_type = "Text"
        
        st.session_state.workflow_data['file_type'] = file_type
        st.success(f"📋 Detected format: **{file_type}**")
    
    if uploaded_file:
        # Extract text based on file type
        with st.spinner("Reading document..."):
            if file_type == "PDF":
                full_text = extract_pdf_text(uploaded_file)
            elif file_type == "CSV":
                full_text = extract_csv_text(uploaded_file)
            elif file_type == "Excel":
                full_text = extract_excel_text(uploaded_file)
            else:  # Text
                full_text = extract_text_file(uploaded_file)
        
        if full_text:
            # Store in workflow data
            st.session_state.workflow_data['full_text'] = full_text
            st.session_state.workflow_data['filename'] = uploaded_file.name
            
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Size", f"{uploaded_file.size:,} bytes")
            with col2:
                st.metric("Word Count", f"{len(full_text.split()):,}")
            with col3:
                st.metric("Character Count", f"{len(full_text):,}")
            
            # Preview first 300 characters
            st.write("**Document Preview:**")
            st.text_area("", full_text[:300] + "..." if len(full_text) > 300 else full_text, height=100, disabled=True)
            
            # Navigation
            col1, col2 = st.columns([1, 1])
            with col2:
                if st.button("Next: Configure Processing →", type="primary", use_container_width=True):
                    st.session_state.workflow_step = 2
                    st.rerun()
        else:
            st.error("Could not extract text from the uploaded file. Please try a different file.")
    else:
        st.info("Upload a file to continue")

def step_2_configure():
    """Step 2: Configure Processing Options"""
    st.title("⚙️ Configure Processing")
    st.write("Choose how you want your document to be processed and structured.")
    
    # Show file info
    st.write(f"**File:** {st.session_state.workflow_data.get('filename', 'Unknown')}")
    st.write(f"**Type:** {st.session_state.workflow_data.get('file_type', 'Unknown')}")
    
    # Processing options - AI extraction is always enabled
    st.info("🤖 **AI-Powered Data Extraction** - Automatically extracts provider names, categories, contact information, and service descriptions using advanced language models.")
    st.session_state.workflow_data['use_structured'] = True
    st.session_state.workflow_data['extraction_method'] = 'llm'
    
    # Get word count for intelligent chunking
    word_count = len(st.session_state.workflow_data.get('full_text', '').split())
    
    # Intelligent chunking based on document size
    st.write("**📄 Intelligent Text Processing:**")
    
    # Calculate optimal chunk size based on document length
    if word_count <= 500:
        recommended_chunks = 1
        chunk_size = word_count
        chunking_strategy = "Single chunk - Document is small enough to process as one piece"
    elif word_count <= 1500:
        recommended_chunks = 2
        chunk_size = word_count // 2
        chunking_strategy = "Two chunks - Split document in half for balanced processing"
    elif word_count <= 3000:
        recommended_chunks = 3
        chunk_size = word_count // 3
        chunking_strategy = "Three chunks - Optimal for medium-sized documents"
    else:
        recommended_chunks = max(3, min(6, word_count // 500))
        chunk_size = word_count // recommended_chunks
        chunking_strategy = f"{recommended_chunks} chunks - Large document split for efficient processing"
    
    # Display chunking analysis
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document Size", f"{word_count:,} words")
    with col2:
        st.metric("Recommended Chunks", recommended_chunks)
    with col3:
        st.metric("Words per Chunk", f"~{chunk_size:,}")
    
    st.info(f"💡 **Strategy**: {chunking_strategy}")
    
    # Allow manual override
    use_custom_chunking = st.checkbox(
        "Customize chunking strategy",
        value=False,
        help="Override the automatic chunking recommendation"
    )
    
    if use_custom_chunking:
        chunk_size = st.slider(
            "Custom chunk size (words)",
            min_value=100,
            max_value=min(1000, word_count),
            value=chunk_size,
            step=50,
            help="Smaller chunks = more precise search, Larger chunks = more context"
        )
        estimated_chunks = max(1, word_count // chunk_size)
        st.write(f"📊 This will create approximately **{estimated_chunks} chunks**")
    
    st.session_state.workflow_data['chunk_size'] = chunk_size
    st.session_state.workflow_data['chunking_strategy'] = chunking_strategy
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Upload", use_container_width=True):
            st.session_state.workflow_step = 1
            st.rerun()
    with col2:
        if st.button("Next: Preview Data →", type="primary", use_container_width=True):
            st.session_state.workflow_step = 3
            st.rerun()

def step_3_preview():
    """Step 3: Preview Extracted Data"""
    st.title("👀 Preview Extracted Data")
    st.write("Review the processed data before saving to your knowledge base.")
    
    # Process the data
    if 'processed_data' not in st.session_state.workflow_data:
        with st.spinner("Processing document with AI extraction..."):
            # Always use LLM extraction
            extracted_data = extract_structured_data_llm(
                st.session_state.workflow_data['full_text'],
                st.session_state.workflow_data['file_type'].lower()
            )
            
            st.session_state.workflow_data['processed_data'] = extracted_data
            st.session_state.workflow_data['final_text'] = normalize_text(extracted_data)
    
    # Show extraction results
    if st.session_state.workflow_data.get('use_structured') and st.session_state.workflow_data.get('processed_data'):
        show_structured_preview(st.session_state.workflow_data['processed_data'])
    else:
        show_raw_preview(st.session_state.workflow_data['final_text'])
    
    # Show chunking preview with configured chunk size
    chunk_size = st.session_state.workflow_data.get('chunk_size', 300)
    chunks = chunk_text(st.session_state.workflow_data['final_text'], chunk_size=chunk_size)
    st.write(f"**📄 Text will be split into {len(chunks)} chunks for embedding**")
    
    # Show chunking details
    actual_chunk_sizes = [len(chunk.split()) for chunk in chunks]
    avg_chunk_size = sum(actual_chunk_sizes) / len(actual_chunk_sizes) if chunks else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Chunks", len(chunks))
    with col2:
        st.metric("Avg Words/Chunk", f"{avg_chunk_size:.0f}")
    with col3:
        st.metric("Target Size", chunk_size)
    
    with st.expander("Preview First 3 Chunks"):
        for i, chunk in enumerate(chunks[:3]):
            st.write(f"**Chunk {i+1}:**")
            st.text_area("", chunk[:200] + "..." if len(chunk) > 200 else chunk, height=80, disabled=True, key=f"chunk_{i}")
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Configure", use_container_width=True):
            st.session_state.workflow_step = 2
            st.rerun()
    with col2:
        if st.button("Next: Confirm & Save →", type="primary", use_container_width=True):
            st.session_state.workflow_step = 4
            st.rerun()

def step_4_confirm():
    """Step 4: Final Confirmation"""
    st.title("✅ Confirm & Save")
    st.write("Ready to save your document to the knowledge base? Review the summary below.")
    
    # Summary card
    with st.container():
        st.write("### 📋 Processing Summary")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Document Details:**")
            st.write(f"• File: {st.session_state.workflow_data.get('filename')}")
            st.write(f"• Type: {st.session_state.workflow_data.get('file_type')}")
            st.write(f"• Size: {len(st.session_state.workflow_data.get('full_text', '')):,} characters")
            st.write(f"• Tenant: {st.session_state.workflow_data.get('tenant_id')}")
        
        with col2:
            st.write("**Processing Settings:**")
            st.write("• Smart Extraction: AI-Powered")
            st.write("• Method: LLM-based extraction")
            
            chunk_size = st.session_state.workflow_data.get('chunk_size', 300)
            chunks = chunk_text(st.session_state.workflow_data.get('final_text', ''), chunk_size=chunk_size)
            st.write(f"• Chunks: {len(chunks)} pieces")
            st.write(f"• Chunk Size: ~{chunk_size} words")
            strategy = st.session_state.workflow_data.get('chunking_strategy', 'Intelligent chunking')
            st.write(f"• Strategy: {strategy}")
    
    # Final confirmation
    st.write("### 🚀 Ready to Process")
    st.info("This will embed your document and make it searchable in your knowledge base. This action cannot be undone.")
    
    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Preview", use_container_width=True):
            st.session_state.workflow_step = 3
            st.rerun()
    with col2:
        if st.button("🚀 Process & Save Document", type="primary", use_container_width=True):
            process_and_save()

def step_5_complete():
    """Step 5: Completion Status"""
    st.title("🎉 Upload Complete!")
    
    # Success message
    st.success("Your document has been successfully processed and added to the knowledge base!")
    
    # Show processing results
    if 'processing_results' in st.session_state.workflow_data:
        results = st.session_state.workflow_data['processing_results']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chunks Created", results.get('chunks_count', 0))
        with col2:
            st.metric("Embeddings Generated", results.get('embeddings_count', 0))
        with col3:
            st.metric("Processing Time", f"{results.get('processing_time', 0):.1f}s")
    
    # What's next
    st.write("### 🔍 What's Next?")
    st.write("• Your document is now searchable in the knowledge base")
    st.write("• Use the 'Ask a Question' page to query your documents")
    st.write("• Upload more documents to expand your knowledge base")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Upload Another Document", use_container_width=True):
            reset_workflow()
            st.rerun()
    with col2:
        if st.button("🔍 Ask Questions", type="primary", use_container_width=True):
            st.info("Use the navigation menu to go to 'Ask a Question' page")
    with col3:
        if st.button("📊 View All Documents", use_container_width=True):
            st.info("Use the navigation menu to go to 'Document Manager' page")

def process_and_save():
    """Process and save the document with progress tracking"""
    start_time = time.time()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Chunk the text
        status_text.text("Creating text chunks...")
        progress_bar.progress(25)
        chunk_size = st.session_state.workflow_data.get('chunk_size', 300)
        chunks = chunk_text(st.session_state.workflow_data['final_text'], chunk_size=chunk_size)
        
        # Step 2: Generate embeddings
        status_text.text("Generating embeddings...")
        progress_bar.progress(50)
        records = embed_chunks(chunks, st.session_state.workflow_data['tenant_id'])
        
        # Step 3: Save to database
        status_text.text("Saving to database...")
        progress_bar.progress(75)
        insert_embeddings(records)
        
        # Step 4: Complete
        status_text.text("Processing complete!")
        progress_bar.progress(100)
        
        # Store results
        processing_time = time.time() - start_time
        st.session_state.workflow_data['processing_results'] = {
            'chunks_count': len(chunks),
            'embeddings_count': len(records),
            'processing_time': processing_time
        }
        
        time.sleep(1)  # Brief pause to show completion
        st.session_state.workflow_step = 5
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing document: {str(e)}")
        status_text.text("Processing failed!")

def reset_workflow():
    """Reset the workflow to start over"""
    st.session_state.workflow_step = 1
    st.session_state.workflow_data = {}

def show_structured_preview(extracted_data):
    """Show preview of structured data"""
    st.write("### 📊 Extracted Structured Data")
    
    # Provider name
    if extracted_data.get("provider_name"):
        st.write("**Provider/Organization:**")
        st.write(f"• {extracted_data['provider_name']}")
        st.write("")
    
    # Categories
    if extracted_data.get("categories"):
        st.write("**Categories Found:**")
        for category, terms in extracted_data["categories"].items():
            st.write(f"• {category}: {', '.join(terms[:3])}")
        st.write("")
    
    # Contacts
    contacts = extracted_data.get("contacts", {})
    if any(contacts.values()):
        st.write("**Contact Information:**")
        for contact_type, values in contacts.items():
            if values:
                st.write(f"• {contact_type.title()}: {', '.join(values[:2])}")
        st.write("")
    
    # Description
    if extracted_data.get("description"):
        st.write("**Description:**")
        st.write(extracted_data["description"][:200] + "..." if len(extracted_data["description"]) > 200 else extracted_data["description"])

def show_raw_preview(text):
    """Show preview of raw text"""
    st.write("### 📄 Raw Text Preview")
    st.text_area("Document content:", text[:500] + "..." if len(text) > 500 else text, height=200, disabled=True)

# Helper functions from original upload.py
def extract_pdf_text(pdf_file):
    """Extract text from a PDF file"""
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text

def extract_csv_text(csv_file):
    """Extract and format text from a CSV file"""
    try:
        df = pd.read_csv(csv_file)
        text_chunks = []
        
        for _, row in df.iterrows():
            chunk = ""
            for col in df.columns:
                if pd.notna(row[col]):
                    chunk += f"{col}: {row[col]}\n"
            text_chunks.append(chunk)
            
        return "\n\n".join(text_chunks)
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}")
        return ""

def extract_excel_text(excel_file):
    """Extract and format text from an Excel file"""
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
        text_chunks = []
        
        for _, row in df.iterrows():
            chunk = ""
            for col in df.columns:
                if pd.notna(row[col]):
                    chunk += f"{col}: {row[col]}\n"
            text_chunks.append(chunk)
            
        return "\n\n".join(text_chunks)
    except Exception as e:
        st.error(f"Error processing Excel file: {str(e)}")
        return ""

def extract_text_file(text_file):
    """Extract text from a plain text file"""
    try:
        content = text_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return content
    except Exception as e:
        st.error(f"Error processing text file: {str(e)}")
        return ""