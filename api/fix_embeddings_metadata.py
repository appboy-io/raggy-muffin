#!/usr/bin/env python3
"""
Migration script to fix existing embeddings metadata
Adds document_id to meta_data field for proper deletion cascade
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime

# Database connection
DB_HOST = os.getenv('DB_HOST', 'cleona_pgvector')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = 'cleona_db'
DB_USER = 'cleona_user'
DB_PASSWORD = 'cleona_secure_pass_2024'

def fix_embeddings_metadata():
    """Fix metadata for existing embeddings"""
    
    conn = None
    cur = None
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Connected to database")
        
        # First, check how many embeddings exist without document_id
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM embeddings 
            WHERE meta_data IS NULL 
               OR meta_data::text = '{}'
               OR NOT (meta_data ? 'document_id')
        """)
        result = cur.fetchone()
        orphaned_count = result['count']
        
        print(f"Found {orphaned_count} embeddings without document_id")
        
        if orphaned_count == 0:
            print("No orphaned embeddings found. Migration not needed.")
            return
        
        # Get all documents with their tenant_id and creation times
        cur.execute("""
            SELECT id, tenant_id, created_at, filename, chunk_count
            FROM documents 
            ORDER BY created_at DESC
        """)
        documents = cur.fetchall()
        
        print(f"Found {len(documents)} documents")
        
        fixed_count = 0
        
        for doc in documents:
            doc_id = str(doc['id'])
            tenant_id = doc['tenant_id']
            doc_created = doc['created_at']
            filename = doc['filename']
            
            # Update embeddings for this tenant that were created around the same time
            # and don't have a document_id yet
            cur.execute("""
                UPDATE embeddings
                SET meta_data = jsonb_set(
                    COALESCE(meta_data, '{}'::jsonb),
                    '{document_id}',
                    %s::jsonb
                )
                WHERE tenant_id = %s
                  AND (meta_data IS NULL 
                       OR meta_data::text = '{}'
                       OR NOT (meta_data ? 'document_id'))
                  AND created_at >= %s::timestamp - interval '1 minute'
                  AND created_at <= %s::timestamp + interval '5 minutes'
                RETURNING id
            """, (json.dumps(doc_id), tenant_id, doc_created, doc_created))
            
            updated_ids = cur.fetchall()
            update_count = len(updated_ids)
            
            if update_count > 0:
                fixed_count += update_count
                print(f"Fixed {update_count} embeddings for document '{filename}' (ID: {doc_id})")
        
        # Check if there are still orphaned embeddings
        cur.execute("""
            SELECT COUNT(*) as count, tenant_id
            FROM embeddings 
            WHERE meta_data IS NULL 
               OR meta_data::text = '{}'
               OR NOT (meta_data ? 'document_id')
            GROUP BY tenant_id
        """)
        remaining = cur.fetchall()
        
        if remaining:
            print("\nWarning: Some embeddings could not be matched to documents:")
            for row in remaining:
                print(f"  - Tenant {row['tenant_id']}: {row['count']} embeddings")
            print("\nThese embeddings will be left as-is. Consider manually reviewing or deleting them.")
        
        # Commit the changes
        conn.commit()
        print(f"\nMigration completed successfully!")
        print(f"Total embeddings fixed: {fixed_count}")
        
        # Verify the fix
        cur.execute("""
            SELECT COUNT(*) as with_doc_id
            FROM embeddings 
            WHERE meta_data ? 'document_id'
        """)
        result = cur.fetchone()
        print(f"Embeddings with document_id: {result['with_doc_id']}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting embeddings metadata migration...")
    print("=" * 60)
    fix_embeddings_metadata()
    print("=" * 60)
    print("Migration finished!")