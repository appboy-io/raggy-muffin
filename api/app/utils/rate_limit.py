"""
Rate limiting utilities for API endpoints
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import redis
from app.config import config

# Initialize Redis connection for rate limiting with connection pooling
redis_client = redis.Redis.from_url(
    config.REDIS_URL, 
    decode_responses=True,
    max_connections=50,
    retry_on_timeout=True,
    socket_connect_timeout=3,
    socket_timeout=3,
    health_check_interval=30
)

# Key function for rate limiting - uses IP address
def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on IP address"""
    return get_remote_address(request)

# Initialize the limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=config.REDIS_URL,
    default_limits=["1000/hour"]  # Global default limit
)

# Custom rate limit exceeded handler
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    return HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after
        }
    )

def get_tenant_rate_limit(tenant_id: str) -> str:
    """Get rate limit for a specific tenant from their widget config with caching"""
    try:
        # Try to get from cache first
        cache_key = f"tenant_rate_limit:{tenant_id}"
        cached_limit = redis_client.get(cache_key)
        
        if cached_limit:
            return cached_limit
        
        # Get from database
        from app.database import SessionLocal
        from app.models import WidgetConfig
        
        with SessionLocal() as db:
            widget_config = db.query(WidgetConfig).filter(
                WidgetConfig.tenant_id == tenant_id
            ).first()
            
            if widget_config and widget_config.rate_limit_per_hour:
                rate_limit = f"{widget_config.rate_limit_per_hour}/hour"
            else:
                rate_limit = "100/hour"  # Default rate limit
            
            # Cache the result for 5 minutes
            redis_client.setex(cache_key, 300, rate_limit)
            return rate_limit
                
    except Exception:
        return "100/hour"  # Fallback on error

def get_tenant_rate_limit_key(request: Request, tenant_id: str) -> str:
    """Get rate limit key for tenant-specific endpoints"""
    ip_address = get_remote_address(request)
    return f"{tenant_id}:{ip_address}"

# Tenant-specific limiter
def create_tenant_limiter(tenant_id: str):
    """Create a tenant-specific rate limiter"""
    rate_limit = get_tenant_rate_limit(tenant_id)
    
    def tenant_key_func(request: Request) -> str:
        return get_tenant_rate_limit_key(request, tenant_id)
    
    return Limiter(
        key_func=tenant_key_func,
        storage_uri=config.REDIS_URL,
        default_limits=[rate_limit]
    )

# Rate limiting decorators for different endpoint types
def rate_limit_auth_endpoints():
    """Rate limiter for authentication endpoints"""
    return limiter.limit("10/minute")  # Stricter for auth

def rate_limit_chat_endpoints():
    """Rate limiter for chat endpoints"""
    return limiter.limit("60/hour")  # Moderate for chat

def rate_limit_widget_endpoints():
    """Rate limiter for widget endpoints"""
    return limiter.limit("300/hour")  # More permissive for widget access

def rate_limit_general_endpoints():
    """Rate limiter for general public endpoints"""
    return limiter.limit("500/hour")  # General rate limit

def rate_limit_document_upload():
    """Rate limiter for document upload endpoints"""
    return limiter.limit("10/hour")  # Stricter for uploads

def rate_limit_embedding_endpoints():
    """Rate limiter for embedding generation endpoints"""
    return limiter.limit("20/hour")  # Moderate for expensive operations

def rate_limit_admin_endpoints():
    """Rate limiter for admin endpoints"""
    return limiter.limit("1000/hour")  # More permissive for admin users