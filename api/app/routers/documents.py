from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_tenant_id
from app.models import Document, Embedding
from app.core.document_processor import process_document, validate_file_size, get_file_type_from_filename
from app.core.embedding import chunk_text, embed_chunks_async
from app.config import config
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime
    error_message: Optional[str] = None

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    skip: int = 0,
    limit: int = 100
):
    """List all documents for the current tenant"""
    try:
        query = db.query(Document).filter(Document.tenant_id == tenant_id)
        total = query.count()
        documents = query.offset(skip).limit(limit).all()
        
        document_responses = [
            DocumentResponse(
                id=str(doc.id),
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                status=doc.status,
                chunk_count=doc.chunk_count,
                created_at=doc.created_at,
                error_message=doc.error_message
            )
            for doc in documents
        ]
        
        return DocumentListResponse(documents=document_responses, total=total)
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    extract_structured: bool = Form(False),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Get file type
        file_type = get_file_type_from_filename(file.filename)
        if not file_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if not validate_file_size(file_size, config.MAX_FILE_SIZE_MB):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {config.MAX_FILE_SIZE_MB}MB limit"
            )
        
        # Check document limit
        doc_count = db.query(Document).filter(Document.tenant_id == tenant_id).count()
        if doc_count >= config.MAX_DOCUMENTS_PER_TENANT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document limit ({config.MAX_DOCUMENTS_PER_TENANT}) exceeded"
            )
        
        # Create document record
        document = Document(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            status="processing",
            metadata={"extract_structured": extract_structured}
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document in background (for now, synchronously)
        try:
            # Extract text
            result = await process_document(file_content, file.filename, file_type)
            
            if not result["success"]:
                document.status = "failed"
                document.error_message = result["error"]
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document processing failed: {result['error']}"
                )
            
            text = result["text"]
            
            # Chunk text
            chunks = chunk_text(text)
            
            # Generate embeddings
            embedding_data = await embed_chunks_async(chunks, tenant_id)
            
            # Store embeddings
            embeddings = []
            for chunk_id, tenant, content, embedding in embedding_data:
                emb = Embedding(
                    id=uuid.uuid4(),
                    tenant_id=tenant,
                    content=content,
                    embedding=embedding,
                    metadata={"document_id": str(document.id)}
                )
                embeddings.append(emb)
            
            db.add_all(embeddings)
            
            # Update document status
            document.status = "completed"
            document.chunk_count = len(chunks)
            db.commit()
            
            logger.info(f"Successfully processed document {file.filename} with {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {file.filename}: {e}")
            document.status = "failed"
            document.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {str(e)}"
            )
        
        return DocumentResponse(
            id=str(document.id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
            error_message=document.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Delete a document and its embeddings"""
    try:
        # Find document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete associated embeddings
        db.query(Embedding).filter(
            Embedding.meta_data["document_id"].astext == document_id
        ).delete(synchronize_session=False)
        
        # Delete document
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get document details"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse(
            id=str(document.id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
            error_message=document.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )