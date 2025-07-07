from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
from app.auth.cognito import CognitoAuth
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])
cognito_auth = CognitoAuth()

class SignUpRequest(BaseModel):
    username: str
    password: str
    email: EmailStr

class SignInRequest(BaseModel):
    username: str
    password: str

class ConfirmSignUpRequest(BaseModel):
    username: str
    confirmation_code: str

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    username: str
    confirmation_code: str
    new_password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

@router.post("/signup", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """Register a new user"""
    result = cognito_auth.sign_up(
        username=request.username,
        password=request.password,
        email=request.email
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return AuthResponse(**result)

@router.post("/confirm-signup", response_model=AuthResponse)
async def confirm_sign_up(request: ConfirmSignUpRequest):
    """Confirm user registration with verification code"""
    result = cognito_auth.confirm_sign_up(
        username=request.username,
        confirmation_code=request.confirmation_code
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return AuthResponse(**result)

@router.post("/signin", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """Authenticate user and return tokens"""
    result = cognito_auth.sign_in(
        username=request.username,
        password=request.password
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return AuthResponse(**result)

@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate password reset"""
    result = cognito_auth.forgot_password(username=request.username)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return AuthResponse(**result)

@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(request: ResetPasswordRequest):
    """Complete password reset"""
    result = cognito_auth.confirm_forgot_password(
        username=request.username,
        confirmation_code=request.confirmation_code,
        new_password=request.new_password
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return AuthResponse(**result)

@router.get("/verify", response_model=AuthResponse)
async def verify_token(authorization: str = Header(None)):
    """Verify access token"""
    
    print(f"DEBUG: Authorization header: {authorization}")
    
    # Get token from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        print(f"DEBUG: Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    print(f"DEBUG: Extracted token: {access_token[:20]}...")
    
    result = cognito_auth.verify_token(access_token)
    print(f"DEBUG: Verify result: {result}")
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return AuthResponse(**result)