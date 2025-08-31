from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_sync
from app.models import SuperAdmin, SystemConfig
import asyncio

class SetupCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check if initial system setup is complete.
    Blocks all requests except setup-related endpoints until a superadmin exists.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.setup_complete = None
        self.allowed_paths = {
            "/api/superadmin/setup/status",
            "/api/superadmin/setup/initialize",
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/redoc"
        }
    
    async def check_setup_status(self) -> bool:
        """Check if setup is complete by looking for superadmins"""
        try:
            # Create a new database session
            async with get_db_sync() as db:
                # Check if any superadmin exists
                result = await db.execute(
                    select(func.count(SuperAdmin.id))
                )
                superadmin_count = result.scalar()
                
                # Check system config
                result = await db.execute(
                    select(SystemConfig)
                    .where(SystemConfig.key == "setup_complete")
                )
                config = result.scalar_one_or_none()
                
                # Setup is complete if we have at least one superadmin
                # and the config says setup is complete
                if superadmin_count > 0:
                    if config and config.value == False:
                        # Update config if it's out of sync
                        config.value = True
                        await db.commit()
                    return True
                
                return False
        except Exception as e:
            # If there's an error checking (e.g., tables don't exist yet),
            # assume setup is not complete
            print(f"Error checking setup status: {e}")
            return False
    
    async def dispatch(self, request: Request, call_next):
        """Check each request to see if setup is required"""
        
        # Always allow these paths
        if request.url.path in self.allowed_paths:
            return await call_next(request)
        
        # Allow any path that starts with allowed prefixes
        allowed_prefixes = ["/api/superadmin/setup/", "/docs", "/redoc"]
        for prefix in allowed_prefixes:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        
        # Check if setup is complete (with caching to avoid hitting DB every request)
        if self.setup_complete is None or not self.setup_complete:
            self.setup_complete = await self.check_setup_status()
        
        if not self.setup_complete:
            # Return 503 Service Unavailable with setup required message
            return JSONResponse(
                status_code=503,
                content={
                    "error": "System setup required",
                    "setup_required": True,
                    "message": "Initial system setup has not been completed. Please navigate to /setup to configure the system.",
                    "setup_url": "/setup"
                }
            )
        
        # Setup is complete, proceed with the request
        response = await call_next(request)
        return response
    
    def invalidate_cache(self):
        """Invalidate the setup status cache"""
        self.setup_complete = None