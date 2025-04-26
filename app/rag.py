from embedding import embedder
from db import engine
from sqlalchemy import text
from transformers import pipeline

# Simple pipeline with HuggingFace for now
generator = pipeline(
    "text-generation", 
    model="google/flan-t5-base",
    device=0
)

def retrieve_relevant_chunks(query, tenant_id, top_k=5):
    query_emb = embedder.encode([query], normalize_embeddings=True)[0].tolist()
    with engine.connect() as conn:
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
        return [row[0] for row in result]

def generate_answer(question, context_chunks):
    formatted_context = "\n\n==========\n\n".join(context_chunks)
    prompt = f""""You are an expert assistant. You must ONLY answer the question based on the provided context below.

    If the context does NOT contain enough information to answer the question, you must respond with "I don't know based on the provided information."    
    
    Context:
    {formatted_context}

    Question: {question}

    Answer:"""

    response = generator(prompt, max_new_tokens=512, do_sample=False, temperature=0)
    return response[0]["generated_text"]
