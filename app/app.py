import streamlit as st
from upload import upload_page
from query import query_page
import asyncio
import nest_asyncio
import sys

# Fix for asyncio "no running event loop" error
try:
    # Set event loop policy to avoid runtime errors
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Apply nest_asyncio to allow nested event loops
    # This allows asyncio to work within Streamlit
    nest_asyncio.apply()
except Exception as e:
    st.error(f"Error setting up asyncio: {e}")

# App configuration
st.set_page_config(
    page_title="RAG Q&A App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Error handling wrapper
try:
    pages = {
        "Upload PDF": upload_page,
        "Ask a Question": query_page
    }

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", list(pages.keys()))
    
    # Execute the selected page function
    pages[page]()
    
except Exception as e:
    st.error(f"Application error: {str(e)}")
    st.code(str(e))
