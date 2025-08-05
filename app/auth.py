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
            print(f"DEBUG: Attempting signup for user: {username}, email: {email}")
            print(f"DEBUG: Using pool: {self.user_pool_id}, client: {self.client_id}")
            
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,  # Use the actual username
                user_pool_region=self.region
            )
            
            # Register with username but set email attribute
            cognito.set_base_attributes(email=email)
            result = cognito.register(
                username=username,
                password=password,
                attr_map={
                    'email': email
                }
            )
            
            print(f"DEBUG: Registration result: {result}")
            return {"success": True, "message": "Registration successful! Please check your email for verification."}
            
        except Exception as e:
            print(f"DEBUG: Registration error: {str(e)}")
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
            print(f"DEBUG: Attempting login for user: {username}")
            print(f"DEBUG: Using pool: {self.user_pool_id}, client: {self.client_id}")
            
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            print(f"DEBUG: About to authenticate...")
            cognito.authenticate(password=password)
            print(f"DEBUG: Authentication successful")
            
            # Get user ID from Cognito token to use as tenant ID
            try:
                user_info = cognito.get_user()
                print(f"DEBUG: User info: {user_info}")
                
                # Extract user ID - try different possible locations
                user_id = None
                if isinstance(user_info, dict):
                    # Try direct access first
                    user_id = user_info.get('sub') or user_info.get('username')
                    
                    # Try UserAttributes if it exists
                    if not user_id and 'UserAttributes' in user_info:
                        for attr in user_info['UserAttributes']:
                            if attr.get('Name') == 'sub':
                                user_id = attr.get('Value')
                                break
                
                print(f"DEBUG: Extracted user_id: {user_id}")
                
                # Fallback to username if no user_id found
                if not user_id:
                    user_id = username
                    print(f"DEBUG: Using username as fallback user_id: {user_id}")
                
            except Exception as e:
                print(f"DEBUG: Error getting user info: {e}")
                user_id = username  # Fallback to username
            
            # Store authentication state
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_id = user_id
            st.session_state.tenant_id = user_id  # Use Cognito user ID as tenant ID
            st.session_state.access_token = cognito.access_token
            st.session_state.id_token = cognito.id_token
            st.session_state.refresh_token = cognito.refresh_token
            
            print(f"DEBUG: Session state set - authenticated: {st.session_state.authenticated}, tenant_id: {st.session_state.tenant_id}")
            
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
            keys_to_clear = ['authenticated', 'username', 'user_id', 'tenant_id', 'access_token', 'id_token', 'refresh_token']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            return {"success": True, "message": "Logged out successfully!"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        is_auth = st.session_state.get('authenticated', False)
        print(f"DEBUG: is_authenticated() called - result: {is_auth}")
        print(f"DEBUG: Session state keys: {list(st.session_state.keys())}")
        return is_auth
    
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
    
    def get_tenant_id(self):
        """Get the current user's tenant ID (Cognito user ID)"""
        return st.session_state.get('tenant_id', None)
    
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