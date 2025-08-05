from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import config
from app.database import init_db
from app.auth.routes import router as auth_router
# from app.cache import cached
from app.utils.rate_limit import limiter, custom_rate_limit_exceeded_handler, rate_limit_general_endpoints
from slowapi.errors import RateLimitExceeded

# Create FastAPI app
app = FastAPI(
    title=f"{config.BRAND_NAME} API",
    description=f"Backend API for {config.BRAND_NAME} RAG platform",
    version="1.0.0"
)

# Add rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")

# Import and include other routers
from app.routers.documents import router as documents_router
from app.routers.chat import router as chat_router
from app.routers.widgets import router as widgets_router
from app.routers.customer import router as customer_router

app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(widgets_router, prefix="/api/v1")
app.include_router(customer_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
@rate_limit_general_endpoints()
async def root(request: Request):
    """Root endpoint with client branding"""
    return {
        "message": f"Welcome to {config.BRAND_NAME} API",
        "version": "1.0.0",
        "brand": config.BRAND_NAME,
        "logo": config.BRAND_LOGO
    }

@app.get("/api/v1/config")
@rate_limit_general_endpoints()
# @cached(key_prefix="config", ttl=3600)  # Cache for 1 hour
async def get_config(request: Request):
    """Get client configuration for frontend"""
    return config.to_dict()

@app.get("/health")
@rate_limit_general_endpoints()
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy", "brand": config.BRAND_NAME}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )