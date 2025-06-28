import streamlit as st
from auth import CognitoAuth
from config import config

def login_page():
    auth = CognitoAuth()
    
    st.title(f"🔐 Sign In to {config.APP_NAME}")
    
    # Check if user is already authenticated
    if auth.is_authenticated():
        st.success(f"Welcome back, {st.session_state.username}!")
        st.info("You're already logged in. Use the sidebar to navigate to your dashboard.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 Go to Upload Workflow", use_container_width=True):
                st.session_state.selected_page = "📁 Upload Workflow"
                st.rerun()
        with col2:
            if st.button("🔍 Ask Questions", use_container_width=True):
                st.session_state.selected_page = "🔍 Ask a Question"
                st.rerun()
        
        st.markdown("---")
        if st.button("Sign Out", type="secondary", use_container_width=True):
            result = auth.sign_out()
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])
        return
    
    # Login form
    with st.form("login_form"):
        st.markdown("### Enter your credentials")
        username = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("🚀 Sign In", type="primary", use_container_width=True)
        with col2:
            forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
        
        if login_button:
            if username and password:
                with st.spinner("Signing you in..."):
                    result = auth.sign_in(username, password)
                
                if result["success"]:
                    st.success(result["message"])
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Login failed: {result['message']}")
            else:
                st.error("Please enter both username and password.")
        
        if forgot_password:
            if username:
                result = auth.forgot_password(username)
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.show_reset_form = True
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.error("Please enter your username first.")
    
    # Password reset form
    if st.session_state.get('show_reset_form', False):
        st.markdown("---")
        st.markdown("### Reset Your Password")
        
        with st.form("reset_form"):
            reset_username = st.text_input("Username", value=username if 'username' in locals() else "", disabled=True)
            verification_code = st.text_input("Verification Code", placeholder="Enter the code from your email")
            new_password = st.text_input("New Password", type="password", placeholder="Enter your new password")
            
            if st.form_submit_button("Reset Password", type="primary", use_container_width=True):
                if verification_code and new_password:
                    result = auth.confirm_forgot_password(reset_username, verification_code, new_password)
                    if result["success"]:
                        st.success(result["message"])
                        st.session_state.show_reset_form = False
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.error("Please enter both verification code and new password.")
    
    # Sign up link
    st.markdown("---")
    st.markdown("### Don't have an account?")
    if st.button("📝 Create Account", use_container_width=True):
        st.session_state.selected_page = "📝 Sign Up"
        st.rerun()
    
    # Back to home
    if st.button("🏠 Back to Home", use_container_width=True):
        st.session_state.selected_page = "🏠 Product Overview"
        st.rerun()