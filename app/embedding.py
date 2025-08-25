import ollama
import streamlit as st
import uuid
import os
import numpy as np

@st.cache_resource
def get_ollama_client():
    """Get Ollama client with configuration"""
    host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    return host

def get_embedding_model():
    """Get the embedding model name from environment"""
    return os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')

def chunk_text(text, chunk_size=300, overlap_words=50):
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

@st.cache_data(ttl=3600)
def cached_embed_text(text_list):
    """Cache embeddings for repeated text processing"""
    host = get_ollama_client()
    model = get_embedding_model()
    
    embeddings = []
    for text in text_list:
        response = ollama.embeddings(
            model=model,
            prompt=text,
            options={'host': host}
        )
        embeddings.append(np.array(response['embedding']))
    
    # Normalize embeddings
    embeddings = np.array(embeddings)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norms
    
    return normalized_embeddings

def embed_chunks(chunks, tenant_id):
    embeddings = cached_embed_text(chunks)
    return [
        (str(uuid.uuid4()), tenant_id, chunk, emb.tolist())
        for chunk, emb in zip(chunks, embeddings)
    ]