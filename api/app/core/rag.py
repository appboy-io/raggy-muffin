from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.embedding import embed_query_async
from app.models import Embedding, AgentConfig
# from app.cache import cached
from typing import List, Dict, Any, Tuple
import logging
import re
import json
import hashlib
import ollama
import os
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

def extract_location_from_query(query: str) -> List[str]:
    """
    Extract any location-like terms from user query using pattern matching.
    Works for any location without hard-coding specific places.
    Returns list of potential location terms found.
    """
    query_lower = query.lower()
    locations = []
    
    # Pattern 1: "County" mentions (e.g., "Spokane County", "Pierce County")
    # Be more specific to avoid capturing prepositions
    county_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County\b'
    county_matches = re.findall(county_pattern, query)
    for match in county_matches:
        locations.append(match.lower())
        locations.append(f"{match.lower()} county")
    
    # Pattern 2: Location indicators - look for proper nouns after location prepositions
    # Extract just the location name, not the preposition
    # Updated to handle directional terms like "Eastern Washington"
    location_patterns = [
        r'\blives in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
        r'\bnear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
        r'\baround\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
        r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
        r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
        r'\bnearby\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+County)?)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, query)
        for match in matches:
            # Clean and validate the match
            clean_match = match.strip()
            if (clean_match and 
                clean_match[0].isupper() and  # Must start with capital
                clean_match.lower() not in ['the', 'a', 'an', 'this', 'that', 'medicaid', 'medicare'] and
                not clean_match.lower() in locations):  # Avoid duplicates
                locations.append(clean_match.lower())
    
    # Pattern 3: State abbreviations (e.g., "WA", "OR", "CA")
    state_pattern = r'\b([A-Z]{2})\b'
    state_matches = re.findall(state_pattern, query)
    for match in state_matches:
        # Basic check for likely state abbreviations (all caps, 2 letters)
        if match not in ['IN', 'AT', 'TO', 'OF', 'BY', 'OR', 'AN', 'AS', 'IF', 'IS', 'IT', 'NO', 'OK', 'SO', 'UP', 'US', 'WE', 'MY']:
            locations.append(match)
    
    # Pattern 4: City + State patterns (e.g., "Seattle, WA")
    city_state_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b'
    city_state_matches = re.findall(city_state_pattern, query, re.IGNORECASE)
    for city, state in city_state_matches:
        locations.append(city.lower())
        locations.append(state.upper())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locations = []
    for loc in locations:
        if loc not in seen:
            seen.add(loc)
            unique_locations.append(loc)
    
    if unique_locations:
        logger.error(f"DEBUG: Extracted locations from query: {unique_locations}")
    
    return unique_locations

def detect_locations_in_chunk(chunk: str) -> List[str]:
    """
    Detect any location mentions in a chunk using pattern matching.
    Works for any location without hard-coding specific places.
    Returns list of location terms found.
    """
    chunk_lower = chunk.lower()
    locations = []
    
    # Pattern 1: County mentions
    county_pattern = r'\b([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+County\b'
    county_matches = re.findall(county_pattern, chunk, re.IGNORECASE)
    for match in county_matches:
        locations.append(match.lower())
        locations.append(f"{match.lower()} county")
    
    # Pattern 2: Look for "City:" or "County:" or "Location:" labels
    label_patterns = [
        r'City:\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)',
        r'County:\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)',
        r'Location:\s*([A-Za-z]+(?:\s+[A-Za-z]+]*)*)',
        r'Address:.*?\b([A-Za-z]+(?:\s+[A-Za-z]+)*),\s*[A-Z]{2}\b',  # Extract city from addresses
    ]
    
    for pattern in label_patterns:
        matches = re.findall(pattern, chunk, re.IGNORECASE)
        for match in matches:
            if match.lower() not in ['not specified', 'n/a', 'none', 'unknown', 'various', 'multiple']:
                locations.append(match.lower())
    
    # Pattern 3: State abbreviations in addresses (e.g., "Tacoma, WA 98402")
    address_pattern = r'\b([A-Za-z]+(?:\s+[A-Za-z]+)*),\s*([A-Z]{2})\s+\d{5}'
    address_matches = re.findall(address_pattern, chunk)
    for city, state in address_matches:
        locations.append(city.lower())
    
    # Pattern 4: Look for specific location indicators in structured data
    # This catches things like "Tacoma" or "Spokane" when they appear as standalone values
    if any(indicator in chunk for indicator in ['City', 'County', 'Location', 'Address', 'Physical Address']):
        # Extract potential city names that appear after colons or in quotes
        standalone_pattern = r'["\']([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)["\']|:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        standalone_matches = re.findall(standalone_pattern, chunk)
        for match_tuple in standalone_matches:
            for match in match_tuple:
                if match and len(match) > 2 and match.lower() not in ['not specified', 'n/a', 'none', 'unknown']:
                    locations.append(match.lower())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locations = []
    for loc in locations:
        if loc and loc not in seen:
            seen.add(loc)
            unique_locations.append(loc)
    
    return unique_locations

def filter_chunks_by_location(
    chunks: List[str], 
    similarities: List[float],
    requested_locations: List[str]
) -> List[Tuple[str, float]]:
    """
    Filter chunks to only include those matching any of the requested locations.
    Uses flexible string matching without hard-coding specific locations.
    Returns list of (chunk, similarity) tuples.
    """
    if not requested_locations:
        # No location filter needed
        return list(zip(chunks, similarities))
    
    filtered_results = []
    
    logger.info(f"Filtering chunks for locations: {requested_locations}")
    
    for i, chunk in enumerate(chunks):
        chunk_locations = detect_locations_in_chunk(chunk)
        
        # Check if any detected location matches any requested location
        location_match = False
        
        for requested_loc in requested_locations:
            requested_lower = requested_loc.lower()
            
            for detected_loc in chunk_locations:
                detected_lower = detected_loc.lower()
                
                # Flexible matching: exact match or contains
                if (requested_lower == detected_lower or 
                    requested_lower in detected_lower or 
                    detected_lower in requested_lower):
                    location_match = True
                    logger.debug(f"Chunk {i} matches: '{detected_loc}' ~ '{requested_loc}'")
                    break
            
            if location_match:
                break
        
        if location_match:
            filtered_results.append((chunk, similarities[i]))
        else:
            # Log what was filtered out
            if chunk_locations:
                logger.debug(f"Chunk {i} filtered out - found: {chunk_locations[:3]}, requested: {requested_locations}")
            else:
                logger.debug(f"Chunk {i} filtered out - no locations detected")
    
    logger.info(f"Geographic filtering: {len(chunks)} chunks → {len(filtered_results)} chunks")
    
    # Sort by similarity score (highest first)
    filtered_results.sort(key=lambda x: x[1], reverse=True)
    
    return filtered_results

def get_chat_model():
    """Get the chat model name from environment"""
    return os.getenv('OLLAMA_CHAT_MODEL', 'mistral:7b-instruct-q4_0')

def get_ollama_host():
    """Get Ollama host from environment"""
    return os.getenv('OLLAMA_HOST', 'http://localhost:11434')

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    Returns a value between -1 and 1, where 1 means identical direction
    """
    try:
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

async def apply_semantic_category_filtering(query: str, chunks: List[str], similarities: List[float], relevance_threshold: float = 0.3) -> List[tuple]:
    """Filter out chunks with categories that don't semantically match the query intent"""
    
    # Get query embedding for category matching
    query_embedding = await embed_query_async(query)
    relevant_results = []
    
    logger.info(f"Applying semantic category filtering for query: {query}")
    
    for i, chunk in enumerate(chunks):
        current_score = similarities[i]
        
        # Extract categories from chunk  
        categories = await extract_categories_from_chunks([chunk])
        logger.error(f"DEBUG CATEGORIES for chunk {i}: {categories}")
        
        # Check if any category is semantically relevant to the query
        is_relevant = False
        best_category_similarity = 0.0
        best_category = ""
        
        for category in categories:
            if category and len(category.strip()) > 2:  # Skip empty/short categories
                # Create category-focused text for embedding
                category_text = f"business service category: {category}"
                try:
                    category_embedding = await embed_query_async(category_text)
                    similarity = cosine_similarity(query_embedding, category_embedding)
                    
                    if similarity > best_category_similarity:
                        best_category_similarity = similarity
                        best_category = category
                    
                    # If any category is semantically relevant, include this chunk
                    if similarity >= relevance_threshold:
                        is_relevant = True
                        
                except Exception as e:
                    logger.warning(f"Error processing category '{category}': {e}")
                    continue
        
        # Include chunk if categories are relevant OR if no categories found (fallback)
        if is_relevant or not categories:
            relevant_results.append((chunk, current_score))
            if best_category:
                logger.info(f"INCLUDED - Category: '{best_category}' similarity: {best_category_similarity:.3f}")
        else:
            logger.info(f"FILTERED OUT - Category: '{best_category}' similarity: {best_category_similarity:.3f} (below {relevance_threshold})")
    
    # Sort by original similarity scores
    relevant_results.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"Category filtering complete: {len(chunks)} → {len(relevant_results)} chunks")
    
    return relevant_results

def split_into_sections(chunk: str, max_section_length: int = 500) -> List[str]:
    """
    Split a text chunk into semantic sections based on structure
    Returns list of text sections that are semantically coherent
    """
    sections = []
    
    # First, check for structured data markers
    if "PROVIDER:" in chunk or "DESCRIPTION:" in chunk or "CONTACT INFORMATION:" in chunk:
        # Split by major sections
        lines = chunk.split('\n')
        current_section = []
        current_header = ""
        
        for line in lines:
            if any(marker in line for marker in ["PROVIDER:", "DESCRIPTION:", "CATEGORIES:", "CONTACT INFORMATION:"]):
                # Save previous section if it exists
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text and len(section_text) > 20:
                        sections.append(section_text)
                # Start new section
                current_header = line
                current_section = [line]
            else:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text and len(section_text) > 20:
                sections.append(section_text)
    
    # If no structured markers, split by paragraphs and bullet points
    if not sections:
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', chunk)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if this paragraph has bullet points
            if '•' in para or re.search(r'^\s*[-*]\s', para, re.MULTILINE):
                # Split bullet points into individual items
                bullet_pattern = r'(?:^|\n)\s*[•\-*]\s*'
                bullets = re.split(bullet_pattern, para)
                
                for bullet in bullets:
                    bullet = bullet.strip()
                    if bullet and len(bullet) > 20:
                        # Group small bullets together, keep large ones separate
                        if len(bullet) < 150 and sections and len(sections[-1]) < max_section_length:
                            sections[-1] = sections[-1] + "\n• " + bullet
                        else:
                            sections.append("• " + bullet)
            else:
                # Regular paragraph - split if too long
                if len(para) > max_section_length:
                    # Split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    current_section = ""
                    
                    for sentence in sentences:
                        if len(current_section) + len(sentence) < max_section_length:
                            current_section += " " + sentence if current_section else sentence
                        else:
                            if current_section:
                                sections.append(current_section.strip())
                            current_section = sentence
                    
                    if current_section:
                        sections.append(current_section.strip())
                else:
                    sections.append(para)
    
    # Filter out very short or empty sections
    sections = [s for s in sections if s and len(s.strip()) > 20]
    
    return sections

async def filter_context_by_semantic_relevance(
    query: str, 
    chunks: List[str], 
    threshold: float = 0.3,
    max_sections: int = 5
) -> List[str]:
    """
    Filter context chunks based on semantic relevance to the query
    Returns only the most relevant sections from the chunks
    
    Args:
        query: The user's query
        chunks: List of text chunks from vector search
        threshold: Minimum cosine similarity to include a section (0.0 to 1.0)
        max_sections: Maximum number of sections to return
    
    Returns:
        List of relevant text sections
    """
    if not chunks:
        return []
    
    try:
        # Get query embedding
        query_embedding = await embed_query_async(query)
        
        # Store sections with their relevance scores
        scored_sections = []
        
        for chunk in chunks:
            # Split chunk into semantic sections
            sections = split_into_sections(chunk)
            
            for section in sections:
                # Skip if section is too short
                if len(section) < 30:
                    continue
                
                # Get embedding for first part of section (to save computation)
                section_preview = section[:300] if len(section) > 300 else section
                section_embedding = await embed_query_async(section_preview)
                
                # Calculate semantic similarity
                similarity = cosine_similarity(query_embedding, section_embedding)
                
                # Only keep sections above threshold
                if similarity >= threshold:
                    scored_sections.append((similarity, section))
                    logger.debug(f"Section similarity: {similarity:.3f} for: {section[:100]}...")
        
        # Sort by relevance score (highest first)
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        # Return top sections
        relevant_sections = [section for score, section in scored_sections[:max_sections]]
        
        logger.info(f"Semantic filtering: {len(chunks)} chunks → {len(sections)} sections → {len(relevant_sections)} relevant")
        logger.info(f"Relevance scores: {[f'{score:.3f}' for score, _ in scored_sections[:3]]}")
        
        return relevant_sections
        
    except Exception as e:
        logger.error(f"Error in semantic relevance filtering: {e}")
        # Fallback to returning original chunks if filtering fails
        return chunks[:3]

# @cached(key_prefix="rag_chunks", ttl=1800)  # Cache for 30 minutes
async def retrieve_relevant_chunks(
    query: str, 
    tenant_id: str, 
    db: Session, 
    top_k: int = 4,
    similarity_threshold: float = -0.5,
    use_semantic_filter: bool = True,
    semantic_threshold: float = 0.15
) -> tuple[List[str], List[float]]:
    """
    Retrieve relevant chunks using vector similarity search with optional semantic filtering
    Returns chunks and their similarity scores
    
    Args:
        query: The user's query
        tenant_id: The tenant identifier
        db: Database session
        top_k: Number of chunks to retrieve initially
        similarity_threshold: Minimum vector similarity score
        use_semantic_filter: Whether to apply semantic relevance filtering
        semantic_threshold: Minimum cosine similarity for semantic filter
    """
    logger.error(f"retrieve_relevant_chunks called with query='{query}', tenant_id='{tenant_id}'")
    logger.error(f"DEBUG: ENTERING retrieve_relevant_chunks function - NEW CODE VERSION")
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
        
        # Perform vector similarity search with threshold
        # Retrieve more chunks initially if semantic filtering is enabled
        initial_top_k = top_k * 2 if use_semantic_filter else top_k
        
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
                "top_k": initial_top_k
            }
        )
        
        rows = result.fetchall()
        
        # Debug logging: show all similarity scores before filtering
        logger.error(f"DEBUG: Raw similarity scores for all {len(rows)} chunks:")
        for i, row in enumerate(rows):
            chunk_preview = row[0][:100].replace('\n', ' ')
            logger.error(f"  Chunk {i}: Score {row[1]:.4f} - {chunk_preview}...")
        
        # Adaptive similarity threshold based on content relevance
        # Check if any chunks contain terms from the query
        query_terms = set(query.lower().split())
        
        # Extract key terms that might indicate specific requirements 
        key_terms = []
        for term in query_terms:
            if len(term) > 3 and term not in ['this', 'that', 'they', 'with', 'which', 'where', 'what', 'when', 'asked', 'client', 'supports']:
                key_terms.append(term.lower())
        
        # Add specific medical/service terms to look for
        medical_terms = ['vbac', 'tolac', 'midwife', 'midwives', 'birth', 'delivery', 'obstetric', 'prenatal']
        
        # Check if any chunks contain relevant key terms or medical terms
        has_relevant_content = False
        if key_terms or medical_terms:
            for i, row in enumerate(rows):
                chunk_text = row[0].lower()
                # Check both query terms and medical terms
                all_terms = key_terms + medical_terms
                for term in all_terms:
                    if term in chunk_text:
                        has_relevant_content = True
                        logger.error(f"DEBUG: Found relevant term '{term}' in chunk {i} (score {row[1]:.4f})")
                        break
                if has_relevant_content:
                    break
        
        # Use adaptive threshold: stricter when no relevant content, much more lenient when relevant content exists
        adaptive_threshold = similarity_threshold if not has_relevant_content else -2.0
        
        logger.info(f"Adaptive threshold: {adaptive_threshold} (has_relevant_content: {has_relevant_content})")
        
        # Filter by adaptive similarity threshold  
        filtered_results = [(row[0], row[1]) for row in rows if row[1] >= adaptive_threshold]
        logger.error(f"DEBUG: After threshold filtering ({adaptive_threshold}): {len(filtered_results)} chunks")
        
        chunks = [result[0] for result in filtered_results]
        similarities = [result[1] for result in filtered_results]
        
        # Apply semantic category filtering to exclude irrelevant business types
        logger.error(f"DEBUG: About to apply semantic category filtering to {len(chunks)} chunks")
        filtered_results = await apply_semantic_category_filtering(query, chunks, similarities)
        chunks = [result[0] for result in filtered_results]
        similarities = [result[1] for result in filtered_results]
        logger.error(f"DEBUG: After category filtering, have {len(chunks)} chunks")
        
        # Apply geographic filtering if location is mentioned in query
        requested_locations = extract_location_from_query(query)
        if requested_locations:
            logger.error(f"DEBUG: Applying geographic filtering for locations: {requested_locations}")
            filtered_results = filter_chunks_by_location(chunks, similarities, requested_locations)
            chunks = [result[0] for result in filtered_results]
            similarities = [result[1] for result in filtered_results]
            logger.error(f"DEBUG: After geographic filtering: {len(chunks)} chunks remain")
        
        # Debug logging before semantic filtering
        logger.error(f"Query: '{query}' for tenant: {tenant_id}")
        logger.error(f"Found {len(rows)} total chunks, {len(chunks)} above threshold {adaptive_threshold} (adaptive threshold applied)")
        if similarities:
            logger.error(f"Initial similarity scores: {[f'{s:.3f}' for s in similarities[:3]]}")
        
        # Apply semantic relevance filtering if enabled
        if use_semantic_filter and chunks:
            logger.info(f"Applying semantic relevance filtering to {len(chunks)} chunks")
            
            # Filter chunks by semantic relevance
            filtered_sections = await filter_context_by_semantic_relevance(
                query=query,
                chunks=chunks,
                threshold=semantic_threshold,
                max_sections=top_k  # Return up to top_k sections
            )
            
            # If we got filtered results, use them
            if filtered_sections:
                # For now, we'll return the filtered sections as chunks
                # and create synthetic similarity scores based on order
                chunks = filtered_sections
                # Create decreasing similarity scores for filtered results
                similarities = [0.9 - (i * 0.1) for i in range(len(filtered_sections))]
                
                logger.info(f"After semantic filtering: {len(chunks)} relevant sections")
            else:
                logger.warning("Semantic filtering returned no results, using original chunks")
                # Fall back to original chunks but limit to top_k
                chunks = chunks[:top_k]
                similarities = similarities[:top_k]
        
        # Log first chunk content to see what's being matched
        if chunks:
            logger.error(f"Best match content (first 200 chars): {chunks[0][:200]}...")
        
        return chunks, similarities
        
    except Exception as e:
        logger.error(f"Error retrieving chunks: {e}")
        return [], []


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
    """Extract contact information maintaining organization associations"""
    # This function now returns structured contact info that preserves organization associations
    contact_info = {
        "emails": [],
        "phones": [],
        "websites": [],
        "addresses": []
    }
    
    # Regular expressions for contact information
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(?:\(\d{3}\)\s*|\d{3}[-.\s]?)?\d{3}[-.\s]?\d{4}\b'
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;!?]'
    
    # Look for structured chunks with "CONTACT INFORMATION:" sections
    for chunk in context_chunks:
        if "CONTACT INFORMATION:" in chunk:
            lines = chunk.split('\n')
            for i, line in enumerate(lines):
                if "Email:" in line:
                    emails = re.findall(email_pattern, line)
                    contact_info["emails"].extend(emails)
                elif "Phone:" in line:
                    phones = re.findall(phone_pattern, line)
                    valid_phones = [p for p in phones if len(re.sub(r'[^\d]', '', p)) == 10]
                    contact_info["phones"].extend(valid_phones)
                elif "Website:" in line or "URL:" in line:
                    urls = re.findall(url_pattern, line)
                    valid_urls = [url for url in urls if '.' in url and not url.endswith('..')]
                    contact_info["websites"].extend(valid_urls)
                elif "Address:" in line:
                    address = line.replace("Address:", "").strip()
                    if address:
                        contact_info["addresses"].append(address)
    
    # Deduplicate and clean
    for key in contact_info:
        contact_info[key] = list(set([item for item in contact_info[key] if item and item.strip()]))
    
    # Return only properly structured contact info (no orphaned numbers)
    contact_info["emails"] = contact_info["emails"][:10]
    contact_info["phones"] = contact_info["phones"][:10] 
    contact_info["websites"] = contact_info["websites"][:10]
    contact_info["addresses"] = contact_info["addresses"][:5]
    
    return contact_info

def extract_structured_providers(context_chunks: List[str]) -> List[Dict]:
    """Extract providers with their associated contact information to prevent orphaned data"""
    providers = []
    logger.error(f"extract_structured_providers called with {len(context_chunks)} chunks")
    
    phone_pattern = r'\b(?:\(\d{3}\)\s*|\d{3}[-.\s]?)?\d{3}[-.\s]?\d{4}\b'
    
    for chunk in context_chunks:
        if 'Provider:' in chunk and 'CONTACT INFORMATION:' in chunk:
            lines = chunk.split('\n')
            current_name = ""
            current_contacts = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('Provider:'):
                    current_name = line.replace('Provider:', '').strip()
                
                elif line == 'CONTACT INFORMATION:':
                    # Collect contact info from next few lines
                    contact = {}
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        contact_line = lines[i].strip()
                        if contact_line.startswith('Phone:'):
                            phone_text = contact_line.replace('Phone:', '').strip()
                            if re.search(phone_pattern, phone_text):
                                contact['phone'] = phone_text
                        elif contact_line.startswith('Address:'):
                            contact['address'] = contact_line.replace('Address:', '').strip()
                        elif contact_line.startswith('Website:'):
                            website = contact_line.replace('Website:', '').strip()
                            website = re.sub(r'\.\.+', '.', website)
                            if 'http' in website:
                                contact['website'] = website
                        i += 1
                    
                    if contact:
                        current_contacts.append(contact)
                    i -= 1  # Back up one since we'll increment at end of loop
                
                i += 1
            
            if current_name and current_contacts:
                providers.append({
                    'name': current_name,
                    'contacts': current_contacts
                })
    
    logger.error(f"extract_structured_providers found {len(providers)} providers")
    return providers

async def extract_categories_from_chunks(chunks: List[str]) -> List[str]:
    """Extract categories using semantic analysis to identify business category text"""
    categories = []
    
    # Create embedding for "business category" concept
    try:
        category_concept_embedding = await embed_query_async("business category service type industry classification")
    except Exception as e:
        logger.warning(f"Error creating category concept embedding: {e}")
        return []
    
    for chunk in chunks:
        lines = chunk.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip obvious non-category lines
            if not line or len(line) < 3 or len(line) > 50:
                continue
            if line.startswith(('Provider:', 'CONTACT INFORMATION:', 'Phone:', 'Email:', 'Website:', 'Address:')):
                continue
            if any(char.isdigit() for char in line):  # Skip lines with numbers
                continue
            if '@' in line or 'http' in line or '(' in line:  # Skip contact info
                continue
                
            # Check if line semantically represents a business category
            try:
                line_embedding = await embed_query_async(f"business category: {line}")
                similarity = cosine_similarity(category_concept_embedding, line_embedding)
                
                # If similarity is high, this line likely represents a category
                if similarity > 0.4:  # Threshold for category-like text
                    categories.append(line)
                    logger.debug(f"Found category '{line}' with similarity {similarity:.3f}")
                    
            except Exception as e:
                logger.debug(f"Error processing potential category '{line}': {e}")
                continue
    
    # Return unique categories
    unique_categories = list(set(categories))
    logger.debug(f"Extracted categories: {unique_categories}")
    return unique_categories

def get_tenant_system_prompt(db: Session, tenant_id: str) -> str:
    """
    Generate system prompt based on tenant-specific agent configuration
    Falls back to minimal generic prompt if no config exists
    """
    try:
        # Get agent config for tenant
        agent_config = db.query(AgentConfig).filter(
            AgentConfig.tenant_id == tenant_id,
            AgentConfig.is_active == True
        ).first()
        
        if agent_config and agent_config.system_prompt:
            # Use custom system prompt if provided
            return agent_config.system_prompt
        elif agent_config:
            # Generate prompt from config settings
            prompt_parts = []
            
            # Basic personality setup
            prompt_parts.append(f"You are {agent_config.agent_name}, a {agent_config.agent_role}.")
            
            # Add personality traits
            if agent_config.personality_traits:
                traits_text = ", ".join(agent_config.personality_traits)
                prompt_parts.append(f"\nYour personality traits: {traits_text}")
            
            # Add industry context
            if agent_config.industry != "general":
                prompt_parts.append(f"\nYou specialize in {agent_config.industry} and have deep knowledge in this field.")
            
            # Add response style guidance
            style_guidance = {
                "conversational": "Respond in a friendly, conversational tone.",
                "professional": "Maintain a professional and formal tone.",
                "technical": "Use technical language and be precise in your explanations.",
                "casual": "Keep your responses casual and relaxed.",
                "formal": "Use formal language and structure in your responses."
            }
            
            if agent_config.response_style in style_guidance:
                prompt_parts.append(f"\nCommunication style: {style_guidance[agent_config.response_style]}")
            
            # Add custom instructions
            if agent_config.custom_instructions:
                prompt_parts.append(f"\nAdditional guidelines: {agent_config.custom_instructions}")
            
            # Add general guidelines
            prompt_parts.append("""
\nABSOLUTE MANDATORY RULES - VIOLATION OF THESE RULES IS UNACCEPTABLE:

RULE 1 - GEOGRAPHIC ACCURACY (MOST CRITICAL):
- If user asks about SPOKANE: ONLY mention resources explicitly located in Spokane, WA
- If user asks about TACOMA: ONLY mention resources explicitly located in Tacoma, WA  
- If user asks about SEATTLE: ONLY mention resources explicitly located in Seattle, WA
- NEVER EVER mention a Tacoma address when someone asks about Spokane
- NEVER EVER mention a Spokane address when someone asks about Tacoma
- EXAMPLES OF VIOLATIONS (DO NOT DO THESE):
  ❌ BAD: "For Spokane housing, there's a resource at 405 Broadway, Tacoma, WA"
  ❌ BAD: "In the Spokane area... Also, here's something in Tacoma..."
  ✅ GOOD: "For Spokane housing, I found [Spokane address only]"
  ✅ GOOD: "I don't have any Spokane-specific resources in my information"

RULE 2 - CONTACT INFORMATION LOGIC:
- If you provide a phone number, that IS contact information
- NEVER say "I don't have contact information" if you just provided a phone/address/email
- EXAMPLES OF VIOLATIONS (DO NOT DO THESE):
  ❌ BAD: "They have a number at 253-383-2593, but I don't have their contact information"
  ❌ BAD: "Located at 123 Main St, but no contact details available"
  ✅ GOOD: "You can contact them at 253-383-2593"
  ✅ GOOD: "I found their address at 123 Main St but don't have a phone number"

RULE 3 - CONTEXT-ONLY INFORMATION:
- ONLY use information explicitly stated in the provided context
- DO NOT elaborate or add details not in the context
- DO NOT describe services unless those exact descriptions are provided
- EXAMPLES OF VIOLATIONS (DO NOT DO THESE):
  ❌ BAD: "They offer food, shelter, and case management for up to 90 days" (unless exactly stated)
  ❌ BAD: "This appears to be a domestic violence shelter" (unless exactly stated)
  ✅ GOOD: "According to my information, they provide [exact text from context]"
  ✅ GOOD: "I found this organization but don't have details about their specific services"

RULE 4 - NO MIXING OR COMBINING:
- Each piece of information must come from the same source entry
- NEVER combine details from different organizations or entries
- NEVER assume connections between separate pieces of information
- EXAMPLES OF VIOLATIONS (DO NOT DO THESE):
  ❌ BAD: Taking name from one entry and phone from another entry
  ❌ BAD: "Organization X, part of Department Y" (unless explicitly stated together)
  ✅ GOOD: "I found Organization X, and separately I found Department Y"

RULE 5 - CRITICAL REFERENCING:
- NEVER use "us", "we", "our" when referring to organizations
- Always use "they", "them", "their"
- You are providing information ABOUT services, not representing them
- EXAMPLES:
  ✅ GOOD: "You can contact them at..."
  ❌ BAD: "You can contact us at..."

RULE 6 - NO EXTERNAL LOOKUPS:
- NEVER offer to "look up", "find", or "search for" additional information
- NEVER suggest you can get more contact details or information later
- Only provide what's available in the current database
- EXAMPLES OF VIOLATIONS (DO NOT DO THESE):
  ❌ BAD: "If you'd like more information on these options, I can try to look up their contact details for you"
  ❌ BAD: "I can search for more midwives in the area"
  ❌ BAD: "Let me find their phone number for you"
  ✅ GOOD: "This is the information I have available"
  ✅ GOOD: "I don't have additional contact details in my current information"

RULE 7 - RELEVANCE TO QUERY:
- ONLY provide information directly relevant to what was asked
- If context doesn't contain relevant information, clearly state that
- NEVER provide unrelated services just to have something to say
- EXAMPLES:
  ❌ BAD: User asks for midwives, you provide legal services information
  ❌ BAD: User asks for prenatal care, you provide housing information
  ✅ GOOD: "I don't have information about midwives in Spokane County in my current database"
  ✅ GOOD: "I wasn't able to find prenatal care providers that accept Medicaid in the area"

CRITICAL INSTRUCTION FOR LIMITED/IRRELEVANT CONTEXT:
If the provided context does NOT contain information relevant to the user's specific query:
- State clearly and simply: "I don't have information about [specific request] in [location] in my current database."
- Do NOT list unrelated services or organizations
- Do NOT provide contact information for unrelated services
- Do NOT mention services you're unsure about
- Do NOT say "however" or "but" and then list unrelated information
- Be honest and direct about the limitations
- Keep your response brief and clear

STEP-BY-STEP RESPONSE VERIFICATION PROCESS:
Before providing ANY information, you MUST check:

STEP 1 - LOCATION CHECK:
- What location did the user ask about? (Spokane/Tacoma/Seattle/etc.)
- Does each resource I'm about to mention explicitly match that location?
- If not, REMOVE that resource from my response immediately

STEP 2 - INFORMATION COMPLETENESS CHECK:
- For each organization I mention, what do I actually know about them?
- Do I have their name AND verified contact information together in the same context entry?
- If not, I must say "I found [name] but don't have their contact information"

STEP 3 - CONTEXT VERIFICATION:
- Is every detail I'm about to share written exactly as stated in my context?
- Am I adding any descriptions, services, or details not explicitly provided?
- If yes, REMOVE those additions immediately

STEP 4 - LOGIC CHECK:
- Am I saying contradictory things (like providing a phone number then saying I have no contact info)?
- Am I mixing information from different sources?
- If yes, FIX the contradiction or remove the conflicting information

WHAT YOU CAN DO:
- Share names, contact details, and information that ARE in the context
- Use exact quotes from the context when describing services
- Be helpful while staying within verified information
- Maintain your personality while being accurate

WHAT YOU CANNOT DO - EXAMPLES:
❌ "For Spokane resources, here's one in Tacoma..." (WRONG LOCATION)
❌ "They have phone 123-456-7890 but I don't have contact info" (CONTRADICTORY)
❌ "They provide comprehensive case management services" (UNLESS EXACTLY STATED)
❌ "Organization X is part of Department Y" (UNLESS EXPLICITLY CONNECTED)
❌ "This appears to be..." or "seems to offer..." (NO GUESSING)

MANDATORY RESPONSE FORMAT:
1. Always start by acknowledging the specific location requested
2. Only mention resources that match that exact location
3. For each resource, provide: Name + Contact Information (if available)
4. If no location-appropriate resources found, say so clearly
5. Never mix locations in the same response

EMERGENCY FALLBACK RULE:
If you are EVER unsure about any detail, always choose the more conservative option:
- Don't mention the resource rather than risk providing wrong information
- Say "I don't have information about that" rather than guess
- Provide less information rather than potentially incorrect information

IMPORTANT FORMATTING RULES:
1. Use plain text formatting, NOT markdown
2. For bullet points, use "•" (bullet character), not "*" or "-"
3. For section headers, use plain text with colons (like "Available Providers (3 found):")
4. Always include proper line breaks between sections""")
            
            return "".join(prompt_parts)
            
    except Exception as e:
        logger.error(f"Error getting tenant system prompt: {e}")
    
    # Minimal generic fallback prompt - encourages proper agent configuration
    return """You are an AI assistant. Please provide helpful and accurate responses based on available information.

ABSOLUTE MANDATORY RULES - VIOLATION IS UNACCEPTABLE:

RULE 1 - GEOGRAPHIC ACCURACY (MOST CRITICAL):
- If user asks about SPOKANE: ONLY mention Spokane, WA resources
- If user asks about TACOMA: ONLY mention Tacoma, WA resources  
- NEVER EVER mention a Tacoma address for a Spokane question
- NEVER EVER mention a Spokane address for a Tacoma question
- EXAMPLES:
  ❌ BAD: "For Spokane housing, here's one in Tacoma..."
  ✅ GOOD: "For Spokane housing, I found [Spokane address only]"

RULE 2 - CONTACT INFORMATION LOGIC:
- If you provide a phone number, that IS contact information
- NEVER say "I don't have contact information" after providing a phone/address
- EXAMPLES:
  ❌ BAD: "Call them at 253-383-2593, but I don't have their contact information"
  ✅ GOOD: "You can contact them at 253-383-2593"

RULE 3 - CONTEXT-ONLY INFORMATION:
- ONLY use information explicitly stated in the provided context
- DO NOT elaborate or add details not in the context
- EXAMPLES:
  ❌ BAD: "They offer food, shelter, and case management" (unless exactly stated)
  ✅ GOOD: "According to my information, they provide [exact text from context]"

STEP-BY-STEP VERIFICATION:
Before responding, check:
1. What location did user ask about?
2. Do my resources match that exact location?
3. Am I being contradictory about contact information?
4. Am I adding details not in my context?

EMERGENCY FALLBACK RULE:
When in doubt, always choose the more conservative option:
- Don't mention the resource rather than risk wrong information
- Say "I don't have information about that" rather than guess

CRITICAL REFERENCING RULES:
- NEVER use "us", "we", "our" when referring to providers
- Always use "they", "them", "their"
- You provide information ABOUT services, not representing them

IMPORTANT FORMATTING RULES:
1. Use plain text formatting, NOT markdown
2. For bullet points, use "•" (bullet character)
3. Always include proper line breaks between sections

General guidelines:
- Be helpful and informative within these strict rules
- If you don't know something, say so clearly
- Keep responses focused and relevant to the requested location"""

def get_tenant_greeting(db: Session, tenant_id: str) -> str:
    """
    Get tenant-specific greeting message
    Falls back to default if no config exists
    """
    try:
        agent_config = db.query(AgentConfig).filter(
            AgentConfig.tenant_id == tenant_id,
            AgentConfig.is_active == True
        ).first()
        
        if agent_config and agent_config.greeting_message:
            return agent_config.greeting_message
        elif agent_config:
            return f"Hi there! I'm {agent_config.agent_name}, and I'm here to help you."
    except Exception as e:
        logger.error(f"Error getting tenant greeting: {e}")
    
    # Generic fallback greeting
    return "Hello! I'm here to help you with your questions."

def build_agent_aware_prompt(question: str, context_chunks: List[str], agent_config: AgentConfig, contact_info: Dict, provider_names: List[str]) -> str:
    """
    Build a prompt that reflects the agent's personality and style.
    This creates more natural, agent-like responses by adapting the prompt
    structure to match the configured response style.
    """
    
    # Different prompt styles based on response_style
    if agent_config.response_style == "conversational":
        if context_chunks:
            # Natural conversation with context
            primary_context = clean_text_content(context_chunks[0][:400])
            prompt = f"""Customer asks: {question}

Available information: {primary_context}

MANDATORY INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:
1. READ the customer's question carefully
2. READ the available information carefully  
3. CHECK: Does the available information contain what the customer is asking for?
4. IF YES: Provide only that relevant information
5. IF NO: Say "I don't have information about [what they asked for] in [location] in my current database" and STOP
6. DO NOT mention any organization unless you are 100% certain it provides what they asked for
7. DO NOT say "however" or "but" and then mention unrelated services

EXAMPLE:
- Customer asks for midwives
- Information is about legal services
- Response: "I don't have information about midwives in Spokane County in my current database."
- DO NOT mention the legal services AT ALL

YOUR RESPONSE:"""
            
            # Add contact information associated with providers (prevents orphaned contacts)
            if contact_info and provider_names:
                prompt += "\nCONTACT INFORMATION (associated with providers found):"
                for provider_name in provider_names:
                    prompt += f"\n{provider_name}:"
                    if contact_info.get('phones'):
                        prompt += f"\n  Phone numbers available: {', '.join(contact_info['phones'])}"
                    if contact_info.get('emails'):
                        prompt += f"\n  Emails available: {', '.join(contact_info['emails'])}"
                    if contact_info.get('websites'):
                        prompt += f"\n  Websites available: {', '.join(contact_info['websites'])}"
                    if contact_info.get('addresses'):
                        prompt += f"\n  Addresses available: {' | '.join(contact_info['addresses'])}"
                    break  # Only show contact info once with first provider
            
            prompt += f"\n\nAs {agent_config.agent_name}, respond conversationally using ONLY the information provided above. CRITICAL: If you mention a name or organization but don't have their contact details in the context above, you MUST say 'I found [name] but don't have their contact information.' NEVER invent phone numbers, addresses, emails, or websites. NEVER use placeholder formats like '123 Main St' or '(XXX) XXX-XXXX' as if they're real."
            return prompt
        else:
            return f"""Customer: {question}

As {agent_config.agent_name}, help them with their question. No specific matches were found in our database, but guide them conversationally."""
    
    elif agent_config.response_style == "professional":
        if context_chunks:
            primary_context = clean_text_content(context_chunks[0][:500])
            prompt = f"""Client inquiry: {question}

Reference material:
{primary_context}"""
            
            # Add contact information associated with providers (prevents orphaned contacts)
            if contact_info and provider_names:
                prompt += "\n\nCONTACT DIRECTORY:"
                for provider_name in provider_names:
                    prompt += f"\n{provider_name}:"
                    if contact_info.get('phones'):
                        prompt += f"\n  Phone: {', '.join(contact_info['phones'])}"
                    if contact_info.get('emails'):
                        prompt += f"\n  Email: {', '.join(contact_info['emails'])}"
                    if contact_info.get('websites'):
                        prompt += f"\n  Website: {', '.join(contact_info['websites'])}"
                    if contact_info.get('addresses'):
                        prompt += f"\n  Address: {' | '.join(contact_info['addresses'])}"
                    break  # Only show contact info once with first provider
            
            prompt += f"""

RELEVANCE CHECK: Only mention services/organizations if they are DIRECTLY RELEVANT to "{question}".
If the reference material is about unrelated services (e.g., legal services for a midwife question), state that you don't have relevant information.

As {agent_config.agent_name} ({agent_config.agent_role}), provide a professional response using ONLY the information above. Include ALL available contact details when mentioning any organization or service. Do not add any details not present in the material."""
            return prompt
        else:
            return f"""Client inquiry: {question}

As {agent_config.agent_name} ({agent_config.agent_role}), provide professional guidance. No specific matches were found in our database."""
    
    elif agent_config.response_style == "technical":
        if context_chunks:
            # Technical style gets more raw data
            context_data = '\n'.join([chunk[:200] for chunk in context_chunks[:2]])
            prompt = f"""Query: {question}

Data retrieved:
{context_data}"""
            
            # Add contact information associated with providers (prevents orphaned contacts)
            if contact_info and provider_names:
                prompt += "\n\nPROVIDER CONTACT DATA:"
                for provider_name in provider_names:
                    prompt += f"\n{provider_name}:"
                    if contact_info.get('phones'):
                        prompt += f"\n  Phone: {', '.join(contact_info['phones'])}"
                    if contact_info.get('emails'):
                        prompt += f"\n  Email: {', '.join(contact_info['emails'])}"
                    if contact_info.get('websites'):
                        prompt += f"\n  Website: {', '.join(contact_info['websites'])}"
                    if contact_info.get('addresses'):
                        prompt += f"\n  Address: {' | '.join(contact_info['addresses'])}"
                    break  # Only show contact info once with first provider
            
            prompt += f"\n\nRELEVANCE: Only mention data if it relates to '{question}'. If data is unrelated, state no relevant information found.\n\nProvide technical details as {agent_config.agent_name}, focusing on accuracy and specificity. Include ALL contact information when mentioning any organization or service."
            return prompt
        else:
            return f"""Query: {question}

No data matches found. Provide technical guidance as {agent_config.agent_name}."""
    
    elif agent_config.response_style == "casual":
        if context_chunks:
            primary_context = clean_text_content(context_chunks[0][:300])
            prompt = f"""{question}

Here's what I found: {primary_context}\n\nIMPORTANT: Only share this if it's relevant to your question about '{question}'."""
            
            # Add ALL available contact info
            if contact_info.get('phones'):
                prompt += f"\nPhone numbers available: {', '.join(contact_info['phones'])}"
            if contact_info.get('emails'):
                prompt += f"\nEmails available: {', '.join(contact_info['emails'])}"
            if contact_info.get('websites'):
                prompt += f"\nWebsites available: {', '.join(contact_info['websites'])}"
            if contact_info.get('addresses'):
                prompt += f"\nAddresses available: {' | '.join(contact_info['addresses'])}"
            
            prompt += f"\n\nReply casually as {agent_config.agent_name} would - keep it friendly and relaxed. Make sure to share any contact details when you mention organizations or services."
            return prompt
        else:
            return f"""{question}

Didn't find exact matches in our info, but reply helpfully as {agent_config.agent_name} would - keep it casual and friendly."""
    
    else:  # formal or default
        if context_chunks:
            primary_context = clean_text_content(context_chunks[0][:400])
            prompt = f"""Inquiry: {question}

Available information:
{primary_context}"""
            
            # Add ALL available contact info
            if contact_info.get('phones'):
                prompt += f"\nPhone numbers: {', '.join(contact_info['phones'])}"
            if contact_info.get('emails'):
                prompt += f"\nEmails: {', '.join(contact_info['emails'])}"
            if contact_info.get('websites'):
                prompt += f"\nWebsites: {', '.join(contact_info['websites'])}"
            if contact_info.get('addresses'):
                prompt += f"\nAddresses: {' | '.join(contact_info['addresses'])}"
            
            prompt += f"\n\nRELEVANCE CHECK: Only mention the above if it relates to '{question}'. If unrelated, state you don't have that specific information.\n\nPlease respond formally as {agent_config.agent_name}, {agent_config.agent_role}. Include all relevant contact information when referencing any organization or service."
            return prompt
        else:
            return f"""Inquiry: {question}

Please provide formal assistance as {agent_config.agent_name}, {agent_config.agent_role}. Note: No specific matches were found in our database."""

async def generate_single_prompt_response(question: str, context_chunks: List[str], tenant_id: str, db: Session) -> str:
    """
    Generate response using Ollama LLM with agent-aware prompting
    """
    # Get agent configuration for personality-driven prompting
    agent_config = db.query(AgentConfig).filter(
        AgentConfig.tenant_id == tenant_id,
        AgentConfig.is_active == True
    ).first()
    
    # Extract contact info and provider names for association  
    contact_info = extract_contact_info(context_chunks) if context_chunks else {}
    
    # Extract provider names from context to associate with contact info
    provider_names = []
    if context_chunks:
        for chunk in context_chunks:
            lines = chunk.split('\n')
            for line in lines:
                if line.strip().startswith('Provider:'):
                    name = line.replace('Provider:', '').strip()
                    if name and len(name) > 3:  # Avoid short garbage
                        provider_names.append(name)
    
    logger.error(f"DEBUG: Found {len(provider_names)} provider names: {provider_names}")
    logger.error(f"DEBUG: Contact info found: {contact_info}")
    
    # Get tenant-specific system prompt
    system_prompt = get_tenant_system_prompt(db, tenant_id)
    
    # Build context-aware user prompt based on agent personality
    if agent_config:
        user_prompt = build_agent_aware_prompt(
            question, 
            context_chunks, 
            agent_config,
            contact_info,
            provider_names
        )
    else:
        # Fallback to minimal prompt
        if context_chunks:
            user_prompt = f"""{question}

[Context: {clean_text_content(context_chunks[0][:500])}]"""
        else:
            user_prompt = question
    
    
    logger.error(f"Using agent-aware prompt for tenant {tenant_id}")
    logger.error(f"Agent config: {agent_config.agent_name if agent_config else 'No config'}, style: {agent_config.response_style if agent_config else 'N/A'}")
    
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
        # Fallback - extract basic data for fallback response
        chunk_categories = await extract_categories_from_chunks(context_chunks) if context_chunks else []
        providers = []
        descriptions = []
        
        if context_chunks:
            for chunk in context_chunks:
                if "PROVIDER:" in chunk:
                    provider = chunk.split("PROVIDER:")[1].split('\n')[0].strip()
                    if provider and provider not in providers:
                        providers.append(provider)
                if "DESCRIPTION:" in chunk:
                    desc = chunk.split("DESCRIPTION:")[1].strip()
                    cleaned_desc = clean_text_content(desc)
                    if cleaned_desc:
                        descriptions.append(cleaned_desc)
        
        return simulate_llm_response(question, context_chunks, chunk_categories, contact_info, providers, descriptions, tenant_id, db)

def simulate_llm_response(question: str, context_chunks: List[str], categories: List[str], contact_info: Dict, providers: List[str], descriptions: List[str], tenant_id: str = None, db: Session = None) -> str:
    """
    Fallback response generation when Ollama is not available
    """
    q_lower = question.lower().strip()
    
    # Handle greetings and general conversation
    if any(greeting in q_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        base_greeting = get_tenant_greeting(db, tenant_id) if db and tenant_id else "Hello! I'm here to help you with your questions."
        return f"""{base_greeting} 

I'm here to assist you with information and answer your questions. What can I help you with today?"""
    
    if any(question in q_lower for question in ['what can you do', 'what do you do', 'how can you help']):
        return """I'm an AI assistant that can help answer your questions based on the information available to me.

I can provide information and assistance on various topics. Feel free to ask me about anything you'd like to know, and I'll do my best to help you with accurate and relevant information.

What would you like to know about?"""
    
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

async def generate_answer(question: str, context_chunks: List[str], tenant_id: str, db: Session, similarity_scores: List[float] = None) -> Dict[str, Any]:
    """
    Generate structured answers using Ollama
    """
    # Check if we have relevant enough context
    # Since we're using cosine distance (1 - similarity), scores are often negative
    # We consider anything above -0.6 as relevant (closer to 0 = more similar)
    has_relevant_context = bool(context_chunks) and (not similarity_scores or max(similarity_scores, default=-1) >= -0.6)
    
    if not has_relevant_context:
        # Return a polite "I don't know" response
        agent_config = db.query(AgentConfig).filter(
            AgentConfig.tenant_id == tenant_id,
            AgentConfig.is_active == True
        ).first()
        
        agent_name = agent_config.agent_name if agent_config else "I"
        
        answer_text = f"I don't have specific information about {question.lower()} in my knowledge base. {agent_name} can only provide information about topics that have been added to my system. If you have questions about services or resources I've been trained on, I'd be happy to help with those!"
        
        return {
            "answer": answer_text,
            "sources": [],
            "contact_info": {},
            "categories": [],
            "providers": []
        }
    
    # Generate response using Ollama with context
    answer_text = await generate_single_prompt_response(question, context_chunks, tenant_id, db)
    
    # Still extract structured data for API response
    chunk_categories = await extract_categories_from_chunks(context_chunks) if context_chunks else []
    contact_info = extract_contact_info(context_chunks) if context_chunks else {}
    
    providers = []
    # Extract organization names from categories using semantic patterns
    logger.debug(f"DEBUG: generate_answer extracting providers from {len(chunk_categories)} categories")
    for category in chunk_categories:
        # Look for categories that likely contain organization names
        # Pattern: "Category Type: Organization Name" or just proper noun phrases
        if ":" in category:
            # Split on colon and take the part that looks like an organization name
            parts = category.split(":", 1)
            if len(parts) == 2:
                potential_name = parts[1].strip()
                # Check if it looks like an organization name (starts with capital, reasonable length)
                if (potential_name and 
                    len(potential_name) > 3 and 
                    potential_name[0].isupper() and
                    potential_name not in providers):
                    logger.debug(f"DEBUG: generate_answer found organization from colon split: '{potential_name}' from '{category}'")
                    providers.append(potential_name)
        
        # Also check for standalone organization names (proper noun phrases)
        elif (category and 
              len(category) > 3 and 
              category[0].isupper() and
              " " in category and  # Multi-word names more likely to be organizations
              not category.lower().startswith(('the ', 'a ', 'an ')) and  # Avoid generic descriptions
              category not in providers):
            logger.debug(f"DEBUG: generate_answer found standalone organization: '{category}'")
            providers.append(category)
    
    logger.debug(f"DEBUG: generate_answer final extracted providers: {providers}")
    
    # Fallback: Look for traditional provider patterns if no organizations found
    if not providers and context_chunks:
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