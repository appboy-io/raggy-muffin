from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_tenant_id
from app.models import WidgetConfig
from app.config import config
from app.utils.rate_limit import rate_limit_widget_endpoints
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/widgets", tags=["widgets"])

class WidgetConfigRequest(BaseModel):
    widget_title: Optional[str] = None
    widget_subtitle: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    avatar_url: Optional[str] = None
    welcome_message: Optional[str] = None
    placeholder_text: Optional[str] = None
    is_enabled: Optional[bool] = None
    rate_limit_per_hour: Optional[int] = None
    custom_css: Optional[str] = None

class WidgetConfigResponse(BaseModel):
    tenant_id: str
    widget_title: str
    widget_subtitle: str
    primary_color: str
    secondary_color: str
    avatar_url: Optional[str]
    welcome_message: str
    placeholder_text: str
    is_enabled: bool
    rate_limit_per_hour: int
    custom_css: Optional[str]

@router.get("/config", response_model=WidgetConfigResponse)
async def get_widget_config(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get widget configuration for authenticated user"""
    try:
        widget_config = db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id
        ).first()
        
        if not widget_config:
            # Create default config
            widget_config = WidgetConfig(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                widget_title=f"{config.BRAND_NAME} Assistant",
                widget_subtitle="How can I help you?",
                primary_color=config.PRIMARY_COLOR,
                secondary_color=config.SECONDARY_COLOR,
                welcome_message=f"Hello! I'm your {config.BRAND_NAME} assistant. How can I help you today?",
                placeholder_text="Type your message..."
            )
            db.add(widget_config)
            db.commit()
            db.refresh(widget_config)
        
        return WidgetConfigResponse(
            tenant_id=widget_config.tenant_id,
            widget_title=widget_config.widget_title,
            widget_subtitle=widget_config.widget_subtitle,
            primary_color=widget_config.primary_color,
            secondary_color=widget_config.secondary_color,
            avatar_url=widget_config.avatar_url,
            welcome_message=widget_config.welcome_message,
            placeholder_text=widget_config.placeholder_text,
            is_enabled=widget_config.is_enabled,
            rate_limit_per_hour=widget_config.rate_limit_per_hour,
            custom_css=widget_config.custom_css
        )
        
    except Exception as e:
        logger.error(f"Error getting widget config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget configuration"
        )

@router.put("/config", response_model=WidgetConfigResponse)
async def update_widget_config(
    request: WidgetConfigRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Update widget configuration"""
    try:
        widget_config = db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id
        ).first()
        
        if not widget_config:
            # Create new config
            widget_config = WidgetConfig(
                id=uuid.uuid4(),
                tenant_id=tenant_id
            )
            db.add(widget_config)
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(widget_config, field, value)
        
        db.commit()
        db.refresh(widget_config)
        
        return WidgetConfigResponse(
            tenant_id=widget_config.tenant_id,
            widget_title=widget_config.widget_title,
            widget_subtitle=widget_config.widget_subtitle,
            primary_color=widget_config.primary_color,
            secondary_color=widget_config.secondary_color,
            avatar_url=widget_config.avatar_url,
            welcome_message=widget_config.welcome_message,
            placeholder_text=widget_config.placeholder_text,
            is_enabled=widget_config.is_enabled,
            rate_limit_per_hour=widget_config.rate_limit_per_hour,
            custom_css=widget_config.custom_css
        )
        
    except Exception as e:
        logger.error(f"Error updating widget config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update widget configuration"
        )

@router.get("/{tenant_id}/config", response_model=WidgetConfigResponse)
@rate_limit_widget_endpoints()
async def get_public_widget_config(
    request: Request,
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get public widget configuration (no authentication required)"""
    try:
        widget_config = db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id,
            WidgetConfig.is_enabled == True
        ).first()
        
        if not widget_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found or disabled"
            )
        
        return WidgetConfigResponse(
            tenant_id=widget_config.tenant_id,
            widget_title=widget_config.widget_title,
            widget_subtitle=widget_config.widget_subtitle,
            primary_color=widget_config.primary_color,
            secondary_color=widget_config.secondary_color,
            avatar_url=widget_config.avatar_url,
            welcome_message=widget_config.welcome_message,
            placeholder_text=widget_config.placeholder_text,
            is_enabled=widget_config.is_enabled,
            rate_limit_per_hour=widget_config.rate_limit_per_hour,
            custom_css=widget_config.custom_css
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public widget config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget configuration"
        )

@router.get("/{tenant_id}/embed.js", response_class=PlainTextResponse)
@rate_limit_widget_endpoints()
async def get_widget_embed_script(
    request: Request,
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Generate embeddable JavaScript widget"""
    try:
        widget_config = db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id,
            WidgetConfig.is_enabled == True
        ).first()
        
        if not widget_config:
            return "// Widget not found or disabled"
        
        # Helper function to escape JavaScript strings
        def escape_js_string(s):
            if not s:
                return ""
            return s.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        
        # Generate JavaScript embed code
        js_code = f"""
(function() {{
    // {config.BRAND_NAME} Chat Widget
    const TENANT_ID = '{tenant_id}';
    const API_BASE = '{config.API_BASE_URL}';
    const CONFIG = {{
        title: '{escape_js_string(widget_config.widget_title)}',
        subtitle: '{escape_js_string(widget_config.widget_subtitle)}',
        primaryColor: '{escape_js_string(widget_config.primary_color)}',
        secondaryColor: '{escape_js_string(widget_config.secondary_color)}',
        welcomeMessage: '{escape_js_string(widget_config.welcome_message)}',
        placeholder: '{escape_js_string(widget_config.placeholder_text)}',
        avatarUrl: '{escape_js_string(widget_config.avatar_url or "")}'
    }};
    
    let isOpen = false;
    let sessionId = null;
    let messages = [];
    
    // Create widget container
    function createWidget() {{
        const container = document.createElement('div');
        container.id = 'chat-widget-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        
        // Chat toggle button
        const toggleBtn = document.createElement('div');
        toggleBtn.id = 'chat-widget-toggle';
        toggleBtn.style.cssText = `
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: ${{CONFIG.primaryColor}};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-size: 24px;
            transition: all 0.3s ease;
        `;
        toggleBtn.innerHTML = '💬';
        toggleBtn.onclick = toggleChat;
        
        // Chat window
        const chatWindow = document.createElement('div');
        chatWindow.id = 'chat-widget-window';
        chatWindow.style.cssText = `
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            display: none;
            flex-direction: column;
            overflow: hidden;
        `;
        
        createChatWindow(chatWindow);
        
        container.appendChild(toggleBtn);
        container.appendChild(chatWindow);
        document.body.appendChild(container);
    }}
    
    function createChatWindow(chatWindow) {{
        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            background: ${{CONFIG.primaryColor}};
            color: white;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        
        const headerText = document.createElement('div');
        headerText.innerHTML = `
            <div style="font-weight: 600; font-size: 16px;">${{CONFIG.title}}</div>
            <div style="font-size: 12px; opacity: 0.8;">${{CONFIG.subtitle}}</div>
        `;
        
        const closeBtn = document.createElement('div');
        closeBtn.innerHTML = '✕';
        closeBtn.style.cssText = `
            cursor: pointer;
            font-size: 18px;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        `;
        closeBtn.onclick = toggleChat;
        
        header.appendChild(headerText);
        header.appendChild(closeBtn);
        
        // Messages container
        const messagesContainer = document.createElement('div');
        messagesContainer.id = 'chat-messages';
        messagesContainer.style.cssText = `
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #f8f9fa;
        `;
        
        // Welcome message
        if (CONFIG.welcomeMessage) {{
            const welcomeMsg = createMessageBubble(CONFIG.welcomeMessage, false);
            messagesContainer.appendChild(welcomeMsg);
        }}
        
        // Input container
        const inputContainer = document.createElement('div');
        inputContainer.style.cssText = `
            padding: 16px;
            border-top: 1px solid #e9ecef;
            background: white;
        `;
        
        const inputWrapper = document.createElement('div');
        inputWrapper.style.cssText = `
            display: flex;
            gap: 8px;
            align-items: end;
        `;
        
        const messageInput = document.createElement('textarea');
        messageInput.id = 'chat-input';
        messageInput.placeholder = CONFIG.placeholder;
        messageInput.style.cssText = `
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 12px 16px;
            resize: none;
            max-height: 100px;
            font-family: inherit;
            font-size: 14px;
            outline: none;
        `;
        
        const sendBtn = document.createElement('button');
        sendBtn.innerHTML = '➤';
        sendBtn.style.cssText = `
            width: 40px;
            height: 40px;
            border: none;
            background: ${{CONFIG.primaryColor}};
            color: white;
            border-radius: 50%;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        // Event listeners
        sendBtn.onclick = () => sendMessage(messageInput.value);
        messageInput.onkeypress = (e) => {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                sendMessage(messageInput.value);
            }}
        }};
        
        inputWrapper.appendChild(messageInput);
        inputWrapper.appendChild(sendBtn);
        inputContainer.appendChild(inputWrapper);
        
        chatWindow.appendChild(header);
        chatWindow.appendChild(messagesContainer);
        chatWindow.appendChild(inputContainer);
    }}
    
    function createMessageBubble(content, isUser) {{
        const bubble = document.createElement('div');
        bubble.style.cssText = `
            margin-bottom: 12px;
            display: flex;
            ${{isUser ? 'justify-content: flex-end;' : 'justify-content: flex-start;'}}
        `;
        
        const message = document.createElement('div');
        message.style.cssText = `
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            white-space: pre-wrap;
            ${{isUser 
                ? `background: ${{CONFIG.primaryColor}}; color: white; border-bottom-right-radius: 6px;`
                : 'background: white; color: #333; border: 1px solid #e9ecef; border-bottom-left-radius: 6px;'
            }}
        `;
        message.textContent = content;
        
        bubble.appendChild(message);
        return bubble;
    }}
    
    async function sendMessage(content) {{
        if (!content.trim()) return;
        
        const messageInput = document.getElementById('chat-input');
        const messagesContainer = document.getElementById('chat-messages');
        
        // Clear input
        messageInput.value = '';
        
        // Add user message
        const userBubble = createMessageBubble(content, true);
        messagesContainer.appendChild(userBubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Add loading indicator
        const loadingBubble = createMessageBubble('...', false);
        loadingBubble.id = 'loading-message';
        messagesContainer.appendChild(loadingBubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        try {{
            const response = await fetch(`${{API_BASE}}/api/v1/chat/${{TENANT_ID}}/query`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    message: content,
                    session_id: sessionId
                }})
            }});
            
            if (!response.ok) {{
                throw new Error('Failed to send message');
            }}
            
            const data = await response.json();
            
            // Remove loading message
            const loading = document.getElementById('loading-message');
            if (loading) loading.remove();
            
            // Add assistant response
            const assistantBubble = createMessageBubble(data.answer, false);
            messagesContainer.appendChild(assistantBubble);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Store session ID
            if (data.session_id && !sessionId) {{
                sessionId = data.session_id;
            }}
            
        }} catch (error) {{
            console.error('Chat error:', error);
            
            // Remove loading message
            const loading = document.getElementById('loading-message');
            if (loading) loading.remove();
            
            // Show error message
            const errorBubble = createMessageBubble('Sorry, I encountered an error. Please try again.', false);
            messagesContainer.appendChild(errorBubble);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }}
    }}
    
    function toggleChat() {{
        const chatWindow = document.getElementById('chat-widget-window');
        const toggleBtn = document.getElementById('chat-widget-toggle');
        
        isOpen = !isOpen;
        
        if (isOpen) {{
            chatWindow.style.display = 'flex';
            toggleBtn.innerHTML = '✕';
        }} else {{
            chatWindow.style.display = 'none';
            toggleBtn.innerHTML = '💬';
        }}
    }}
    
    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', createWidget);
    }} else {{
        createWidget();
    }}
}})();
"""
        
        return js_code
        
    except Exception as e:
        logger.error(f"Error generating widget embed script: {e}")
        return "// Error loading widget"

@router.get("/{tenant_id}/preview", response_class=HTMLResponse)
@rate_limit_widget_endpoints()
async def get_widget_preview(
    request: Request,
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Generate HTML preview of the widget"""
    try:
        widget_config = db.query(WidgetConfig).filter(
            WidgetConfig.tenant_id == tenant_id
        ).first()
        
        if not widget_config:
            return "<html><body><h1>Widget not found</h1></body></html>"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{widget_config.widget_title} - Preview</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .preview-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .widget-info {{
            background: {widget_config.primary_color};
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .embed-code {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #e9ecef;
            font-family: monospace;
            white-space: pre-wrap;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <h1>{config.BRAND_NAME} Chat Widget Preview</h1>
        
        <div class="widget-info">
            <h2>{widget_config.widget_title}</h2>
            <p>{widget_config.widget_subtitle}</p>
            <p><strong>Welcome Message:</strong> {widget_config.welcome_message}</p>
            <p><strong>Status:</strong> {'Enabled' if widget_config.is_enabled else 'Disabled'}</p>
        </div>
        
        <h3>Embed Code</h3>
        <p>Copy and paste this code into your website:</p>
        <div class="embed-code">&lt;script src="{config.API_BASE_URL}/api/v1/widgets/{tenant_id}/embed.js"&gt;&lt;/script&gt;</div>
        
        <h3>API Endpoints</h3>
        <ul>
            <li><strong>Chat:</strong> POST /api/v1/chat/{tenant_id}/query</li>
            <li><strong>Config:</strong> GET /api/v1/widgets/{tenant_id}/config</li>
        </ul>
    </div>
    
    <!-- Load the actual widget -->
    <script src="{config.API_BASE_URL}/api/v1/widgets/{tenant_id}/embed.js"></script>
</body>
</html>
"""
        
        return html
        
    except Exception as e:
        logger.error(f"Error generating widget preview: {e}")
        return "<html><body><h1>Error loading preview</h1></body></html>"