from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import bcrypt
import jwt
import hashlib
import secrets
from app.database import get_db
from app.models import (
    SuperAdmin, SuperAdminSession, SuperAdminAuditLog, 
    SystemConfig, CustomerProfile, Document, ChatMessage
)
from app.config import config as settings

router = APIRouter(prefix="/api/superadmin", tags=["superadmin"])
security = HTTPBearer(auto_error=False)

# JWT Configuration
SUPERADMIN_SECRET_KEY = settings.SECRET_KEY + "_superadmin"  # Different from tenant JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# =====================================================
# Pydantic Models
# =====================================================

class SetupStatusResponse(BaseModel):
    setup_required: bool
    system_ready: bool
    message: str

class SuperAdminSetup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    
class SuperAdminLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class CustomerListResponse(BaseModel):
    customers: List[Dict[str, Any]]
    total: int
    page: int
    limit: int

# =====================================================
# Helper Functions
# =====================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict) -> str:
    """Create a JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SUPERADMIN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def hash_token(token: str) -> str:
    """Hash a token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

async def get_current_superadmin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuperAdmin:
    """Verify and get current superadmin from token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SUPERADMIN_SECRET_KEY, algorithms=[ALGORITHM])
        superadmin_id = payload.get("sub")
        if not superadmin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Verify session exists and is valid
    token_hash = hash_token(token)
    result = db.execute(
        select(SuperAdminSession)
        .where(SuperAdminSession.token_hash == token_hash)
        .where(SuperAdminSession.expires_at > datetime.utcnow())
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    # Get superadmin
    result = db.execute(
        select(SuperAdmin)
        .where(SuperAdmin.id == superadmin_id)
        .where(SuperAdmin.is_active == True)
    )
    superadmin = result.scalar_one_or_none()
    
    if not superadmin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Superadmin not found or inactive"
        )
    
    return superadmin

def log_audit(
    db: Session,
    superadmin_id: Optional[str],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None
):
    """Log superadmin action to audit log"""
    audit_log = SuperAdminAuditLog(
        superadmin_id=superadmin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
        details=details or {},
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()

# =====================================================
# Setup Endpoints (Public - No Auth Required)
# =====================================================

@router.get("/setup/status", response_model=SetupStatusResponse)
async def check_setup_status(db: Session = Depends(get_db)):
    """Check if initial setup is required"""
    # Check if any superadmin exists
    result = db.execute(
        select(func.count(SuperAdmin.id))
    )
    superadmin_count = result.scalar()
    
    # Check system config
    result = db.execute(
        select(SystemConfig)
        .where(SystemConfig.key == "setup_complete")
    )
    setup_config = result.scalar_one_or_none()
    
    setup_required = superadmin_count == 0
    
    return SetupStatusResponse(
        setup_required=setup_required,
        system_ready=not setup_required,
        message="Initial setup required" if setup_required else "System ready"
    )

@router.post("/setup/initialize", response_model=TokenResponse)
async def initialize_superadmin(
    data: SuperAdminSetup,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create the first superadmin account - only works if none exist"""
    # Check if any superadmin already exists
    result = db.execute(
        select(func.count(SuperAdmin.id))
    )
    if result.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup already completed"
        )
    
    # Check if username or email already exists (shouldn't happen but safety check)
    result = db.execute(
        select(SuperAdmin)
        .where(
            (SuperAdmin.username == data.username) |
            (SuperAdmin.email == data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create the first superadmin
    superadmin = SuperAdmin(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        is_active=True,
        is_primary=True  # Mark as primary superadmin
    )
    db.add(superadmin)
    
    # Update system config
    result = db.execute(
        select(SystemConfig)
        .where(SystemConfig.key == "setup_complete")
    )
    setup_config = result.scalar_one_or_none()
    if setup_config:
        setup_config.value = True
        setup_config.updated_at = datetime.utcnow()
    else:
        setup_config = SystemConfig(
            key="setup_complete",
            value=True,
            description="Initial setup completed"
        )
        db.add(setup_config)
    
    db.commit()
    db.refresh(superadmin)
    
    # Create session and token
    access_token = create_access_token({"sub": str(superadmin.id)})
    token_hash = hash_token(access_token)
    
    session = SuperAdminSession(
        superadmin_id=superadmin.id,
        token_hash=token_hash,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    db.add(session)
    
    # Log the setup completion
    log_audit(
        db=db,
        superadmin_id=str(superadmin.id),
        action="system.setup",
        details={"username": data.username, "email": data.email},
        ip_address=request.client.host
    )
    
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user={
            "id": str(superadmin.id),
            "username": superadmin.username,
            "email": superadmin.email,
            "full_name": superadmin.full_name,
            "is_primary": superadmin.is_primary
        }
    )

# =====================================================
# Authentication Endpoints
# =====================================================

@router.post("/auth/login", response_model=TokenResponse)
async def superadmin_login(
    data: SuperAdminLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Superadmin login"""
    # Find superadmin by username
    result = db.execute(
        select(SuperAdmin)
        .where(SuperAdmin.username == data.username)
    )
    superadmin = result.scalar_one_or_none()
    
    if not superadmin:
        # Log failed attempt
        log_audit(
            db=db,
            superadmin_id=None,
            action="auth.login_failed",
            details={"username": data.username, "reason": "user_not_found"},
            ip_address=request.client.host
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is locked
    if superadmin.locked_until and superadmin.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account locked until {superadmin.locked_until}"
        )
    
    # Verify password
    if not verify_password(data.password, superadmin.password_hash):
        # Increment failed attempts
        superadmin.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if superadmin.failed_login_attempts >= 5:
            superadmin.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        db.commit()
        
        # Log failed attempt
        log_audit(
            db=db,
            superadmin_id=str(superadmin.id),
            action="auth.login_failed",
            details={"reason": "invalid_password", "attempts": superadmin.failed_login_attempts},
            ip_address=request.client.host
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is active
    if not superadmin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated"
        )
    
    # Reset failed attempts and update last login
    superadmin.failed_login_attempts = 0
    superadmin.locked_until = None
    superadmin.last_login = datetime.utcnow()
    
    # Create session and token
    access_token = create_access_token({"sub": str(superadmin.id)})
    token_hash = hash_token(access_token)
    
    session = SuperAdminSession(
        superadmin_id=superadmin.id,
        token_hash=token_hash,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    db.add(session)
    
    # Log successful login
    log_audit(
        db=db,
        superadmin_id=str(superadmin.id),
        action="auth.login",
        ip_address=request.client.host
    )
    
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user={
            "id": str(superadmin.id),
            "username": superadmin.username,
            "email": superadmin.email,
            "full_name": superadmin.full_name,
            "is_primary": superadmin.is_primary
        }
    )

@router.post("/auth/logout")
async def superadmin_logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Superadmin logout"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    token_hash = hash_token(token)
    
    # Delete the session
    result = db.execute(
        select(SuperAdminSession)
        .where(SuperAdminSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    
    if session:
        db.delete(session)
        
        # Log logout
        log_audit(
            db=db,
            superadmin_id=str(session.superadmin_id),
            action="auth.logout",
            ip_address=request.client.host
        )
        
        db.commit()
    
    return {"message": "Logged out successfully"}

@router.get("/auth/verify")
async def verify_token(
    superadmin: SuperAdmin = Depends(get_current_superadmin)
):
    """Verify if the current token is valid"""
    return {
        "valid": True,
        "user": {
            "id": str(superadmin.id),
            "username": superadmin.username,
            "email": superadmin.email,
            "full_name": superadmin.full_name,
            "is_primary": superadmin.is_primary
        }
    }

# =====================================================
# Customer Management Endpoints (Auth Required)
# =====================================================

@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    request: Request = None,
    superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """List all customer accounts"""
    # Build query
    query = select(CustomerProfile)
    
    # Apply filters
    if search:
        query = query.where(
            (CustomerProfile.company_name.ilike(f"%{search}%")) |
            (CustomerProfile.contact_email.ilike(f"%{search}%")) |
            (CustomerProfile.tenant_id.ilike(f"%{search}%"))
        )
    
    if status == "active":
        query = query.where(CustomerProfile.is_active == True)
    elif status == "inactive":
        query = query.where(CustomerProfile.is_active == False)
    elif status == "pending":
        query = query.where(CustomerProfile.onboarding_completed == False)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    query = query.order_by(CustomerProfile.created_at.desc())
    
    # Execute query
    result = db.execute(query)
    customers = result.scalars().all()
    
    # Get additional stats for each customer
    customer_list = []
    for customer in customers:
        # Get document count
        doc_result = db.execute(
            select(func.count(Document.id))
            .where(Document.tenant_id == customer.tenant_id)
        )
        doc_count = doc_result.scalar()
        
        # Get chat message count (this month)
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        msg_result = db.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.tenant_id == customer.tenant_id)
            .where(ChatMessage.created_at >= month_start)
        )
        msg_count = msg_result.scalar()
        
        customer_list.append({
            "id": str(customer.id),
            "tenant_id": customer.tenant_id,
            "company_name": customer.company_name,
            "company_website": customer.company_website,
            "contact_email": customer.contact_email,
            "contact_name": customer.contact_name,
            "industry": customer.industry,
            "subscription_plan": customer.subscription_plan,
            "is_active": customer.is_active,
            "onboarding_completed": customer.onboarding_completed,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "documents_count": doc_count,
            "queries_this_month": msg_count
        })
    
    # Log access
    log_audit(
        db=db,
        superadmin_id=str(superadmin.id),
        action="customer.list",
        details={"page": page, "search": search, "status": status},
        ip_address=request.client.host if request else None
    )
    
    return CustomerListResponse(
        customers=customer_list,
        total=total,
        page=page,
        limit=limit
    )

@router.get("/customers/{tenant_id}")
async def get_customer_details(
    tenant_id: str,
    request: Request = None,
    superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific customer"""
    # Get customer profile
    result = db.execute(
        select(CustomerProfile)
        .where(CustomerProfile.tenant_id == tenant_id)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Get additional statistics
    doc_result = db.execute(
        select(func.count(Document.id))
        .where(Document.tenant_id == tenant_id)
    )
    doc_count = doc_result.scalar()
    
    # Get chat statistics
    msg_result = db.execute(
        select(func.count(ChatMessage.id))
        .where(ChatMessage.tenant_id == tenant_id)
    )
    total_messages = msg_result.scalar()
    
    # Log access
    log_audit(
        db=db,
        superadmin_id=str(superadmin.id),
        action="customer.view",
        entity_type="customer",
        entity_id=str(customer.id),
        tenant_id=tenant_id,
        ip_address=request.client.host if request else None
    )
    
    return {
        "id": str(customer.id),
        "tenant_id": customer.tenant_id,
        "company_name": customer.company_name,
        "company_website": customer.company_website,
        "contact_email": customer.contact_email,
        "contact_name": customer.contact_name,
        "industry": customer.industry,
        "subscription_plan": customer.subscription_plan,
        "is_active": customer.is_active,
        "onboarding_completed": customer.onboarding_completed,
        "allowed_domains": customer.allowed_domains,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "statistics": {
            "documents_count": doc_count,
            "total_messages": total_messages
        }
    }

@router.post("/customers/{tenant_id}/suspend")
async def suspend_customer(
    tenant_id: str,
    request: Request = None,
    superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """Suspend a customer account"""
    result = db.execute(
        select(CustomerProfile)
        .where(CustomerProfile.tenant_id == tenant_id)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.is_active = False
    
    # Log action
    log_audit(
        db=db,
        superadmin_id=str(superadmin.id),
        action="customer.suspend",
        entity_type="customer",
        entity_id=str(customer.id),
        tenant_id=tenant_id,
        details={"company_name": customer.company_name},
        ip_address=request.client.host if request else None
    )
    
    db.commit()
    
    return {"message": "Customer suspended successfully"}

@router.post("/customers/{tenant_id}/activate")
async def activate_customer(
    tenant_id: str,
    request: Request = None,
    superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """Activate a suspended customer account"""
    result = db.execute(
        select(CustomerProfile)
        .where(CustomerProfile.tenant_id == tenant_id)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.is_active = True
    
    # Log action
    log_audit(
        db=db,
        superadmin_id=str(superadmin.id),
        action="customer.activate",
        entity_type="customer",
        entity_id=str(customer.id),
        tenant_id=tenant_id,
        details={"company_name": customer.company_name},
        ip_address=request.client.host if request else None
    )
    
    db.commit()
    
    return {"message": "Customer activated successfully"}