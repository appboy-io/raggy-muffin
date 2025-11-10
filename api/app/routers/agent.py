from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, validator
from app.database import get_db
from app.models import AgentConfig
from app.auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for requests/responses
class AgentConfigRequest(BaseModel):
    agent_name: str
    agent_role: str
    personality_traits: List[str]
    greeting_message: str
    custom_instructions: Optional[str] = None
    response_style: str = "conversational"
    industry: str = "general"
    system_prompt: Optional[str] = None
    
    @validator('agent_name')
    def validate_agent_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Agent name cannot be empty')
        if len(v) > 50:
            raise ValueError('Agent name must be 50 characters or less')
        return v.strip()
    
    @validator('personality_traits')
    def validate_personality_traits(cls, v):
        allowed_traits = [
            'friendly', 'professional', 'empathetic', 'enthusiastic',
            'technical', 'formal', 'casual', 'patient', 'direct',
            'creative', 'analytical', 'supportive', 'energetic', 'calm'
        ]
        if not isinstance(v, list):
            raise ValueError('Personality traits must be a list')
        for trait in v:
            if trait not in allowed_traits:
                raise ValueError(f'Invalid personality trait: {trait}')
        if len(v) > 5:
            raise ValueError('Maximum 5 personality traits allowed')
        return v
    
    @validator('response_style')
    def validate_response_style(cls, v):
        allowed_styles = ['conversational', 'professional', 'technical', 'casual', 'formal']
        if v not in allowed_styles:
            raise ValueError(f'Response style must be one of: {", ".join(allowed_styles)}')
        return v
    
    @validator('greeting_message')
    def validate_greeting_message(cls, v):
        if len(v) > 500:
            raise ValueError('Greeting message must be 500 characters or less')
        return v
    
    @validator('system_prompt')
    def validate_system_prompt(cls, v):
        if v and len(v) > 5000:
            raise ValueError('System prompt must be 5000 characters or less')
        
        # Basic content validation for system prompts
        if v:
            # Check for potentially problematic instructions
            problematic_patterns = [
                'ignore previous instructions',
                'ignore your instructions',
                'forget your role',
                'pretend to be',
                'roleplay as',
                'act as if you are not',
                'don\'t follow',
                'bypass',
                'jailbreak'
            ]
            
            v_lower = v.lower()
            for pattern in problematic_patterns:
                if pattern in v_lower:
                    raise ValueError(f'System prompt contains potentially problematic instruction: "{pattern}"')
            
            # Ensure reasonable content length for readability
            if v.strip() and len(v.strip()) < 10:
                raise ValueError('System prompt is too short to be meaningful')
        
        return v
    
    @validator('custom_instructions')
    def validate_custom_instructions(cls, v):
        if v and len(v) > 2000:
            raise ValueError('Custom instructions must be 2000 characters or less')
        return v
    
    @validator('agent_role')
    def validate_agent_role(cls, v):
        if v and len(v) > 100:
            raise ValueError('Agent role must be 100 characters or less')
        if v and len(v.strip()) < 3:
            raise ValueError('Agent role must be at least 3 characters')
        return v

class AgentConfigResponse(BaseModel):
    tenant_id: str
    agent_name: str
    agent_role: str
    personality_traits: List[str]
    greeting_message: str
    custom_instructions: Optional[str]
    response_style: str
    industry: str
    system_prompt: Optional[str]
    is_active: bool

class PromptPreviewRequest(BaseModel):
    agent_name: str
    agent_role: str
    personality_traits: List[str]
    custom_instructions: Optional[str] = None
    response_style: str = "conversational"
    industry: str = "general"

@router.get("/agent/config", response_model=AgentConfigResponse)
async def get_agent_config(
    auth_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the agent configuration for the authenticated tenant"""
    try:
        tenant_id = auth_data["tenant_id"]
        
        config = db.query(AgentConfig).filter(
            AgentConfig.tenant_id == tenant_id
        ).first()
        
        if not config:
            # Create default config if none exists
            config = AgentConfig(
                tenant_id=tenant_id,
                agent_name="Assistant",
                agent_role="helpful assistant",
                personality_traits=["friendly", "professional"],
                greeting_message="Hello! How can I help you today?",
                response_style="conversational",
                industry="general"
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return AgentConfigResponse(
            tenant_id=config.tenant_id,
            agent_name=config.agent_name,
            agent_role=config.agent_role,
            personality_traits=config.personality_traits,
            greeting_message=config.greeting_message,
            custom_instructions=config.custom_instructions,
            response_style=config.response_style,
            industry=config.industry,
            system_prompt=config.system_prompt,
            is_active=config.is_active
        )
        
    except Exception as e:
        logger.error(f"Error getting agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving agent configuration"
        )

@router.put("/agent/config", response_model=AgentConfigResponse)
async def update_agent_config(
    config_data: AgentConfigRequest,
    auth_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the agent configuration for the authenticated tenant"""
    try:
        tenant_id = auth_data["tenant_id"]
        
        config = db.query(AgentConfig).filter(
            AgentConfig.tenant_id == tenant_id
        ).first()
        
        if not config:
            # Create new config
            config = AgentConfig(tenant_id=tenant_id)
            db.add(config)
        
        # Update fields
        config.agent_name = config_data.agent_name
        config.agent_role = config_data.agent_role
        config.personality_traits = config_data.personality_traits
        config.greeting_message = config_data.greeting_message
        config.custom_instructions = config_data.custom_instructions
        config.response_style = config_data.response_style
        config.industry = config_data.industry
        config.system_prompt = config_data.system_prompt
        
        db.commit()
        db.refresh(config)
        
        logger.info(f"Updated agent config for tenant {tenant_id}")
        
        return AgentConfigResponse(
            tenant_id=config.tenant_id,
            agent_name=config.agent_name,
            agent_role=config.agent_role,
            personality_traits=config.personality_traits,
            greeting_message=config.greeting_message,
            custom_instructions=config.custom_instructions,
            response_style=config.response_style,
            industry=config.industry,
            system_prompt=config.system_prompt,
            is_active=config.is_active
        )
        
    except Exception as e:
        logger.error(f"Error updating agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating agent configuration"
        )

@router.post("/agent/preview-prompt")
async def preview_generated_prompt(
    preview_data: PromptPreviewRequest,
    auth_data: dict = Depends(get_current_user)
):
    """Generate a preview of the system prompt based on current settings"""
    try:
        # Generate prompt preview based on settings
        prompt_parts = []
        
        # Basic personality setup
        prompt_parts.append(f"You are {preview_data.agent_name}, a {preview_data.agent_role}.")
        
        # Add personality traits
        if preview_data.personality_traits:
            traits_text = ", ".join(preview_data.personality_traits)
            prompt_parts.append(f"\nYour personality traits: {traits_text}")
        
        # Add industry context
        if preview_data.industry != "general":
            prompt_parts.append(f"\nYou specialize in {preview_data.industry} and have deep knowledge in this field.")
        
        # Add response style guidance
        style_guidance = {
            "conversational": "Respond in a friendly, conversational tone.",
            "professional": "Maintain a professional and formal tone.",
            "technical": "Use technical language and be precise in your explanations.",
            "casual": "Keep your responses casual and relaxed.",
            "formal": "Use formal language and structure in your responses."
        }
        
        if preview_data.response_style in style_guidance:
            prompt_parts.append(f"\nCommunication style: {style_guidance[preview_data.response_style]}")
        
        # Add custom instructions
        if preview_data.custom_instructions:
            prompt_parts.append(f"\nAdditional guidelines: {preview_data.custom_instructions}")
        
        # Add general guidelines
        prompt_parts.append("""
\nGeneral guidelines:
- Be helpful and informative
- Provide accurate information
- If you don't know something, say so
- Ask clarifying questions when needed
- Keep responses focused and relevant""")
        
        generated_prompt = "".join(prompt_parts)
        
        return {
            "preview": generated_prompt,
            "character_count": len(generated_prompt),
            "estimated_tokens": len(generated_prompt.split()) * 1.3  # Rough estimate
        }
        
    except Exception as e:
        logger.error(f"Error generating prompt preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating prompt preview"
        )

@router.get("/agent/personality-options")
async def get_personality_options():
    """Get available personality traits and response styles"""
    return {
        "personality_traits": [
            {"value": "friendly", "label": "Friendly & Approachable"},
            {"value": "professional", "label": "Professional & Polished"},
            {"value": "empathetic", "label": "Empathetic & Understanding"},
            {"value": "enthusiastic", "label": "Enthusiastic & Energetic"},
            {"value": "technical", "label": "Technical & Precise"},
            {"value": "formal", "label": "Formal & Structured"},
            {"value": "casual", "label": "Casual & Relaxed"},
            {"value": "patient", "label": "Patient & Thorough"},
            {"value": "direct", "label": "Direct & Concise"},
            {"value": "creative", "label": "Creative & Innovative"},
            {"value": "analytical", "label": "Analytical & Logical"},
            {"value": "supportive", "label": "Supportive & Encouraging"},
            {"value": "energetic", "label": "Energetic & Dynamic"},
            {"value": "calm", "label": "Calm & Composed"}
        ],
        "response_styles": [
            {"value": "conversational", "label": "Conversational", "description": "Friendly and natural, like talking to a person"},
            {"value": "professional", "label": "Professional", "description": "Formal and polished for business contexts"},
            {"value": "technical", "label": "Technical", "description": "Precise and detailed for expert audiences"},
            {"value": "casual", "label": "Casual", "description": "Relaxed and informal tone"},
            {"value": "formal", "label": "Formal", "description": "Structured and official communication"}
        ],
        "industries": [
            {"value": "general", "label": "General Purpose"},
            {"value": "healthcare", "label": "Healthcare & Medical"},
            {"value": "education", "label": "Education & Training"},
            {"value": "ecommerce", "label": "E-commerce & Retail"},
            {"value": "technology", "label": "Technology & Software"},
            {"value": "finance", "label": "Finance & Banking"},
            {"value": "legal", "label": "Legal & Compliance"},
            {"value": "realestate", "label": "Real Estate"},
            {"value": "hospitality", "label": "Hospitality & Travel"},
            {"value": "nonprofit", "label": "Non-profit & Community"}
        ]
    }