from pycognito import Cognito
from pycognito.exceptions import SoftwareTokenMFAChallengeException, SMSMFAChallengeException
import hashlib
import hmac
import base64
from app.config import config
from typing import Dict, Any, Optional

class CognitoAuth:
    """AWS Cognito authentication service"""
    
    def __init__(self):
        self.user_pool_id = config.AWS_COGNITO_USER_POOL_ID
        self.client_id = config.AWS_COGNITO_CLIENT_ID
        self.client_secret = config.AWS_COGNITO_CLIENT_SECRET
        self.region = config.AWS_REGION
        
        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("AWS Cognito configuration missing")
    
    def _calculate_secret_hash(self, username: str) -> Optional[str]:
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
    
    def sign_up(self, username: str, password: str, email: str) -> Dict[str, Any]:
        """Register a new user"""
        try:
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=username,
                user_pool_region=self.region
            )
            
            cognito.set_base_attributes(email=email)
            result = cognito.register(
                username=username,
                password=password,
                attr_map={'email': email}
            )
            
            return {
                "success": True, 
                "message": "Registration successful! Please check your email for verification.",
                "data": result
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def confirm_sign_up(self, username: str, confirmation_code: str) -> Dict[str, Any]:
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
    
    def sign_in(self, username: str, password: str) -> Dict[str, Any]:
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
            
            # Get user info for tenant ID
            user_info = cognito.get_user()
            user_id = self._extract_user_id(user_info)
            
            return {
                "success": True,
                "message": "Login successful!",
                "data": {
                    "access_token": cognito.access_token,
                    "id_token": cognito.id_token,
                    "refresh_token": cognito.refresh_token,
                    "user_id": user_id,
                    "tenant_id": user_id,
                    "username": username
                }
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _extract_user_id(self, user_info) -> str:
        """Extract user ID from Cognito user info"""
        print(f"DEBUG: _extract_user_id called with: {user_info}, type: {type(user_info)}")
        
        if user_info is None:
            print("DEBUG: user_info is None")
            return None
            
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
            return user_id
        
        # Handle UserObj case
        if hasattr(user_info, '__dict__'):
            print(f"DEBUG: UserObj attributes: {user_info.__dict__}")
            return getattr(user_info, 'sub', None) or getattr(user_info, 'username', None)
        
        return None
    
    def verify_token(self, access_token: str) -> Dict[str, Any]:
        """Verify and decode access token"""
        try:
            print(f"DEBUG: Verifying token: {access_token[:20]}...")
            cognito = Cognito(
                user_pool_id=self.user_pool_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_pool_region=self.region,
                access_token=access_token
            )
            
            user_info = cognito.get_user()
            print(f"DEBUG: User info retrieved: {user_info}")
            user_id = self._extract_user_id(user_info)
            
            # Extract username properly
            username = None
            if isinstance(user_info, dict):
                username = user_info.get('username')
            elif hasattr(user_info, 'username'):
                username = getattr(user_info, 'username', None)
                # Try _metadata as fallback
                if not username and hasattr(user_info, '_metadata'):
                    username = user_info._metadata.get('username')
            
            return {
                "success": True,
                "message": "Token verified successfully",
                "data": {
                    "user_id": user_id,
                    "tenant_id": user_id,
                    "username": username
                }
            }
            
        except Exception as e:
            print(f"DEBUG: Token verification error: {e}")
            return {"success": False, "message": str(e)}
    
    def forgot_password(self, username: str) -> Dict[str, Any]:
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
    
    def confirm_forgot_password(self, username: str, confirmation_code: str, new_password: str) -> Dict[str, Any]:
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