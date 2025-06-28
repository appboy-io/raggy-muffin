# White Label RAG Q&A Platform

A fully configurable, white-label document analysis platform that can be quickly deployed for different clients with custom branding, messaging, and features.

## 🚀 Features

- **Complete White Labeling**: Every text, color, and message can be customized
- **AWS Cognito Authentication**: Secure user management and subscriptions
- **Plug & Play Deployment**: Easy Docker-based deployment for multiple clients
- **RAG-Powered Q&A**: Advanced document analysis with AI-powered question answering
- **Subscription Ready**: Built-in pricing pages and trial management

## 🔧 Quick Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd raggy-muffin
pip install -r requirements.txt
```

### 2. Configure for Your Client

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` with your client's specific configuration:
- App name, tagline, and description
- Pricing and trial periods
- Brand colors and messaging
- AWS Cognito credentials
- Testimonials and social proof

### 3. Deploy with Docker

For default deployment:
```bash
docker-compose up -d
```

For client-specific deployment:
```bash
# Copy and customize the client template
cp docker-compose.client-example.yml docker-compose.override.yml
# Edit docker-compose.override.yml with client-specific values
docker-compose up -d
```

## 🎨 White Label Configuration

### Core Branding
```bash
APP_NAME=Your Client Name
APP_ICON=🧠
APP_TAGLINE=Your Custom Tagline
APP_DESCRIPTION=Your custom description...
```

### Pricing & Features
```bash
STARTER_PLAN_PRICE=$49
FREE_TRIAL_DAYS=14
FEATURE_1_TITLE=Custom Feature Name
FEATURE_1_ICON=🎯
FEATURE_1_DESC=Custom feature description...
```

### Color Theme
```bash
PRIMARY_COLOR=#0066cc
SECONDARY_COLOR=#666666
ACCENT_COLOR=#f9f9f9
```

### Testimonials & Social Proof
```bash
TESTIMONIAL_1_TEXT=Custom testimonial text...
TESTIMONIAL_1_AUTHOR=Client Name
SOCIAL_PROOF_TEXT=Trusted by X clients worldwide
```

## 🔐 AWS Cognito Setup

1. Create a User Pool in AWS Cognito
2. Create an App Client with client secret
3. Configure the following environment variables:
```bash
AWS_COGNITO_USER_POOL_ID=your_pool_id
AWS_COGNITO_CLIENT_ID=your_client_id
AWS_COGNITO_CLIENT_SECRET=your_client_secret
AWS_REGION=us-east-1
```

## 🐳 Multi-Client Deployment

### Method 1: Environment Variables
Set environment variables before running:
```bash
export APP_NAME="Client Specific Name"
export PRIMARY_COLOR="#ff6b6b"
docker-compose up -d
```

### Method 2: Override Files
Create client-specific override files:
```bash
# For Client A
docker-compose -f docker-compose.yml -f docker-compose.client-a.yml up -d

# For Client B  
docker-compose -f docker-compose.yml -f docker-compose.client-b.yml up -d
```

### Method 3: Multiple .env Files
```bash
# Deploy for different clients
docker-compose --env-file .env.client-a up -d
docker-compose --env-file .env.client-b up -d
```

## 📁 Application Structure

```
app/
├── config.py              # Configuration management
├── auth.py                # AWS Cognito authentication
├── product_page.py        # White-labeled landing page
├── login_page.py          # Configurable login page
├── signup_page.py         # Configurable signup page
├── app.py                 # Main application with auth logic
└── [other app files]      # Core RAG functionality
```

## 🔧 Configuration Reference

See `.env.example` for a complete list of configurable options including:

- **App Branding**: Name, icon, tagline, description
- **Pricing**: Plans, trial periods, feature lists
- **Features**: Icons, titles, descriptions, quotes
- **Testimonials**: Customer stories and social proof
- **Colors**: Primary, secondary, accent colors
- **CTAs**: Button text and trial messaging
- **Company Info**: Support email, website, company name

## 🚀 Deployment Examples

### Legal Industry Client
```bash
APP_NAME="LegalIQ Pro"
APP_TAGLINE="Unlock Insights from Legal Documents"
PRIMARY_COLOR="#1a472a"
FEATURE_1_TITLE="Instant Legal Research"
TESTIMONIAL_1_AUTHOR="Sarah Mitchell, Esq."
```

### Healthcare Client
```bash
APP_NAME="MedDocAI"
APP_TAGLINE="Transform Medical Records into Insights"
PRIMARY_COLOR="#2b77ad"
FEATURE_1_TITLE="HIPAA-Compliant Analysis"
TESTIMONIAL_1_AUTHOR="Dr. Robert Chen, MD"
```

### Financial Services Client
```bash
APP_NAME="FinDocAnalyzer"
APP_TAGLINE="Intelligent Financial Document Review"
PRIMARY_COLOR="#c5a632"
FEATURE_1_TITLE="Regulatory Compliance Ready"
TESTIMONIAL_1_AUTHOR="Jennifer Martinez, CFA"
```

## 📞 Support

For technical support or customization requests, contact the development team or refer to the configuration documentation in `.env.example`.

## 🔒 Security

- All client data is isolated per deployment
- AWS Cognito provides enterprise-grade authentication
- Environment-based configuration prevents cross-client data leaks
- Docker containerization ensures deployment consistency