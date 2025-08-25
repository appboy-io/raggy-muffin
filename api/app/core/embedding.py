import ollama
from functools import lru_cache
from typing import List, Tuple
import uuid
import asyncio
import logging
import os
import numpy as np
# from app.cache import cached

logger = logging.getLogger(__name__)

def get_ollama_host():
    """Get Ollama host from environment"""
    return os.getenv('OLLAMA_HOST', 'http://localhost:11434')

def get_embedding_model():
    """Get the embedding model name from environment"""
    return os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')

def chunk_text(text: str, chunk_size: int = None, overlap_words: int = 50) -> List[str]:
    """
    Intelligent adaptive text chunking with dynamic sizing
    """
    words = text.split()
    text_length = len(words)
    
    # Adaptive chunk sizing based on document length
    if chunk_size is None:
        if text_length < 500:
            chunk_size = 150  # Smaller chunks for short docs
        elif text_length < 2000:
            chunk_size = 300  # Standard chunks for medium docs
        elif text_length < 10000:
            chunk_size = 500  # Larger chunks for long docs
        else:
            chunk_size = 800  # Extra large chunks for very long docs
    
    # If text is smaller than chunk size, return as single chunk
    if text_length <= chunk_size:
        return [text]
    
    # Try to split on sentence boundaries when possible
    sentences = text.split('.')
    chunks = []
    current_chunk = ""
    current_word_count = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_words = len(sentence.split())
        
        # If adding this sentence would exceed chunk size, finalize current chunk
        if current_word_count + sentence_words > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap from previous chunk
            if overlap_words > 0 and len(chunks) > 0:
                prev_words = chunks[-1].split()
                overlap_text = " ".join(prev_words[-overlap_words:]) if len(prev_words) > overlap_words else chunks[-1]
                current_chunk = overlap_text + ". " + sentence + "."
                current_word_count = len(current_chunk.split())
            else:
                current_chunk = sentence + "."
                current_word_count = sentence_words
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += ". " + sentence + "."
            else:
                current_chunk = sentence + "."
            current_word_count += sentence_words
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Fallback to word-based chunking if sentence-based didn't work well
    if not chunks or any(len(chunk.split()) > chunk_size * 1.5 for chunk in chunks):
        return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size - overlap_words)]
    
    # Filter out very small chunks (less than 10 words)
    chunks = [chunk for chunk in chunks if len(chunk.split()) >= 10]
    
    return chunks

async def embed_chunks_async(chunks: List[str], tenant_id: str) -> List[Tuple[str, str, str, List[float]]]:
    """
    Asynchronously embed text chunks using Ollama
    """
    try:
        host = get_ollama_host()
        model = get_embedding_model()
        
        # Run embeddings in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def embed_batch():
            embeddings = []
            for chunk in chunks:
                response = ollama.embeddings(
                    model=model,
                    prompt=chunk,
                    options={'host': host}
                )
                embeddings.append(np.array(response['embedding']))
            
            # Normalize embeddings
            embeddings = np.array(embeddings)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / norms
            return normalized_embeddings
        
        embeddings = await loop.run_in_executor(None, embed_batch)
        
        return [
            (str(uuid.uuid4()), tenant_id, chunk, emb.tolist())
            for chunk, emb in zip(chunks, embeddings)
        ]
    except Exception as e:
        logger.error(f"Error embedding chunks with Ollama: {e}")
        raise

def embed_chunks(chunks: List[str], tenant_id: str) -> List[Tuple[str, str, str, List[float]]]:
    """
    Synchronous version using Ollama
    """
    try:
        host = get_ollama_host()
        model = get_embedding_model()
        
        embeddings = []
        for chunk in chunks:
            response = ollama.embeddings(
                model=model,
                prompt=chunk,
                options={'host': host}
            )
            embeddings.append(np.array(response['embedding']))
        
        # Normalize embeddings
        embeddings = np.array(embeddings)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized_embeddings = embeddings / norms
        
        return [
            (str(uuid.uuid4()), tenant_id, chunk, emb.tolist())
            for chunk, emb in zip(chunks, normalized_embeddings)
        ]
    except Exception as e:
        logger.error(f"Error embedding chunks with Ollama: {e}")
        raise

# @cached(key_prefix="query_embedding", ttl=3600)  # Cache for 1 hour
async def embed_query_async(query: str) -> List[float]:
    """
    Embed a single query asynchronously with caching using Ollama
    """
    try:
        host = get_ollama_host()
        model = get_embedding_model()
        
        # Run embedding in thread pool
        loop = asyncio.get_event_loop()
        
        def embed_single():
            response = ollama.embeddings(
                model=model,
                prompt=query,
                options={'host': host}
            )
            # Normalize the embedding
            embedding = np.array(response['embedding'])
            norm = np.linalg.norm(embedding)
            normalized_embedding = embedding / norm
            return normalized_embedding
        
        embedding = await loop.run_in_executor(None, embed_single)
        
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error embedding query with Ollama: {e}")
        raise