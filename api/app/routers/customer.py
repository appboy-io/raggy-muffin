from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_tenant_id
from app.models import CustomerProfile, Document, ChatMessage, WidgetConfig
from app.config import config
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customer", tags=["customer"])

class CustomerProfileRequest(BaseModel):
    company_name: str
    company_website: Optional[str] = None
    contact_email: EmailStr
    contact_name: Optional[str] = None
    industry: Optional[str] = None
    allowed_domains: Optional[List[str]] = []

class CustomerProfileResponse(BaseModel):
    tenant_id: str
    company_name: str
    company_website: Optional[str]
    contact_email: str
    contact_name: Optional[str]
    industry: Optional[str]
    allowed_domains: List[str]
    subscription_plan: str
    is_active: bool
    onboarding_completed: bool
    created_at: str

class CustomerDashboardResponse(BaseModel):
    profile: CustomerProfileResponse
    stats: dict
    widget_config: dict

@router.get("/profile", response_model=CustomerProfileResponse)
async def get_customer_profile(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get customer profile information"""
    try:
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.tenant_id == tenant_id
        ).first()
        
        if not profile:
            # Create default profile if it doesn't exist
            profile = CustomerProfile(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                company_name="Your Company",
                contact_email="admin@company.com",
                allowed_domains=["*"]
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        return CustomerProfileResponse(
            tenant_id=profile.tenant_id,
            company_name=profile.company_name,
            company_website=profile.company_website,
            contact_email=profile.contact_email,
            contact_name=profile.contact_name,
            industry=profile.industry,
            allowed_domains=profile.allowed_domains or ["*"],
            subscription_plan=profile.subscription_plan,
            is_active=profile.is_active,
            onboarding_completed=profile.onboarding_completed,
            created_at=profile.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting customer profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer profile"
        )

@router.put("/profile", response_model=CustomerProfileResponse)
async def update_customer_profile(
    request: CustomerProfileRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Update customer profile information"""
    try:
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.tenant_id == tenant_id
        ).first()
        
        if not profile:
            # Create new profile
            profile = CustomerProfile(
                id=uuid.uuid4(),
                tenant_id=tenant_id
            )
            db.add(profile)
        
        # Update fields
        profile.company_name = request.company_name
        profile.company_website = request.company_website
        profile.contact_email = request.contact_email
        profile.contact_name = request.contact_name
        profile.industry = request.industry
        profile.allowed_domains = request.allowed_domains or ["*"]
        profile.onboarding_completed = True
        
        db.commit()
        db.refresh(profile)
        
        return CustomerProfileResponse(
            tenant_id=profile.tenant_id,
            company_name=profile.company_name,
            company_website=profile.company_website,
            contact_email=profile.contact_email,
            contact_name=profile.contact_name,
            industry=profile.industry,
            allowed_domains=profile.allowed_domains,
            subscription_plan=profile.subscription_plan,
            is_active=profile.is_active,
            onboarding_completed=profile.onboarding_completed,
            created_at=profile.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error updating customer profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer profile"
        )

@router.get("/dashboard", response_model=CustomerDashboardResponse)
async def get_customer_dashboard(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get complete customer dashboard data"""
    try:
        # Get or create profile
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.tenant_id == tenant_id
        ).first()
        
        if not profile:
            profile = CustomerProfile(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                company_name="Your Company",
                contact_email="admin@company.com",
                allowed_domains=["*"]
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Get widget config
        widget_config = db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id
        ).first()
        
        if not widget_config:
            widget_config = WidgetConfig(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                widget_title=f"{profile.company_name} Assistant",
                welcome_message=f"Hello! I'm the {profile.company_name} assistant. How can I help you today?"
            )
            db.add(widget_config)
            db.commit()
            db.refresh(widget_config)
        
        # Get stats
        doc_count = db.query(Document).filter(Document.tenant_id == tenant_id).count()
        message_count = db.query(ChatMessage).filter(ChatMessage.tenant_id == tenant_id).count()
        
        stats = {
            "document_count": doc_count,
            "message_count": message_count,
            "widget_enabled": widget_config.is_enabled,
            "embed_url": f"{config.API_BASE_URL}/api/v1/widgets/{tenant_id}/embed.js",
            "preview_url": f"{config.API_BASE_URL}/api/v1/widgets/{tenant_id}/preview"
        }
        
        widget_data = {
            "title": widget_config.widget_title,
            "subtitle": widget_config.widget_subtitle,
            "primary_color": widget_config.primary_color,
            "secondary_color": widget_config.secondary_color,
            "welcome_message": widget_config.welcome_message,
            "placeholder_text": widget_config.placeholder_text,
            "is_enabled": widget_config.is_enabled,
            "allowed_domains": widget_config.allowed_domains
        }
        
        return CustomerDashboardResponse(
            profile=CustomerProfileResponse(
                tenant_id=profile.tenant_id,
                company_name=profile.company_name,
                company_website=profile.company_website,
                contact_email=profile.contact_email,
                contact_name=profile.contact_name,
                industry=profile.industry,
                allowed_domains=profile.allowed_domains,
                subscription_plan=profile.subscription_plan,
                is_active=profile.is_active,
                onboarding_completed=profile.onboarding_completed,
                created_at=profile.created_at.isoformat()
            ),
            stats=stats,
            widget_config=widget_data
        )
        
    except Exception as e:
        logger.error(f"Error getting customer dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer dashboard"
        )