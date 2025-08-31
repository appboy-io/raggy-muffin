from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid as uuid_lib
from PIL import Image
import io
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
    company_logo_url: Optional[str]
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
            company_logo_url=profile.company_logo_url,
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
        
        # Get stats (cached for 5 minutes for performance)
        # @cached(key_prefix=f"dashboard_stats_{tenant_id}", ttl=300)
        def get_dashboard_stats():
            doc_count = db.query(Document).filter(Document.tenant_id == tenant_id).count()
            message_count = db.query(ChatMessage).filter(ChatMessage.tenant_id == tenant_id).count()
            return {
                "document_count": doc_count,
                "message_count": message_count,
                "widget_enabled": widget_config.is_enabled,
                "embed_url": f"{config.API_BASE_URL}/api/v1/widgets/{tenant_id}/embed.js",
                "preview_url": f"{config.API_BASE_URL}/api/v1/widgets/{tenant_id}/preview"
            }
        
        stats = get_dashboard_stats()
        
        widget_data = {
            "title": widget_config.widget_title,
            "subtitle": widget_config.widget_subtitle,
            "primary_color": widget_config.primary_color,
            "secondary_color": widget_config.secondary_color,
            "welcome_message": widget_config.welcome_message,
            "placeholder_text": widget_config.placeholder_text,
            "is_enabled": widget_config.is_enabled,
            "allowed_domains": widget_config.allowed_domains,
            "avatar_url": widget_config.avatar_url
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

class AvatarUploadResponse(BaseModel):
    success: bool
    avatar_url: str
    message: str

@router.post("/avatar/upload", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Upload avatar image for chat widget"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG, PNG, and WebP images are allowed"
            )
        
        # Read and validate file size (max 5MB)
        file_content = await file.read()
        file_size = len(file_content)
        max_size = 5 * 1024 * 1024  # 5MB
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        # Process image with PIL
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Validate minimum dimensions
            if image.size[0] < 100 or image.size[1] < 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image must be at least 100x100 pixels"
                )
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to 200x200 for widget display
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Create avatars directory if it doesn't exist
            avatars_dir = "/app/static/avatars"
            os.makedirs(avatars_dir, exist_ok=True)
            
            # Generate filename
            file_extension = "jpg"  # Always save as JPEG for consistency
            filename = f"{tenant_id}.{file_extension}"
            file_path = os.path.join(avatars_dir, filename)
            
            # Save optimized image
            image.save(file_path, "JPEG", quality=85, optimize=True)
            
            # Update widget config with avatar URL
            widget_config = db.query(WidgetConfig).filter(
                WidgetConfig.tenant_id == tenant_id
            ).first()
            
            if not widget_config:
                # Create widget config if it doesn't exist
                widget_config = WidgetConfig(
                    id=uuid_lib.uuid4(),
                    tenant_id=tenant_id
                )
                db.add(widget_config)
            
            # Update avatar URL
            avatar_url = f"/static/avatars/{filename}"
            widget_config.avatar_url = avatar_url
            
            db.commit()
            
            return AvatarUploadResponse(
                success=True,
                avatar_url=avatar_url,
                message="Avatar uploaded successfully"
            )
            
        except Exception as img_error:
            logger.error(f"Image processing error: {img_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file or processing failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )