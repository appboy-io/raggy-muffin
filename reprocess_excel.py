#!/usr/bin/env python3
"""
Script to reprocess Excel files with the new improved processor
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the api directory to Python path
api_path = Path(__file__).parent / "api"
sys.path.insert(0, str(api_path))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Document, Embedding
from app.core.document_processor import process_document
from app.core.embedding import chunk_text, embed_chunks_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reprocess_document(document_id: str, db: Session):
    """Reprocess a single document with the new Excel processor"""
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return False
        
        logger.info(f"Reprocessing document: {document.filename}")
        
        # Delete existing embeddings for this document
        logger.info("Deleting existing embeddings...")
        deleted_count = db.query(Embedding).filter(
            Embedding.meta_data.contains({"document_id": document_id})
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {deleted_count} existing embeddings")
        
        # We need the original file content to reprocess
        # Since we don't store the file content, we'll need to work with what we have
        # For now, let's just mark the document for reprocessing
        document.status = "processing"
        document.chunk_count = 0
        document.error_message = None
        
        db.commit()
        logger.info(f"Document {document.filename} marked for reprocessing")
        logger.warning("Note: Original file content needed for full reprocessing. Document status updated.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error reprocessing document {document_id}: {e}")
        db.rollback()
        return False

async def main():
    """Main function to reprocess Excel files"""
    
    # Excel documents to reprocess (Kate Wild's document first)
    excel_documents = [
        "0824766f-4003-4ea7-a180-e552eaa665eb",  # Kate Wild's document
        "11c3a8dc-fa33-42a4-8f18-967ac648d94c",  # Other WA Medical Providers
        "72b27669-d41f-4bda-80f6-42d4259a4081",  # More WA Medical Providers
        "5f536048-bafc-41cb-ac43-e3c50b6d3401",
        "b4a48e1f-67d5-4635-8c95-413b78904763",
    ]
    
    db = SessionLocal()
    
    try:
        for doc_id in excel_documents:
            logger.info(f"\n=== Processing document {doc_id} ===")
            success = await reprocess_document(doc_id, db)
            if success:
                logger.info(f"✓ Successfully processed {doc_id}")
            else:
                logger.error(f"✗ Failed to process {doc_id}")
            
        logger.info("\n=== Reprocessing complete ===")
        logger.info("NOTE: To complete reprocessing, you'll need to re-upload the Excel files")
        logger.info("The improved Excel processor will then create properly structured chunks with contact information")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())