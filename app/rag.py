from embedding import get_embedder
from db import engine
from sqlalchemy import text
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from categories import category_manager
import streamlit as st
import re

@st.cache_resource
def get_generator():
    """Lazy loading of text generation model with caching"""
    model_name = "google/flan-t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    device = "cpu"
    return pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        device=device,
        max_length=512
    )

def detect_category_in_query(query):
    """Detect potential aid categories in the query"""
    query_lower = query.lower()
    
    # Check for direct category mentions
    categories = []
    confidences = {}
    
    # Split query into words and check each word
    words = query_lower.split()
    
    # Check single words
    for word in words:
        if len(word) > 3:  # Skip very short words
            category, confidence = category_manager.normalize_category(word, threshold=0.7)
            if category and (category not in confidences or confidence > confidences[category]):
                categories.append(category)
                confidences[category] = confidence
    
    # Check bigrams
    for i in range(len(words) - 1):
        if len(words[i]) > 2 and len(words[i+1]) > 2:  # Skip very short words
            bigram = f"{words[i]} {words[i+1]}"
            category, confidence = category_manager.normalize_category(bigram, threshold=0.7)
            if category and (category not in confidences or confidence > confidences[category]):
                categories.append(category)
                confidences[category] = confidence
    
    # Return unique categories
    return list(set(categories))

@st.cache_data(ttl=1800)
def cached_embed_query(query):
    """Cache query embeddings for 30 minutes"""
    embedder = get_embedder()
    return embedder.encode([query], normalize_embeddings=True)[0].tolist()

def retrieve_relevant_chunks(query, tenant_id, top_k=4):
    """Retrieve provider information chunks with improved context and category awareness"""
    
    # Enhance the query for provider lookups
    original_query = query
    enhanced_query = query
    
    # Detect potential categories in the query
    detected_categories = detect_category_in_query(query)
    
    # If we detected specific categories, enhance the query
    if detected_categories:
        category_str = ", ".join(detected_categories)
        enhanced_query = f"{query} (categories: {category_str})"
    # If query is very short or might be looking for providers
    elif len(query) < 10 or any(term in query.lower() for term in ["provider", "find", "who", "recommend"]):
        # Create a provider-focused query
        enhanced_query = f"Provider information for {query}"
    
    # Get embeddings for the enhanced query
    query_emb = cached_embed_query(enhanced_query)
    
    try:
        with engine.connect() as conn:
            # First attempt - use the enhanced query with category awareness
            result = conn.execute(
                text("""
                    SELECT content
                    FROM embeddings
                    WHERE tenant_id = :tenant
                    ORDER BY embedding <-> (:query_emb)::vector
                    LIMIT :top_k
                """),
                {"tenant": tenant_id, "query_emb": query_emb, "top_k": top_k}
            )
            
            # Process chunks
            chunks = [row[0] for row in result]
            
            # Check for category headers in the results to identify normalized data
            has_normalized_data = any("CATEGORIES:" in chunk or "CONTACT INFORMATION:" in chunk for chunk in chunks)
            
            # If detected categories but didn't get good normalized results, try with category-specific query
            if detected_categories and not has_normalized_data:
                category_queries = []
                for category in detected_categories:
                    category_queries.append(f"Information about {category} services for {original_query}")
                
                # Get embeddings for each category query
                if category_queries:
                    cat_embs = [cached_embed_query(cq) for cq in category_queries]
                    cat_chunks = []
                    
                    # Query for each category embedding
                    for cat_emb in cat_embs:
                        cat_result = conn.execute(
                            text("""
                                SELECT content
                                FROM embeddings
                                WHERE tenant_id = :tenant
                                ORDER BY embedding <-> (:query_emb)::vector
                                LIMIT 2
                            """),
                            {"tenant": tenant_id, "query_emb": cat_emb, "top_k": 2}
                        )
                        cat_chunks.extend([row[0] for row in cat_result])
                    
                    # If we got meaningful results, combine with original
                    if cat_chunks:
                        # Deduplicate
                        unique_chunks = []
                        for chunk in cat_chunks:
                            if chunk not in chunks and chunk not in unique_chunks:
                                unique_chunks.append(chunk)
                        
                        # Combine results (original first, then category-specific)
                        combined_chunks = chunks + unique_chunks
                        # Limit to prevent context overload
                        chunks = combined_chunks[:top_k + 2]
            
            # If we still don't have much information, try the original query as fallback
            if len("".join(chunks)) < 100 and enhanced_query != original_query:
                orig_emb = cached_embed_query(original_query)
                result = conn.execute(
                    text("""
                        SELECT content
                        FROM embeddings
                        WHERE tenant_id = :tenant
                        ORDER BY embedding <-> (:query_emb)::vector
                        LIMIT :top_k
                    """),
                    {"tenant": tenant_id, "query_emb": orig_emb, "top_k": top_k}
                )
                orig_chunks = [row[0] for row in result]
                if len("".join(orig_chunks)) > len("".join(chunks)):
                    chunks = orig_chunks
                    
            return chunks
    except Exception as e:
        print(f"Error retrieving chunks: {str(e)}")
        return []

def extract_contact_info(context_chunks):
    """Extract contact information from context chunks"""
    contact_info = {
        "emails": [],
        "phones": [],
        "websites": [],
        "addresses": []
    }
    
    # Regular expressions for contact information
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(\(\d{3}\)\s*|\d{3}[-.])\d{3}[-.]?\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    
    # Look for normalized sections first
    for chunk in context_chunks:
        if "CONTACT INFORMATION:" in chunk:
            # Extract information from structured data
            lines = chunk.split('\n')
            for i, line in enumerate(lines):
                if "Email:" in line:
                    contact_info["emails"].extend(re.findall(email_pattern, line))
                elif "Phone:" in line:
                    contact_info["phones"].extend(re.findall(phone_pattern, line))
                elif "Website:" in line or "URL:" in line:
                    contact_info["websites"].extend(re.findall(url_pattern, line))
                elif "Address:" in line and i+1 < len(lines):
                    # Address might span multiple lines
                    contact_info["addresses"].append(lines[i].replace("Address:", "").strip())
                    if i+1 < len(lines) and not any(k in lines[i+1] for k in ["Email:", "Phone:", "Website:", "DESCRIPTION:"]):
                        contact_info["addresses"].append(lines[i+1].strip())
    
    # If structured data wasn't found, extract from raw text
    if not any(contact_info.values()):
        for chunk in context_chunks:
            contact_info["emails"].extend(re.findall(email_pattern, chunk))
            contact_info["phones"].extend(re.findall(phone_pattern, chunk))
            contact_info["websites"].extend(re.findall(url_pattern, chunk))
    
    # Deduplicate
    for key in contact_info:
        contact_info[key] = list(set(contact_info[key]))
    
    return contact_info

def extract_categories_from_chunks(chunks):
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

def generate_answer(question, context_chunks):
    """Generate structured answers for provider inquiries"""
    
    if not context_chunks:
        return "No provider information found for this query."
    
    # Extract structured data
    question_categories = detect_category_in_query(question)
    chunk_categories = extract_categories_from_chunks(context_chunks)
    contact_info = extract_contact_info(context_chunks)
    
    # Combine categories
    all_categories = list(set(question_categories + chunk_categories))
    
    # Build structured response
    response_parts = []
    
    # Add relevant categories
    if all_categories:
        response_parts.append(f"**Categories:** {', '.join(all_categories)}")
        response_parts.append("")
    
    # Add contact information
    if any(contact_info.values()):
        response_parts.append("**Contact Information:**")
        
        if contact_info["emails"]:
            response_parts.append(f"• Email: {', '.join(contact_info['emails'])}")
        
        if contact_info["phones"]:
            response_parts.append(f"• Phone: {', '.join(contact_info['phones'])}")
        
        if contact_info["websites"]:
            response_parts.append(f"• Website: {', '.join(contact_info['websites'])}")
        
        if contact_info["addresses"]:
            response_parts.append(f"• Address: {contact_info['addresses'][0]}")
        
        response_parts.append("")
    
    # Add provider information
    providers = []
    for chunk in context_chunks:
        if "PROVIDER:" in chunk:
            provider = chunk.split("PROVIDER:")[1].split('\n')[0].strip()
            if provider and provider not in providers:
                providers.append(provider)
    
    if providers:
        response_parts.append("**Provider(s):**")
        response_parts.append(f"• {', '.join(providers)}")
        response_parts.append("")
    
    # Add description from chunks
    descriptions = []
    for chunk in context_chunks:
        if "DESCRIPTION:" in chunk:
            desc = chunk.split("DESCRIPTION:")[1].strip()
            descriptions.append(desc)
        else:
            # Clean chunk content
            lines = [line.strip() for line in chunk.split('\n') 
                    if line.strip() and not any(h in line for h in ["CATEGORIES:", "CONTACT INFORMATION:", "PROVIDER:"])]
            if lines:
                descriptions.append(' '.join(lines))
    
    if descriptions:
        response_parts.append("**Description:**")
        response_parts.append(descriptions[0][:200] + "..." if len(descriptions[0]) > 200 else descriptions[0])
    
    return "\n".join(response_parts)
