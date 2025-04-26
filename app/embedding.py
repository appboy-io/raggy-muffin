from sentence_transformers import SentenceTransformer
import uuid

embedder = SentenceTransformer("BAAI/bge-base-en-v1.5")

def chunk_text(text, chunk_size=300):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def embed_chunks(chunks, tenant_id):
    embeddings = embedder.encode(chunks, normalize_embeddings=True)
    return [
        (str(uuid.uuid4()), tenant_id, chunk, emb.tolist())
        for chunk, emb in zip(chunks, embeddings)
    ]
