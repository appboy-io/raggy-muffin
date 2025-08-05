from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.cognito import CognitoAuth
from typing import Dict, Any

security = HTTPBearer()
cognito_auth = CognitoAuth()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        token = credentials.credentials
        result = cognito_auth.verify_token(token)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return result["data"]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_tenant_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Dependency to get current user's tenant ID
    """
    return current_user["tenant_id"]

# Optional authentication for public endpoints
async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Optional authentication - returns None if no valid token
    """
    try:
        if not credentials:
            return None
            
        token = credentials.credentials
        result = cognito_auth.verify_token(token)
        
        if result["success"]:
            return result["data"]
        return None
        
    except Exception:
        return None