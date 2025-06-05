import streamlit as st
import pdfplumber
import pandas as pd
import io
from embedding import chunk_text, embed_chunks
from db import insert_embeddings
from extraction import extract_structured_data, normalize_text
from llm_extraction import extract_structured_data_llm

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
        # Convert DataFrame to a structured text format
        text_chunks = []
        
        for _, row in df.iterrows():
            # Create a text representation of each row
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
        # Convert DataFrame to a structured text format
        text_chunks = []
        
        for _, row in df.iterrows():
            # Create a text representation of each row
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
        # Read the text file
        content = text_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return content
    except Exception as e:
        st.error(f"Error processing text file: {str(e)}")
        return ""

def upload_page():
    st.title("📄 Upload Documents")

    tenant_id = st.text_input("Tenant ID", "default_tenant")
    
    file_type = st.radio("Select file type:", ["PDF", "CSV", "Excel", "Text"])
    
    full_text = ""
    uploaded_file = None
    
    if file_type == "PDF":
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file:
            full_text = extract_pdf_text(uploaded_file)
            st.success(f"Extracted {len(full_text.split())} words from PDF.")
    elif file_type == "CSV":
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded_file:
            full_text = extract_csv_text(uploaded_file)
            st.success(f"Processed CSV data with {len(full_text.split())} words.")
    elif file_type == "Excel":
        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
        if uploaded_file:
            full_text = extract_excel_text(uploaded_file)
            st.success(f"Processed Excel data with {len(full_text.split())} words.")
    else:  # Text
        uploaded_file = st.file_uploader("Upload a text file", type=["txt", "md", "rst"])
        if uploaded_file:
            full_text = extract_text_file(uploaded_file)
            st.success(f"Processed text file with {len(full_text.split())} words.")
    
    if uploaded_file and full_text:
        # Add option for structured data extraction
        use_structured_extraction = st.checkbox("Normalize and extract structured data (categories, contacts, services)")
        
        # Add option for extraction method if structured extraction is selected
        extraction_method = "traditional"
        if use_structured_extraction:
            extraction_method = st.radio(
                "Choose extraction method:",
                ["traditional", "llm"],
                format_func=lambda x: "Traditional (spaCy + regex)" if x == "traditional" else "LLM-based (AI extraction)",
                help="Traditional method uses regex patterns and spaCy NER. LLM method uses AI for more flexible extraction."
            )
        
        if st.button("Extract and Preview Data"):
            with st.spinner("Processing document..."):
                if use_structured_extraction:
                    if extraction_method == "llm":
                        st.info("Extracting structured data using LLM...")
                        extracted_data = extract_structured_data_llm(full_text, file_type.lower())
                    else:
                        st.info("Extracting structured data using traditional methods...")
                        extracted_data = extract_structured_data(full_text)
                    
                    # Store in session state for later use
                    st.session_state.extracted_data = extracted_data
                    st.session_state.full_text = full_text
                    st.session_state.use_structured = True
                    st.session_state.extraction_method = extraction_method
                    
                    show_data_preview(extracted_data, full_text, extraction_method)
                else:
                    # For raw text, show preview of chunks that will be created
                    st.session_state.full_text = full_text
                    st.session_state.use_structured = False
                    show_raw_text_preview(full_text)
        
        # Show embedding confirmation if data has been processed
        if hasattr(st.session_state, 'full_text'):
            show_embedding_confirmation(tenant_id)

def show_data_preview(extracted_data, full_text, extraction_method="traditional"):
    """Display a preview table of extracted structured data"""
    st.subheader("📋 Data Preview")
    method_label = "LLM-based AI extraction" if extraction_method == "llm" else "Traditional spaCy + regex extraction"
    st.write(f"Review the extracted data before embedding (using {method_label}):")
    
    # Create preview data for table
    preview_data = []
    
    # Add provider name
    if extracted_data.get("provider_name"):
        preview_data.append({
            "Type": "Provider",
            "Field": "Organization Name",
            "Value": extracted_data["provider_name"],
            "Count": 1
        })
    
    # Add categories
    if extracted_data["categories"]:
        for category, terms in extracted_data["categories"].items():
            preview_data.append({
                "Type": "Category", 
                "Field": category,
                "Value": ", ".join(terms[:3]) + ("..." if len(terms) > 3 else ""),
                "Count": len(terms)
            })
    
    # Add contact information
    contacts = extracted_data["contacts"]
    for contact_type, values in contacts.items():
        if values:
            preview_data.append({
                "Type": "Contact",
                "Field": contact_type.capitalize(),
                "Value": ", ".join(values[:2]) + ("..." if len(values) > 2 else ""),
                "Count": len(values)
            })
    
    # Add description
    if extracted_data["description"]:
        preview_data.append({
            "Type": "Description",
            "Field": "Service Description",
            "Value": extracted_data["description"][:100] + ("..." if len(extracted_data["description"]) > 100 else ""),
            "Count": len(extracted_data["description"].split())
        })
    
    if preview_data:
        df = pd.DataFrame(preview_data)
        st.table(df)
        
        # Show normalized text preview
        normalized_text = normalize_text(extracted_data)
        with st.expander("View Normalized Text (what will be embedded)"):
            st.text_area("Normalized text:", normalized_text, height=200, disabled=True)
    else:
        st.warning("No structured data could be extracted from this document.")
        st.info("Consider uploading without structured extraction or try a different document.")

def show_raw_text_preview(full_text):
    """Display preview of raw text chunks"""
    st.subheader("📋 Raw Text Preview")
    
    chunks = chunk_text(full_text)
    
    preview_data = []
    for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
        preview_data.append({
            "Chunk": i + 1,
            "Preview": chunk[:100] + ("..." if len(chunk) > 100 else ""),
            "Length": len(chunk.split())
        })
    
    df = pd.DataFrame(preview_data)
    st.table(df)
    
    if len(chunks) > 5:
        st.info(f"Showing first 5 of {len(chunks)} total chunks")
    
    with st.expander("View Full Text Sample"):
        st.text_area("Full text (first 1000 chars):", full_text[:1000], height=200, disabled=True)

def show_embedding_confirmation(tenant_id):
    """Show confirmation buttons to proceed with embedding"""
    st.subheader("🚀 Ready to Embed")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Accept and Embed Data", type="primary", use_container_width=True):
            with st.spinner("Embedding and storing data..."):
                if st.session_state.use_structured:
                    normalized_text = normalize_text(st.session_state.extracted_data)
                    chunks = chunk_text(normalized_text)
                else:
                    chunks = chunk_text(st.session_state.full_text)
                
                records = embed_chunks(chunks, tenant_id)
                insert_embeddings(records)
                
                st.success("✅ Data successfully embedded and stored!")
                st.balloons()
                
                # Clear session state
                if 'extracted_data' in st.session_state:
                    del st.session_state.extracted_data
                if 'full_text' in st.session_state:
                    del st.session_state.full_text
                if 'use_structured' in st.session_state:
                    del st.session_state.use_structured
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            # Clear session state
            if 'extracted_data' in st.session_state:
                del st.session_state.extracted_data
            if 'full_text' in st.session_state:
                del st.session_state.full_text
            if 'use_structured' in st.session_state:
                del st.session_state.use_structured
            
            st.info("Process cancelled. You can upload a different file or try again.")
            st.rerun()
