import os
from typing import Dict, Any
from functools import lru_cache

class ClientConfig:
    """White-label configuration for different clients"""
    
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/db')
        
        # AWS Cognito
        self.AWS_COGNITO_USER_POOL_ID = os.getenv('AWS_COGNITO_USER_POOL_ID')
        self.AWS_COGNITO_CLIENT_ID = os.getenv('AWS_COGNITO_CLIENT_ID') 
        self.AWS_COGNITO_CLIENT_SECRET = os.getenv('AWS_COGNITO_CLIENT_SECRET')
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
        
        # Client Branding
        self.BRAND_NAME = os.getenv('BRAND_NAME', 'Generic RAG')
        self.BRAND_LOGO = os.getenv('BRAND_LOGO', '🤖')
        self.PRIMARY_COLOR = os.getenv('PRIMARY_COLOR', '#0066cc')
        self.SECONDARY_COLOR = os.getenv('SECONDARY_COLOR', '#666666')
        
        # Domains
        self.WIDGET_DOMAIN = os.getenv('WIDGET_DOMAIN', 'widgets.example.com')
        self.ADMIN_DOMAIN = os.getenv('ADMIN_DOMAIN', 'admin.example.com')
        self.API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')
        
        # Feature Limits
        self.MAX_DOCUMENTS_PER_TENANT = int(os.getenv('MAX_DOCUMENTS_PER_TENANT', '100'))
        self.MAX_QUERIES_PER_DAY = int(os.getenv('MAX_QUERIES_PER_DAY', '1000'))
        self.MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
        
        # API Settings
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
        self.ALGORITHM = 'HS256'
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        
        # Cache Settings
        self.REDIS_URL = os.getenv('REDIS_URL', None)  # Optional Redis for caching
        self.CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for API responses"""
        return {
            'brand_name': self.BRAND_NAME,
            'brand_logo': self.BRAND_LOGO,
            'primary_color': self.PRIMARY_COLOR,
            'secondary_color': self.SECONDARY_COLOR,
            'max_documents': self.MAX_DOCUMENTS_PER_TENANT,
            'max_queries_per_day': self.MAX_QUERIES_PER_DAY,
            'max_file_size_mb': self.MAX_FILE_SIZE_MB
        }

@lru_cache()
def get_config() -> ClientConfig:
    """Get cached configuration instance"""
    return ClientConfig()

# Global config instance
config = get_config()