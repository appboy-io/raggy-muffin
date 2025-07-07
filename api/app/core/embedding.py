from sentence_transformers import SentenceTransformer
from functools import lru_cache
from typing import List, Tuple
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_embedder():
    """Lazy loading of embedding model with caching"""
    try:
        return SentenceTransformer("BAAI/bge-base-en-v1.5")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise

def chunk_text(text: str, chunk_size: int = 300, overlap_words: int = 50) -> List[str]:
    """
    Intelligent text chunking that tries to respect sentence boundaries
    """
    words = text.split()
    
    # If text is smaller than chunk size, return as single chunk
    if len(words) <= chunk_size:
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
    
    return chunks

async def embed_chunks_async(chunks: List[str], tenant_id: str) -> List[Tuple[str, str, str, List[float]]]:
    """
    Asynchronously embed text chunks
    """
    try:
        embedder = get_embedder()
        
        # Run embedding in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            lambda: embedder.encode(chunks, normalize_embeddings=True)
        )
        
        return [
            (str(uuid.uuid4()), tenant_id, chunk, emb.tolist())
            for chunk, emb in zip(chunks, embeddings)
        ]
    except Exception as e:
        logger.error(f"Error embedding chunks: {e}")
        raise

def embed_chunks(chunks: List[str], tenant_id: str) -> List[Tuple[str, str, str, List[float]]]:
    """
    Synchronous version for backwards compatibility
    """
    embedder = get_embedder()
    embeddings = embedder.encode(chunks, normalize_embeddings=True)
    
    return [
        (str(uuid.uuid4()), tenant_id, chunk, emb.tolist())
        for chunk, emb in zip(chunks, embeddings)
    ]

async def embed_query_async(query: str) -> List[float]:
    """
    Embed a single query asynchronously
    """
    try:
        embedder = get_embedder()
        
        # Run embedding in thread pool
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: embedder.encode([query], normalize_embeddings=True)[0]
        )
        
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error embedding query: {e}")
        raise