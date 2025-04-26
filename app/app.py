import streamlit as st
from upload import upload_page
from query import query_page

st.set_page_config(page_title="Multimodal RAG", page_icon="🧠")

pages = {
    "Upload PDF": upload_page,
    "Ask a Question": query_page
}

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", list(pages.keys()))
pages[page]()
