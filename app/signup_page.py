import streamlit as st
from auth import CognitoAuth
from config import config
import re

def signup_page():
    auth = CognitoAuth()
    
    st.title(f"📝 Create Your {config.APP_NAME} Account")
    
    # Check if user is already authenticated
    if auth.is_authenticated():
        st.success(f"Welcome, {st.session_state.username}! You're already signed in.")
        st.info("Use the sidebar to navigate to your dashboard.")
        return
    
    st.markdown("### Join thousands of researchers and analysts")
    st.markdown(f"Start your **{config.FREE_TRIAL_DAYS}-day free trial** - no credit card required!")
    
    # Sign up form
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*", placeholder="Choose a username")
            email = st.text_input("Email*", placeholder="your@email.com")
        
        with col2:
            password = st.text_input("Password*", type="password", placeholder="Choose a strong password")
            confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Confirm your password")
        
        # Terms and conditions
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy*")
        
        # Newsletter opt-in
        newsletter = st.checkbox("Send me product updates and research tips (optional)")
        
        signup_button = st.form_submit_button("🚀 Create Account", type="primary", use_container_width=True)
        
        if signup_button:
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters long")
            
            if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append("Please enter a valid email address")
            
            if not password or len(password) < 8:
                errors.append("Password must be at least 8 characters long")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if not agree_terms:
                errors.append("You must agree to the Terms of Service and Privacy Policy")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                with st.spinner("Creating your account..."):
                    result = auth.sign_up(username, password, email)
                
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.pending_username = username
                    st.session_state.show_verification_form = True
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Account creation failed: {result['message']}")
    
    # Email verification form
    if st.session_state.get('show_verification_form', False):
        st.markdown("---")
        st.markdown("### 📧 Verify Your Email")
        st.info("We've sent a verification code to your email address. Please check your inbox and enter the code below.")
        
        with st.form("verification_form"):
            verification_code = st.text_input("Verification Code", placeholder="Enter the 6-digit code")
            
            col1, col2 = st.columns(2)
            with col1:
                verify_button = st.form_submit_button("✅ Verify Email", type="primary", use_container_width=True)
            with col2:
                resend_button = st.form_submit_button("📤 Resend Code", use_container_width=True)
            
            if verify_button:
                if verification_code:
                    result = auth.confirm_sign_up(st.session_state.pending_username, verification_code)
                    if result["success"]:
                        st.success(result["message"])
                        st.success("🎉 Account verified! You can now sign in.")
                        st.session_state.show_verification_form = False
                        if 'pending_username' in st.session_state:
                            del st.session_state.pending_username
                        
                        # Auto-redirect to login
                        st.info("🎉 Account verified! Redirecting you to sign in...")
                        st.session_state.selected_page = "🔐 Sign In"
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.error("Please enter the verification code.")
            
            if resend_button:
                st.info("Resending verification code... (This feature needs to be implemented)")
    
    # Sign in link
    st.markdown("---")
    st.markdown("### Already have an account?")
    st.markdown(f"""
    <div style="text-align: center; margin: 1rem 0;">
        <a href="{config.ADMIN_DOMAIN}" target="_blank" style="
            display: inline-block;
            padding: 0.5rem 2rem;
            background-color: #2E8B57;
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: bold;
            transition: background-color 0.3s;
        ">
            🔐 Sign In
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Back to home
    if st.button("🏠 Back to Home", use_container_width=True):
        st.session_state.selected_page = "🏠 Product Overview"
        st.rerun()
    
    # Additional information
    st.markdown("---")
    st.markdown("### What you get with your free trial:")
    trial_benefits = config.get_trial_benefits()
    for benefit in trial_benefits:
        st.markdown(f"- {benefit}")
    
    st.markdown("*Required fields")