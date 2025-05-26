from embedding import embedder
from db import engine
from sqlalchemy import text
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from categories import category_manager
import re

# Use a smaller model and explicit tokenizer to better handle context length
model_name = "google/flan-t5-small"  # Use smaller model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Simple pipeline with HuggingFace
device = "cpu"  # Use CPU to avoid CUDA issues
generator = pipeline(
    "text2text-generation",  # Use text2text instead of text-generation
    model=model,
    tokenizer=tokenizer,
    device=device,
    max_length=100  # Set default max length
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
    query_emb = embedder.encode([enhanced_query], normalize_embeddings=True)[0].tolist()
    
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
                    cat_embs = embedder.encode(category_queries, normalize_embeddings=True)
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
                            {"tenant": tenant_id, "query_emb": cat_emb.tolist(), "top_k": 2}
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
                orig_emb = embedder.encode([original_query], normalize_embeddings=True)[0].tolist()
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
    """Generate informative answers for provider inquiries using structured data awareness"""
    
    # Check if we have any context
    if not context_chunks:
        return "No provider information found for this query."
    
    # Extract categories from the question
    question_categories = detect_category_in_query(question)
    
    # Extract categories from the chunks
    chunk_categories = extract_categories_from_chunks(context_chunks)
    
    # Combine categories (question categories first, then chunk categories)
    all_categories = []
    all_categories.extend(question_categories)
    for cat in chunk_categories:
        if cat not in all_categories:
            all_categories.append(cat)
    
    # Extract contact information
    contact_info = extract_contact_info(context_chunks)
    
    # Format context with more details
    formatted_context = " ".join(context_chunks)
    
    # Create category-aware prompt
    category_str = ""
    if all_categories:
        category_str = f"The information is about the following categories: {', '.join(all_categories)}.\n"
    
    # Add contact information to prompt if available
    contact_str = ""
    if any(contact_info.values()):
        contact_str = "The information contains the following contact details:\n"
        
        if contact_info["emails"]:
            contact_str += f"- Emails: {', '.join(contact_info['emails'])}\n"
        
        if contact_info["phones"]:
            contact_str += f"- Phone numbers: {', '.join(contact_info['phones'])}\n"
        
        if contact_info["websites"]:
            contact_str += f"- Websites: {', '.join(contact_info['websites'])}\n"
        
        if contact_info["addresses"]:
            contact_str += f"- Addresses: {'; '.join(contact_info['addresses'])}\n"
    
    # Create an enhanced prompt with structured awareness
    prompt = f"""
    Answer this question: {question}
    
    {category_str}
    {contact_str}
    
    Use only this information:
    {formatted_context}
    
    If the information contains provider details relevant to the question, include the provider names and contact details in your answer.
    Format any contact information clearly and make it easy to read.
    Do not ask follow-up questions. Simply provide the most relevant information you can find.
    """

    try:
        # Increase max length to allow for provider details
        response = generator(
            prompt,
            max_length=250,  # Longer for provider listings
            num_return_sequences=1,
            do_sample=False
        )
        
        # Get response text
        answer_text = response[0]['generated_text'].strip()
        
        # Check for follow-up questions or very short answers
        if "what is" in answer_text.lower() or "who is" in answer_text.lower() or len(answer_text) < 15:
            # Create a structured response from the raw context
            response_parts = []
            
            # Add categories if available
            if all_categories:
                response_parts.append(f"Categories: {', '.join(all_categories)}")
                response_parts.append("")  # Empty line
            
            # Add contact information if available
            if any(contact_info.values()):
                response_parts.append("Contact Information:")
                
                if contact_info["emails"]:
                    response_parts.append(f"Email: {', '.join(contact_info['emails'])}")
                
                if contact_info["phones"]:
                    response_parts.append(f"Phone: {', '.join(contact_info['phones'])}")
                
                if contact_info["websites"]:
                    response_parts.append(f"Website: {', '.join(contact_info['websites'])}")
                
                if contact_info["addresses"]:
                    response_parts.append(f"Address: {'; '.join(contact_info['addresses'])}")
                
                response_parts.append("")  # Empty line
            
            # Format the context into a clean response
            response_parts.append("Description:")
            for chunk in context_chunks:
                # Extract description sections from normalized data
                if "DESCRIPTION:" in chunk:
                    desc_start = chunk.find("DESCRIPTION:")
                    description = chunk[desc_start:].replace("DESCRIPTION:", "").strip()
                    response_parts.append(description)
                else:
                    # For non-normalized data, just add the content
                    lines = chunk.split('\n')
                    for line in lines:
                        if line.strip() and not any(header in line for header in ["CATEGORIES:", "CONTACT INFORMATION:"]):
                            response_parts.append(line.strip())
            
            # Join with line breaks for readability
            structured_response = "\n".join(response_parts)
            return structured_response
            
        return answer_text
        
    except Exception as e:
        print(f"Error in generate_answer: {str(e)}")
        # Provide raw context as fallback
        return "\n".join([chunk for chunk in context_chunks])
