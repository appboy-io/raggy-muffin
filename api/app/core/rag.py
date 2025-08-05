from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.embedding import embed_query_async
from app.models import Embedding
# from app.cache import cached
from typing import List, Dict, Any
import logging
import re
import json
import hashlib
import ollama
import os
import asyncio

logger = logging.getLogger(__name__)

def get_chat_model():
    """Get the chat model name from environment"""
    return os.getenv('OLLAMA_CHAT_MODEL', 'llama3.2:3b-instruct-q4_0')

def get_ollama_host():
    """Get Ollama host from environment"""
    return os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# @cached(key_prefix="rag_chunks", ttl=1800)  # Cache for 30 minutes
async def retrieve_relevant_chunks(
    query: str, 
    tenant_id: str, 
    db: Session, 
    top_k: int = 4
) -> List[str]:
    """
    Retrieve relevant chunks using vector similarity search
    Cached for 30 minutes to improve performance
    """
    logger.error(f"retrieve_relevant_chunks called with query='{query}', tenant_id='{tenant_id}'")
    try:
        # Get query embedding
        query_embedding = await embed_query_async(query)
        
        # First check total embeddings for this tenant
        count_result = db.execute(
            text("SELECT COUNT(*) FROM embeddings WHERE tenant_id = :tenant"),
            {"tenant": tenant_id}
        )
        total_embeddings = count_result.fetchone()[0]
        logger.error(f"Total embeddings for tenant {tenant_id}: {total_embeddings}")
        
        # Perform vector similarity search without threshold to see top matches
        result = db.execute(
            text("""
                SELECT content, 
                       (1 - (embedding <-> (:query_emb)::vector)) as similarity
                FROM embeddings
                WHERE tenant_id = :tenant
                ORDER BY embedding <-> (:query_emb)::vector
                LIMIT :top_k
            """),
            {
                "tenant": tenant_id, 
                "query_emb": query_embedding, 
                "top_k": top_k
            }
        )
        
        rows = result.fetchall()
        chunks = [row[0] for row in rows]
        
        # Debug logging
        logger.error(f"Query: '{query}' for tenant: {tenant_id}")
        logger.error(f"Found {len(chunks)} chunks with similarities: {[f'{row[1]:.3f}' for row in rows[:3]]}")
        
        # Log first chunk content to see what's being matched
        if chunks:
            logger.error(f"Best match content (first 200 chars): {chunks[0][:200]}...")
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error retrieving chunks: {e}")
        return []

# @cached(key_prefix="rag_batch_chunks", ttl=1800)  # Cache for 30 minutes
async def retrieve_relevant_chunks_batch(
    queries: List[str], 
    tenant_id: str, 
    db: Session, 
    top_k: int = 4
) -> Dict[str, List[str]]:
    """
    Retrieve relevant chunks for multiple queries efficiently
    """
    try:
        # Get all query embeddings in batch
        query_embeddings = []
        for query in queries:
            embedding = await embed_query_async(query)
            query_embeddings.append(embedding)
        
        # Perform batch similarity search
        results = {}
        for query, query_embedding in zip(queries, query_embeddings):
            result = db.execute(
                text("""
                    SELECT content, 
                           (1 - (embedding <-> (:query_emb)::vector)) as similarity
                    FROM embeddings
                    WHERE tenant_id = :tenant
                      AND (embedding <-> (:query_emb)::vector) < 0.5
                    ORDER BY embedding <-> (:query_emb)::vector
                    LIMIT :top_k
                """),
                {
                    "tenant": tenant_id, 
                    "query_emb": query_embedding, 
                    "top_k": top_k
                }
            )
            
            chunks = [row[0] for row in result.fetchall()]
            results[query] = chunks
        
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving batch chunks: {e}")
        return {query: [] for query in queries}

def extract_contact_info(context_chunks: List[str]) -> Dict[str, List[str]]:
    """Extract contact information from context chunks with better parsing"""
    contact_info = {
        "emails": [],
        "phones": [],
        "websites": [],
        "addresses": []
    }
    
    # Improved regular expressions for contact information
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # More specific phone pattern - full 10-digit numbers only
    phone_pattern = r'\b(?:\(\d{3}\)\s*|\d{3}[-.\s]?)?\d{3}[-.\s]?\d{4}\b'
    # Better URL pattern - complete URLs only
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;!?]'
    
    # Look for normalized sections first
    for chunk in context_chunks:
        if "CONTACT INFORMATION:" in chunk:
            # Extract information from structured data
            lines = chunk.split('\n')
            for i, line in enumerate(lines):
                if "Email:" in line:
                    emails = re.findall(email_pattern, line)
                    contact_info["emails"].extend(emails)
                elif "Phone:" in line:
                    phones = re.findall(phone_pattern, line)
                    # Filter to complete phone numbers only
                    valid_phones = [p for p in phones if len(re.sub(r'[^\d]', '', p)) == 10]
                    contact_info["phones"].extend(valid_phones)
                elif "Website:" in line or "URL:" in line:
                    urls = re.findall(url_pattern, line)
                    # Filter out incomplete URLs
                    valid_urls = [url for url in urls if '.' in url and not url.endswith('..')]
                    contact_info["websites"].extend(valid_urls)
                elif "Address:" in line and i+1 < len(lines):
                    # Address might span multiple lines
                    address = line.replace("Address:", "").strip()
                    if address:
                        contact_info["addresses"].append(address)
    
    # If structured data wasn't found, try to extract from raw text more carefully
    if not any(contact_info.values()):
        for chunk in context_chunks:
            # Extract emails
            emails = re.findall(email_pattern, chunk)
            contact_info["emails"].extend(emails)
            
            # Extract complete phone numbers only
            phones = re.findall(phone_pattern, chunk)
            valid_phones = []
            for phone in phones:
                # Clean and validate phone number
                digits_only = re.sub(r'[^\d]', '', phone)
                if len(digits_only) == 10:
                    # Format nicely
                    formatted = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
                    valid_phones.append(formatted)
            contact_info["phones"].extend(valid_phones)
            
            # Extract complete URLs only
            urls = re.findall(url_pattern, chunk)
            valid_urls = []
            for url in urls:
                # Filter out incomplete or broken URLs
                if (not url.endswith('..') and 
                    '.' in url and 
                    len(url) > 10 and
                    not url.startswith('http://www..')):
                    valid_urls.append(url)
            contact_info["websites"].extend(valid_urls)
    
    # Deduplicate and clean
    for key in contact_info:
        # Remove duplicates and empty strings
        contact_info[key] = list(set([item for item in contact_info[key] if item and item.strip()]))
    
    # Limit results to prevent overwhelming output
    contact_info["emails"] = contact_info["emails"][:3]
    contact_info["phones"] = contact_info["phones"][:3]
    contact_info["websites"] = contact_info["websites"][:3]
    contact_info["addresses"] = contact_info["addresses"][:3]
    
    return contact_info

def extract_categories_from_chunks(chunks: List[str]) -> List[str]:
    """Extract categories from normalized chunks"""
    categories = []
    
    for chunk in chunks:
        if "CATEGORIES:" in chunk:
            # Extract the categories line
            lines = chunk.split('\n')
            for line in lines:
                if "CATEGORIES:" in line:
                    # Extract categories
                    cats = line.replace("CATEGORIES:", "").strip()
                    # Split by comma and clean
                    cat_list = [c.strip() for c in cats.split(',')]
                    categories.extend(cat_list)
    
    # Return unique categories
    return list(set(categories))

async def generate_single_prompt_response(question: str, context_chunks: List[str]) -> str:
    """
    Generate response using Ollama LLM
    """
    # Extract data for context
    chunk_categories = extract_categories_from_chunks(context_chunks)
    contact_info = extract_contact_info(context_chunks)
    providers = []
    descriptions = []
    
    # Extract providers from unstructured text (handles bullet points with ●)
    for chunk in context_chunks:
        # Look for patterns like "● Name, MD" or "● Name, NP"
        provider_matches = re.findall(r'●\s*([^●\n]+?(?:,\s*(?:MD|NP|DO|PA|RN))[^●\n]*)', chunk)
        for match in provider_matches:
            # Clean up the provider name
            provider = match.strip()
            # Remove extra info in parentheses for the main name, but keep it for context
            if provider and provider not in providers:
                providers.append(provider)
        
        # Also look for structured format
        if "PROVIDER:" in chunk:
            provider = chunk.split("PROVIDER:")[1].split('\n')[0].strip()
            if provider and provider not in providers:
                providers.append(provider)
        if "DESCRIPTION:" in chunk:
            desc = chunk.split("DESCRIPTION:")[1].strip()
            cleaned_desc = clean_text_content(desc)
            if cleaned_desc:
                descriptions.append(cleaned_desc)
    
    logger.error(f"Extracted providers: {providers}")
    logger.error(f"Extracted contact_info: {contact_info}")
    logger.error(f"Extracted categories: {chunk_categories}")
    
    # Create the prompt
    system_prompt = """You are Clara, a helpful and empathetic assistant that connects people with local aid services and resources. You have access to a database of service providers and organizations that offer various types of assistance.

Your personality:
- Warm, caring, and encouraging
- Patient and understanding of people's situations
- Professional but approachable
- Always try to be helpful, even for general questions
- Acknowledge when someone seems urgent or stressed
- Guide people toward finding the help they need

When someone asks about services:
1. If you have relevant information, provide it in a structured, easy-to-read format
2. Include provider names, service categories, descriptions, and contact information
3. Give practical next steps and encouraging guidance
4. Handle emergency situations with appropriate urgency

When someone asks general questions or greets you:
1. Respond warmly and conversationally
2. Gently guide them toward asking about services if appropriate
3. Explain what kind of help you can provide

Always be encouraging and remind people that help is available."""
    
    user_prompt = f"""User Question: {question}

Available Information:
"""
    
    if context_chunks:
        user_prompt += f"""
Service Categories: {', '.join(chunk_categories) if chunk_categories else 'Not specified'}
Providers: {', '.join(providers) if providers else 'Not specified'}
Descriptions: {'; '.join(descriptions[:2]) if descriptions else 'Not available'}

Contact Information:
- Phones: {', '.join(contact_info.get('phones', [])) if contact_info.get('phones') else 'Not available'}
- Emails: {', '.join(contact_info.get('emails', [])) if contact_info.get('emails') else 'Not available'}
- Websites: {', '.join(contact_info.get('websites', [])) if contact_info.get('websites') else 'Not available'}
- Addresses: {', '.join(contact_info.get('addresses', [])) if contact_info.get('addresses') else 'Not available'}

Please provide a helpful response based on this information."""
    else:
        user_prompt += """
No specific service information was found for this question.

Please respond helpfully. If this is a greeting or general question, respond conversationally and guide them toward asking about services. If they're asking about services but no information was found, explain this warmly and suggest they try rephrasing or ask about other topics."""
    
    try:
        # Call Ollama API with async
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.chat(
                model=get_chat_model(),
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                options={'host': get_ollama_host(), 'temperature': 0.7}
            )
        )
        
        return response['message']['content']
        
    except Exception as e:
        logger.error(f"Error generating response with Ollama: {str(e)}")
        # Fallback to simulate_llm_response
        return simulate_llm_response(question, context_chunks, chunk_categories, contact_info, providers, descriptions)

def simulate_llm_response(question: str, context_chunks: List[str], categories: List[str], contact_info: Dict, providers: List[str], descriptions: List[str]) -> str:
    """
    Fallback response generation when Ollama is not available
    """
    q_lower = question.lower().strip()
    
    # Handle greetings and general conversation
    if any(greeting in q_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return """Hi there! I'm Clara, and I'm here to help you find local resources and services. 

I can help you locate:
• Housing assistance and shelters
• Food banks and meal programs  
• Healthcare services
• Job training and employment help
• Financial assistance programs
• Mental health and counseling services
• And many other community resources

What kind of support are you looking for today?"""
    
    if any(question in q_lower for question in ['what can you do', 'what do you do', 'how can you help']):
        return """I'm here to help connect you with local aid services and community resources! 

I have access to information about various organizations and programs that provide:

• **Housing**: Emergency shelters, transitional housing, rental assistance
• **Food**: Food banks, soup kitchens, meal delivery programs
• **Healthcare**: Community health centers, free clinics, mental health services
• **Employment**: Job training, career counseling, placement services
• **Financial Help**: Utility assistance, emergency funds, benefits enrollment
• **Family Services**: Childcare, elder care, family counseling

Just tell me what kind of help you're looking for, and I'll find the best resources in your area. Is there something specific you need assistance with?"""
    
    # Handle service requests with context
    if not context_chunks:
        if any(urgent in q_lower for urgent in ['emergency', 'urgent', 'crisis', 'immediate']):
            return """I understand this is urgent, and I want to help you right away. Unfortunately, I wasn't able to find specific information that matches your request in our current database.

**For immediate emergencies:**
• Call 911 if this is a life-threatening situation
• Call 211 for general crisis support and resource referrals
• Visit your local emergency room if you need immediate medical care

If you can provide more details about what type of assistance you need (housing, food, healthcare, etc.), I might be able to find other relevant resources for you."""
        
        return """I wasn't able to find specific information that matches your question in our current resource database. This could mean:

• The information might not be in our system yet
• You might try rephrasing with different keywords
• The service might not be available in this area

Some things you can try:
• Be more specific about the type of help you need
• Ask about related services (like "food assistance" instead of "groceries")
• Try asking about a broader category first

I'm here to help connect you with resources, so don't hesitate to ask about other topics or rephrase your question!"""
    
    # Handle service requests with context - build response
    response_parts = []
    
    # Contextual intro based on urgency and question type
    if any(urgent in q_lower for urgent in ['emergency', 'urgent', 'crisis', 'immediate']):
        if categories:
            response_parts.append(f"I understand this is urgent. Let me get you the {', '.join(categories).lower()} resources you need right away.")
        else:
            response_parts.append("I understand this is urgent. Here are the resources I found for your immediate needs.")
    elif any(help_word in q_lower for help_word in ['help', 'need', 'can you', 'looking for']):
        if categories:
            response_parts.append(f"I'd be happy to help you find {', '.join(categories).lower()} services! Here are some options that might work for your situation.")
        else:
            response_parts.append("I'd be happy to help! Here are some resources that should be useful for your situation.")
    else:
        if categories:
            response_parts.append(f"Great question! I found several {', '.join(categories).lower()} resources for you.")
        else:
            response_parts.append("Here's what I found that should help with your request.")
    
    response_parts.append("")
    
    # Add service categories
    if categories:
        if len(categories) == 1:
            response_parts.append(f"**Service Category:** {categories[0]}")
        else:
            response_parts.append(f"**Related Categories:** {', '.join(categories)}")
        response_parts.append("")
    
    # Add providers
    if providers:
        if len(providers) == 1:
            response_parts.append("**Available Provider:**")
        else:
            response_parts.append(f"**Available Providers ({len(providers)} found):**")
        for provider in providers[:5]:
            response_parts.append(f"• {provider}")
        if len(providers) > 5:
            response_parts.append(f"• ...and {len(providers) - 5} more providers")
        response_parts.append("")
    
    # Add description
    if descriptions:
        response_parts.append("**About These Services:**")
        best_desc = get_best_description(descriptions)
        if len(best_desc) > 300:
            break_point = best_desc.find('. ', 200)
            if break_point > 0:
                response_parts.append(best_desc[:break_point + 1])
            else:
                response_parts.append(best_desc[:300] + "...")
        else:
            response_parts.append(best_desc)
        response_parts.append("")
    
    # Add contact info
    if any(contact_info.values()):
        response_parts.append("**How to Get Started:**")
        
        if contact_info.get("phones"):
            for phone in contact_info["phones"][:3]:
                response_parts.append(f"• Call: {phone}")
        
        if contact_info.get("emails"):
            for email in contact_info["emails"][:3]:
                response_parts.append(f"• Email: {email}")
        
        if contact_info.get("websites"):
            for website in contact_info["websites"][:3]:
                response_parts.append(f"• Visit: {website}")
        
        if contact_info.get("addresses"):
            response_parts.append(f"• Location: {contact_info['addresses'][0]}")
        
        response_parts.append("")
    
    # Add encouraging next steps
    response_parts.append("**Next Steps:**")
    if contact_info.get("phones"):
        if any(urgent in q_lower for urgent in ['emergency', 'urgent', 'crisis']):
            response_parts.append("• Call the phone number above right away - they should be able to help you immediately")
        else:
            response_parts.append("• Give them a call - speaking directly with someone is often the quickest way to get started")
    elif contact_info.get("emails"):
        response_parts.append("• Send them an email with your specific questions - most organizations respond within 24-48 hours")
    elif contact_info.get("websites"):
        response_parts.append("• Check out their website for detailed information and applications")
    
    if len(providers) > 1:
        response_parts.append("• Don't hesitate to reach out to multiple providers - they may have different eligibility requirements")
    
    response_parts.append("• Remember, these organizations are here to help - don't hesitate to ask questions about their services")
    
    if any(urgent in q_lower for urgent in ['emergency', 'urgent', 'crisis']):
        response_parts.append("• If this is a life-threatening emergency, please call 911 immediately")
    
    return "\n".join(response_parts)

async def generate_answer(question: str, context_chunks: List[str]) -> Dict[str, Any]:
    """
    Generate structured answers using Ollama
    """
    # Generate response using Ollama
    answer_text = await generate_single_prompt_response(question, context_chunks)
    
    # Still extract structured data for API response
    chunk_categories = extract_categories_from_chunks(context_chunks) if context_chunks else []
    contact_info = extract_contact_info(context_chunks) if context_chunks else {}
    
    providers = []
    if context_chunks:
        for chunk in context_chunks:
            if "PROVIDER:" in chunk:
                provider = chunk.split("PROVIDER:")[1].split('\n')[0].strip()
                if provider and provider not in providers:
                    providers.append(provider)
    
    return {
        "answer": answer_text,
        "sources": context_chunks,
        "contact_info": contact_info,
        "categories": chunk_categories,
        "providers": providers
    }

def analyze_question_intent(question: str) -> dict:
    """Analyze question for intent, emotion, and context"""
    q = question.lower().strip()
    
    # Enhanced patterns with variations
    patterns = {
        'help_seeking': [
            r'\b(help|helping|helped)\b',
            r'\b(support|supporting|supported)\b', 
            r'\b(assist|assistance|assisting)\b',
            r'\b(need|needing|needed)\b',
            r'\bcan you\b',
            r'\bcould you\b',
            r"\bi'm looking for\b",
            r'\bwhere can i\b'
        ],
        'search_intent': [
            r'\b(find|finding|found)\b',
            r'\b(search|searching)\b',
            r'\b(look|looking)\b',
            r'\bwhere (is|are)\b',
            r'\bshow me\b',
            r'\blist\b'
        ],
        'urgency': [
            r'\b(urgent|emergency|crisis|immediate)\b',
            r'\b(asap|right now|today)\b',
            r'\b(desperate|struggling)\b'
        ],
        'gratitude': [
            r'\b(thank|thanks|grateful)\b',
            r'\bappreciate\b'
        ]
    }
    
    # Check patterns
    intent = {'primary': 'general', 'modifiers': []}
    
    for intent_type, pattern_list in patterns.items():
        if any(re.search(pattern, q) for pattern in pattern_list):
            if intent_type in ['help_seeking', 'search_intent']:
                intent['primary'] = intent_type
            else:
                intent['modifiers'].append(intent_type)
    
    return intent

def generate_contextual_intro(question: str, categories: List[str]) -> str:
    """Generate personality-rich contextual introduction"""
    intent = analyze_question_intent(question)
    
    # Handle urgency first
    if 'urgency' in intent['modifiers']:
        if categories:
            return f"I understand this is urgent. Let me quickly get you the {', '.join(categories).lower()} resources you need right away."
        return "I understand this is urgent. Here are the most relevant resources I found for your immediate needs."
    
    # Handle help-seeking with empathy
    if intent['primary'] == 'help_seeking':
        if 'gratitude' in intent['modifiers']:
            if categories:
                return f"You're very welcome! I'm happy to help you find {', '.join(categories).lower()} services that could work for your situation."
            return "You're very welcome! I'm glad I can help connect you with these resources."
        
        if categories:
            return f"I'd be happy to help you find {', '.join(categories).lower()} services. Here are some options that might work for your situation."
        return "I'd be happy to help! Here are some resources that might be helpful for your situation."
    
    # Handle search intent with enthusiasm  
    if intent['primary'] == 'search_intent':
        if categories:
            return f"Great question! I found several {', '.join(categories).lower()} options for you."
        return "Great question! Here's what I found that matches what you're looking for."
    
    # Enhanced fallback with warmth
    if categories:
        return f"Here's what I found related to {', '.join(categories).lower()} that should be helpful."
    return "Based on your question, here's the relevant information that should help."

def generate_next_steps(question: str, contact_info: Dict, providers: List[str]) -> str:
    """Generate helpful next steps with encouraging tone"""
    intent = analyze_question_intent(question)
    steps = []
    
    # Personality-rich guidance based on available contact methods
    if contact_info.get("phones"):
        if 'urgency' in intent['modifiers']:
            steps.append("Call the phone number above right away - they should be able to help you immediately")
        else:
            steps.append("Give them a call - speaking directly with someone is often the quickest way to get started")
    
    elif contact_info.get("emails"):
        steps.append("Send them an email with your specific questions - most organizations respond within 24-48 hours")
    
    elif contact_info.get("websites"):
        steps.append("Check out their website for detailed information and online applications")
    
    # Multiple providers guidance
    if len(providers) > 1:
        steps.append("Don't hesitate to reach out to multiple providers - different organizations may have different eligibility requirements or waitlists")
    
    # Emergency handling with care
    if 'urgency' in intent['modifiers']:
        steps.append("If this is a life-threatening emergency, please call 911 immediately")
    
    # Encouraging close
    if steps:
        steps.append("Remember, these organizations are here to help - don't hesitate to ask questions about their services")
    
    return "• " + "\n• ".join(steps) if steps else ""

def is_malformed_line(line: str) -> bool:
    """Check if a line contains malformed data that should be filtered out"""
    malformed_indicators = [
        '%22',  # URL encoded quotes
        '%2',   # Other URL encoding
        'field_specialty_ids',
        'geo_location=',
        'network_id=',
        'locale=en_us',
        '..67709152046795',  # Broken coordinates
        ',-117..',  # Broken coordinates
        'ci=wa-medicaid',
        'radius%22:%22',
        'sort%22:%22score',
    ]
    
    # Check for URL encoding or API parameters
    if any(indicator in line for indicator in malformed_indicators):
        return True
    
    # Check for lines that are mostly encoded characters
    encoded_chars = sum(1 for c in line if c in '%=&?')
    if len(line) > 0 and (encoded_chars / len(line)) > 0.3:
        return True
    
    # Check for lines with excessive dots or broken URLs
    if '..' in line and line.count('..') > 2:
        return True
        
    return False

def clean_text_content(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove URL encoded characters
    text = text.replace('%22', '"').replace('%20', ' ')
    
    # Fix broken URLs patterns
    text = re.sub(r'www\.\.\s*', 'www.', text)
    text = re.sub(r'https?://[^\s]*%[0-9A-F]{2}[^\s]*', '', text)
    
    # Remove malformed coordinate patterns
    text = re.sub(r'-?\d+\.\.\s*\d+', '', text)
    
    # Clean up multiple spaces and dots
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'\s{2,}', ' ', text)
    
    # Remove lines that are just fragments
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        if (len(line) > 10 and  # Minimum length
            not is_malformed_line(line) and
            not line.startswith('t%22:') and
            not line.startswith('field_')):
            clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()

def get_best_description(descriptions: List[str]) -> str:
    """Select the most readable and complete description"""
    if not descriptions:
        return ""
    
    # Score descriptions based on readability
    scored_descriptions = []
    for desc in descriptions:
        score = 0
        
        # Prefer longer descriptions
        score += len(desc) * 0.1
        
        # Prefer descriptions with proper sentences
        if '. ' in desc:
            score += 20
        
        # Prefer descriptions with actual words vs. technical content
        word_count = len([w for w in desc.split() if w.isalpha() and len(w) > 2])
        score += word_count * 0.5
        
        # Penalize descriptions with lots of technical/encoded content
        if '%' in desc or '&' in desc:
            score -= 30
        
        # Penalize descriptions that are mostly URLs or technical data
        if desc.count('http') > 2 or desc.count('www') > 3:
            score -= 20
            
        scored_descriptions.append((score, desc))
    
    # Return the highest scoring description
    scored_descriptions.sort(key=lambda x: x[0], reverse=True)
    return scored_descriptions[0][1] if scored_descriptions else descriptions[0]