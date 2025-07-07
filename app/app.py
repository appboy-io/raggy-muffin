import streamlit as st
from upload_workflow import upload_workflow_page
from query import query_page
from document_manager import document_manager_page
from product_page import product_page
from login_page import login_page
from signup_page import signup_page
from auth import CognitoAuth, require_auth
from config import config
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

# App configuration - optimized for performance
st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT,
    initial_sidebar_state="collapsed"  # Faster initial load
)

# Configure file upload limits and performance settings
st.session_state.setdefault('max_upload_size', 200)  # 200MB default

# Performance optimizations
if 'performance_initialized' not in st.session_state:
    st.session_state.performance_initialized = True

# Initialize authentication
auth = CognitoAuth()

# Error handling wrapper
try:
    # Define public pages (no authentication required)
    public_pages = {
        "🏠 Product Overview": product_page,
        "🔐 Sign In": login_page,
        "📝 Sign Up": signup_page
    }
    
    # Define protected pages (authentication required)
    protected_pages = {
        "📁 Upload Workflow": upload_workflow_page,
        "🔍 Ask a Question": query_page,
        "📚 Document Manager": document_manager_page
    }
    
    # Combine pages based on authentication status
    if auth.is_authenticated():
        # User is logged in - show all pages except sign up/sign in
        available_pages = {**public_pages}
        available_pages.update(protected_pages)
        # Remove sign in/up pages for authenticated users
        if "🔐 Sign In" in available_pages:
            del available_pages["🔐 Sign In"]
        if "📝 Sign Up" in available_pages:
            del available_pages["📝 Sign Up"]
        
        # Add logout option in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Welcome, {st.session_state.username}!**")
        if st.sidebar.button("🔓 Sign Out"):
            result = auth.sign_out()
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])
    else:
        # User is not logged in - show only public pages
        available_pages = public_pages

    st.sidebar.title("Navigation")
    
    # Handle page selection via session state or sidebar
    if 'selected_page' in st.session_state and st.session_state.selected_page in available_pages:
        page = st.session_state.selected_page
        # Update radio to match session state
        page_index = list(available_pages.keys()).index(page)
        page = st.sidebar.radio("Go to:", list(available_pages.keys()), index=page_index)
    else:
        page = st.sidebar.radio("Go to:", list(available_pages.keys()))
    
    # Clear selected_page from session state after use
    if 'selected_page' in st.session_state:
        del st.session_state.selected_page
    
    # Execute the selected page function
    if page in protected_pages and not auth.is_authenticated():
        # This shouldn't happen with the current logic, but add as safety check
        st.warning("🔒 Please log in to access this feature.")
        st.info("👈 Use the navigation sidebar to sign in or create an account.")
    else:
        available_pages[page]()
    
except Exception as e:
    st.error(f"Application error: {str(e)}")
    st.code(str(e))
