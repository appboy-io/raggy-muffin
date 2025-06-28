import streamlit as st
import boto3
import os
from pycognito import Cognito
from pycognito.exceptions import SoftwareTokenMFAChallengeException, SMSMFAChallengeException
import hashlib
import hmac
import base64
from config import config

class CognitoAuth:
    def __init__(self):
        self.user_pool_id = config.AWS_COGNITO_USER_POOL_ID
        self.client_id = config.AWS_COGNITO_CLIENT_ID
        self.client_secret = config.AWS_COGNITO_CLIENT_SECRET
        self.region = config.AWS_REGION
        
        if not all([self.user_pool_id, self.client_id]):
            st.error("AWS Cognito configuration missing. Please set environment variables.")
            st.stop()
    
    def _calculate_secret_hash(self, username):
        """Calculate the secret hash for Cognito client"""
        if not self.client_secret:
            return None
        
        message = username + self.client_id
        dig = hmac.new(
            str(self.client_secret).encode('utf-8'),
            msg=str(message).encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def sign_up(self, username, password, email):
        """Register a new user"""
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            result = cognito.register(
                username=username,
                password=password,
                email=email
            )
            
            return {"success": True, "message": "Registration successful! Please check your email for verification."}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def confirm_sign_up(self, username, confirmation_code):
        """Confirm user registration with verification code"""
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            cognito.confirm_sign_up(confirmation_code)
            return {"success": True, "message": "Email verified successfully!"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def sign_in(self, username, password):
        """Authenticate user"""
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            cognito.authenticate(password=password)
            
            # Store authentication state
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.access_token = cognito.access_token
            st.session_state.id_token = cognito.id_token
            st.session_state.refresh_token = cognito.refresh_token
            
            return {"success": True, "message": "Login successful!", "user": cognito}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def sign_out(self):
        """Sign out user and clear session"""
        try:
            if 'access_token' in st.session_state:
                cognito = Cognito(
                    user_pool_id=self.user_pool_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_pool_region=self.region,
                    access_token=st.session_state.access_token
                )
                cognito.logout()
            
            # Clear session state
            keys_to_clear = ['authenticated', 'username', 'access_token', 'id_token', 'refresh_token']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            return {"success": True, "message": "Logged out successfully!"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_user_info(self):
        """Get current user information"""
        if not self.is_authenticated():
            return None
        
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_pool_region=self.region,
                access_token=st.session_state.access_token
            )
            
            return cognito.get_user()
            
        except Exception as e:
            st.error(f"Error getting user info: {e}")
            return None
    
    def forgot_password(self, username):
        """Initiate password reset"""
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            cognito.initiate_forgot_password()
            return {"success": True, "message": "Password reset code sent to your email!"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def confirm_forgot_password(self, username, confirmation_code, new_password):
        """Complete password reset"""
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            cognito.confirm_forgot_password(confirmation_code, new_password)
            return {"success": True, "message": "Password reset successful!"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}

def require_auth():
    """Decorator function to require authentication for pages"""
    auth = CognitoAuth()
    if not auth.is_authenticated():
        st.warning("🔒 Please log in to access this feature.")
        st.info("👈 Use the navigation sidebar to go to login or create an account.")
        st.stop()
    return True