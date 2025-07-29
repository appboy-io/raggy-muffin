from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.embedding import embed_query_async
from app.models import Embedding
# from app.cache import cached
from typing import List, Dict, Any
import logging
import re
import hashlib

logger = logging.getLogger(__name__)

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
    try:
        # Get query embedding
        query_embedding = await embed_query_async(query)
        
        # Perform optimized vector similarity search with similarity threshold
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

def generate_answer(question: str, context_chunks: List[str]) -> Dict[str, Any]:
    """
    Generate structured answers for provider inquiries with helpful context
    """
    if not context_chunks:
        return {
            "answer": "I couldn't find any specific information related to your question in the available documents. You might want to try rephrasing your question or asking about a different topic that's covered in the uploaded resources.",
            "sources": [],
            "contact_info": {},
            "categories": [],
            "providers": []
        }
    
    # Extract structured data
    chunk_categories = extract_categories_from_chunks(context_chunks)
    contact_info = extract_contact_info(context_chunks)
    
    # Analyze the question to provide contextual introduction
    question_lower = question.lower()
    context_intro = generate_contextual_intro(question_lower, chunk_categories)
    
    # Build structured response
    response_parts = []
    
    # Add contextual introduction
    if context_intro:
        response_parts.append(context_intro)
        response_parts.append("")
    
    # Add relevant categories with context
    if chunk_categories:
        if len(chunk_categories) == 1:
            response_parts.append(f"**Service Category:** {chunk_categories[0]}")
        else:
            response_parts.append(f"**Related Categories:** {', '.join(chunk_categories)}")
        response_parts.append("")
    
    # Add provider information first (more relevant)
    providers = []
    for chunk in context_chunks:
        if "PROVIDER:" in chunk:
            provider = chunk.split("PROVIDER:")[1].split('\n')[0].strip()
            if provider and provider not in providers:
                providers.append(provider)
    
    if providers:
        if len(providers) == 1:
            response_parts.append("**Available Provider:**")
        else:
            response_parts.append(f"**Available Providers ({len(providers)} found):**")
        for provider in providers[:5]:  # Limit to 5 providers
            response_parts.append(f"• {provider}")
        if len(providers) > 5:
            response_parts.append(f"• ...and {len(providers) - 5} more providers")
        response_parts.append("")
    
    # Add description with better formatting and cleaning
    descriptions = []
    for chunk in context_chunks:
        if "DESCRIPTION:" in chunk:
            desc = chunk.split("DESCRIPTION:")[1].strip()
            cleaned_desc = clean_text_content(desc)
            if cleaned_desc:
                descriptions.append(cleaned_desc)
        else:
            # Clean chunk content
            lines = []
            for line in chunk.split('\n'):
                line = line.strip()
                # Skip malformed lines and headers
                if (line and 
                    not any(h in line for h in ["CATEGORIES:", "CONTACT INFORMATION:", "PROVIDER:"]) and
                    not is_malformed_line(line)):
                    lines.append(line)
            
            if lines:
                cleaned_content = clean_text_content(' '.join(lines))
                if cleaned_content:
                    descriptions.append(cleaned_content)
    
    if descriptions:
        response_parts.append("**About This Service:**")
        # Use the most readable description
        best_desc = get_best_description(descriptions)
        if len(best_desc) > 300:
            # Find a good breaking point
            break_point = best_desc.find('. ', 200)
            if break_point > 0:
                response_parts.append(best_desc[:break_point + 1])
            else:
                response_parts.append(best_desc[:300] + "...")
        else:
            response_parts.append(best_desc)
        response_parts.append("")
    
    # Add contact information with helpful context
    if any(contact_info.values()):
        response_parts.append("**How to Get Started:**")
        
        # Only show contact info if we have valid data
        if contact_info["phones"] and len(contact_info["phones"]) <= 3:
            for phone in contact_info["phones"]:
                response_parts.append(f"• Call: {phone}")
        
        if contact_info["emails"] and len(contact_info["emails"]) <= 3:
            for email in contact_info["emails"]:
                response_parts.append(f"• Email: {email}")
        
        if contact_info["websites"] and len(contact_info["websites"]) <= 3:
            for website in contact_info["websites"]:
                response_parts.append(f"• Visit: {website}")
        
        if contact_info["addresses"]:
            response_parts.append(f"• Location: {contact_info['addresses'][0]}")
        
        response_parts.append("")
    else:
        # If no clean contact info found, provide general guidance
        response_parts.append("**How to Get Started:**")
        response_parts.append("• Contact the providers listed above for more information")
        response_parts.append("• Check the documents for specific contact details")
        response_parts.append("")
    
    # Add helpful next steps
    next_steps = generate_next_steps(question_lower, contact_info, providers)
    if next_steps:
        response_parts.append("**Next Steps:**")
        response_parts.append(next_steps)
    
    answer_text = "\n".join(response_parts)
    
    return {
        "answer": answer_text,
        "sources": context_chunks,
        "contact_info": contact_info,
        "categories": chunk_categories,
        "providers": providers
    }

def generate_contextual_intro(question: str, categories: List[str]) -> str:
    """Generate a contextual introduction based on the question"""
    if any(word in question for word in ['help', 'support', 'assistance', 'need']):
        if categories:
            return f"I found some resources that might help you with {', '.join(categories).lower()} services."
        return "I found some resources that might be helpful for your situation."
    
    elif any(word in question for word in ['find', 'looking for', 'search']):
        if categories:
            return f"Here's what I found related to {', '.join(categories).lower()}:"
        return "Here's what I found based on your search:"
    
    elif any(word in question for word in ['services', 'programs', 'resources']):
        return "Based on the available resources, here are the relevant services:"
    
    elif any(word in question for word in ['contact', 'call', 'reach']):
        return "Here's the contact information for the services you're looking for:"
    
    return "Based on your question, here's the relevant information:"

def generate_next_steps(question: str, contact_info: Dict, providers: List[str]) -> str:
    """Generate helpful next steps for the user"""
    steps = []
    
    if contact_info.get("phones"):
        steps.append("Call the phone number above to speak with someone directly")
    elif contact_info.get("emails"):
        steps.append("Send an email to inquire about services and availability")
    elif contact_info.get("websites"):
        steps.append("Visit their website for more information and to get started")
    
    if len(providers) > 1:
        steps.append("Compare the different providers to find the best fit for your needs")
    
    if any(word in question for word in ['emergency', 'urgent', 'crisis']):
        steps.append("If this is an emergency, please call 911 or go to your nearest emergency room")
    
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