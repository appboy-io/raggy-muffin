import streamlit as st
import pdfplumber
from embedding import chunk_text, embed_chunks
from db import insert_embeddings

def upload_page():
    st.title("📄 Upload a PDF")

    tenant_id = st.text_input("Tenant ID", "default_tenant")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        st.success(f"Extracted {len(full_text.split())} words.")

        if st.button("Process and Upload"):
            st.info("Chunking and embedding...")
            chunks = chunk_text(full_text)
            records = embed_chunks(chunks, tenant_id)

            st.info(f"Inserting {len(records)} chunks into database...")
            insert_embeddings(records)

            st.success("✅ Uploaded successfully!")
