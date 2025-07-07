import os
from typing import Dict, Any

class AppConfig:
    """Configuration class for white-label application settings"""
    
    def __init__(self):
        # Load all configuration from environment variables with defaults
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        
        # App Branding
        self.APP_NAME = os.getenv('APP_NAME', 'Raggy Muffin')
        self.APP_ICON = os.getenv('APP_ICON', '🧠')
        self.APP_TAGLINE = os.getenv('APP_TAGLINE', 'Turn Your Documents Into Intelligent Conversations')
        self.APP_DESCRIPTION = os.getenv('APP_DESCRIPTION', 'Built by researchers, for researchers. Upload your documents, ask questions in natural language, and get instant, accurate answers with source citations.')
        
        # Pricing
        self.STARTER_PLAN_PRICE = os.getenv('STARTER_PLAN_PRICE', '$19')
        self.STARTER_PLAN_PERIOD = os.getenv('STARTER_PLAN_PERIOD', 'month')
        self.FREE_TRIAL_DAYS = os.getenv('FREE_TRIAL_DAYS', '14')
        self.STARTER_PLAN_PAGES = os.getenv('STARTER_PLAN_PAGES', '1,000')
        
        # Features
        self.FEATURE_1_TITLE = os.getenv('FEATURE_1_TITLE', 'Instant Insights')
        self.FEATURE_1_ICON = os.getenv('FEATURE_1_ICON', '🎯')
        self.FEATURE_1_DESC = os.getenv('FEATURE_1_DESC', 'Upload documents and start asking questions immediately. No complex setup or training required.')
        self.FEATURE_1_QUOTE = os.getenv('FEATURE_1_QUOTE', 'I can now analyze 100+ research papers in minutes instead of days')
        
        self.FEATURE_2_TITLE = os.getenv('FEATURE_2_TITLE', 'Your Data, Your Control')
        self.FEATURE_2_ICON = os.getenv('FEATURE_2_ICON', '🔒')
        self.FEATURE_2_DESC = os.getenv('FEATURE_2_DESC', 'Enterprise-grade security with complete data privacy. Your documents never leave your secure workspace.')
        self.FEATURE_2_QUOTE = os.getenv('FEATURE_2_QUOTE', 'Finally, a solution that respects our confidential research data')
        
        self.FEATURE_3_TITLE = os.getenv('FEATURE_3_TITLE', 'Pay Only For What You Use')
        self.FEATURE_3_ICON = os.getenv('FEATURE_3_ICON', '💰')
        self.FEATURE_3_DESC = os.getenv('FEATURE_3_DESC', 'Transparent pricing based on document processing. No hidden fees, no surprises.')
        self.FEATURE_3_QUOTE = os.getenv('FEATURE_3_QUOTE', 'More cost-effective than hiring a research assistant')
        
        # Social Proof
        self.SOCIAL_PROOF_TEXT = os.getenv('SOCIAL_PROOF_TEXT', 'Trusted by thousands of researchers, analysts, and knowledge workers worldwide')
        
        # Testimonials
        self.TESTIMONIAL_1_TEXT = os.getenv('TESTIMONIAL_1_TEXT', 'Raggy Muffin transformed how I conduct literature reviews. What used to take weeks now takes hours. The accuracy of answers and proper citations save me countless hours of verification.')
        self.TESTIMONIAL_1_AUTHOR = os.getenv('TESTIMONIAL_1_AUTHOR', 'Dr. Sarah Chen')
        self.TESTIMONIAL_1_TITLE = os.getenv('TESTIMONIAL_1_TITLE', 'Research Scientist, MIT')
        
        self.TESTIMONIAL_2_TEXT = os.getenv('TESTIMONIAL_2_TEXT', 'As a legal researcher, I need precise information fast. Raggy Muffin helps me find relevant precedents and extract key arguments from hundreds of case documents effortlessly.')
        self.TESTIMONIAL_2_AUTHOR = os.getenv('TESTIMONIAL_2_AUTHOR', 'Marcus Rodriguez')
        self.TESTIMONIAL_2_TITLE = os.getenv('TESTIMONIAL_2_TITLE', 'Senior Legal Analyst')
        
        # Document Types
        self.SUPPORTED_FORMATS = os.getenv('SUPPORTED_FORMATS', 'PDFs, Word docs, text files, Research papers & reports, Legal documents & contracts').split(', ')
        
        # Use Cases
        self.USE_CASES = os.getenv('USE_CASES', 'Research analysis, Document review, Knowledge extraction, Content summarization, Q&A automation').split(', ')
        
        # Company Info
        self.COMPANY_NAME = os.getenv('COMPANY_NAME', 'Raggy Muffin Inc.')
        self.SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'support@raggymuffin.com')
        self.WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://raggymuffin.com')
        
        # AWS Cognito (keep existing)
        self.AWS_COGNITO_USER_POOL_ID = os.getenv('AWS_COGNITO_USER_POOL_ID')
        self.AWS_COGNITO_CLIENT_ID = os.getenv('AWS_COGNITO_CLIENT_ID')
        self.AWS_COGNITO_CLIENT_SECRET = os.getenv('AWS_COGNITO_CLIENT_SECRET')
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
        
        # Streamlit Config
        self.STREAMLIT_PAGE_TITLE = os.getenv('STREAMLIT_PAGE_TITLE', f'{self.APP_NAME} - RAG Q&A Platform')
        self.STREAMLIT_PAGE_ICON = os.getenv('STREAMLIT_PAGE_ICON', self.APP_ICON)
        self.STREAMLIT_LAYOUT = os.getenv('STREAMLIT_LAYOUT', 'wide')
        
        # Color Theme (hex colors)
        self.PRIMARY_COLOR = os.getenv('PRIMARY_COLOR', '#0066cc')
        self.SECONDARY_COLOR = os.getenv('SECONDARY_COLOR', '#666666')
        self.ACCENT_COLOR = os.getenv('ACCENT_COLOR', '#f9f9f9')
        
        # Domains
        self.ADMIN_DOMAIN = os.getenv('ADMIN_DOMAIN', 'http://localhost:3000')
        self.API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.WEBSITE_DOMAIN = os.getenv('WEBSITE_DOMAIN', 'http://localhost:3002')
        
        # CTA Buttons
        self.CTA_PRIMARY_TEXT = os.getenv('CTA_PRIMARY_TEXT', 'GET STARTED FREE')
        self.CTA_SECONDARY_TEXT = os.getenv('CTA_SECONDARY_TEXT', 'START FREE TRIAL')
        self.CTA_TRIAL_TEXT = os.getenv('CTA_TRIAL_TEXT', f'Start your {self.FREE_TRIAL_DAYS}-day free trial')
    
    def get_starter_plan_features(self) -> list:
        """Get starter plan features as a list"""
        features_env = os.getenv('STARTER_PLAN_FEATURES', 
            f'{self.STARTER_PLAN_PAGES} pages processed/{self.STARTER_PLAN_PERIOD}|Unlimited questions|Document management dashboard|Export capabilities|Email support')
        return [f"✅ {feature.strip()}" for feature in features_env.split('|')]
    
    def get_trial_benefits(self) -> list:
        """Get trial benefits as a list"""
        benefits_env = os.getenv('TRIAL_BENEFITS',
            f'Process up to {self.STARTER_PLAN_PAGES} pages|Unlimited questions and queries|Full document management dashboard|Export capabilities|Email support|All features unlocked for {self.FREE_TRIAL_DAYS} days')
        return [f"✅ {benefit.strip()}" for benefit in benefits_env.split('|')]
    
    def get_how_it_works_steps(self) -> list:
        """Get how it works steps"""
        steps = [
            {
                'number': '1',
                'icon': '📁',
                'title': os.getenv('STEP_1_TITLE', 'Upload'),
                'desc': os.getenv('STEP_1_DESC', 'Drag & drop your documents'),
                'details': os.getenv('STEP_1_DETAILS', '- PDFs, Word docs, text files\n- Research papers & reports\n- Legal documents & contracts')
            },
            {
                'number': '2',
                'icon': '🤖',
                'title': os.getenv('STEP_2_TITLE', 'Process'),
                'desc': os.getenv('STEP_2_DESC', 'AI analyzes your content'),
                'details': os.getenv('STEP_2_DETAILS', '- Intelligent text extraction\n- Semantic understanding\n- Citation mapping')
            },
            {
                'number': '3',
                'icon': '💬',
                'title': os.getenv('STEP_3_TITLE', 'Ask'),
                'desc': os.getenv('STEP_3_DESC', 'Query in natural language'),
                'details': os.getenv('STEP_3_DETAILS', '- "What are the key findings?"\n- "Compare methodology across papers"\n- "Find contradicting evidence"')
            },
            {
                'number': '4',
                'icon': '✨',
                'title': os.getenv('STEP_4_TITLE', 'Get Answers'),
                'desc': os.getenv('STEP_4_DESC', 'Receive intelligent responses'),
                'details': os.getenv('STEP_4_DETAILS', '- Accurate, contextual answers\n- Source citations included\n- Export to reports')
            }
        ]
        return steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for easy access"""
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

# Global configuration instance
config = AppConfig()