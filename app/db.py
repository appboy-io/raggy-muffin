from sqlalchemy import create_engine, text
import os

DB_CONN = os.getenv("DB_CONN", "postgresql://rag_user:rag_pass@localhost:5432/rag_db")

engine = create_engine(DB_CONN)

def insert_embeddings(records):
    """
    records = list of (id, tenant_id, content, embedding) tuples
    """

    insert_query = text("""
        INSERT INTO embeddings (id, tenant_id, content, embedding)
        VALUES (:id, :tenant_id, :content, :embedding)
    """)

    with engine.begin() as conn:
        for record in records:
            conn.execute(insert_query, {
                "id": record[0],
                "tenant_id": record[1],
                "content": record[2],
                "embedding": record[3]
            })
