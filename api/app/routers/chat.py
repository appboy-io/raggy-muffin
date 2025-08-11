from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_tenant_id, get_optional_user
from app.models import ChatSession, ChatMessage
from app.core.rag import retrieve_relevant_chunks, generate_answer
from app.utils.rate_limit import rate_limit_chat_endpoints
# from app.cache import cached, cache
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[str]
    contact_info: Dict[str, List[str]]
    categories: List[str]
    providers: List[str]
    message_id: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime

# @cached(key_prefix="chat_session", ttl=300)  # Cache for 5 minutes
async def get_cached_session(session_id: str, tenant_id: str, db: Session) -> Optional[ChatSession]:
    """Get chat session with caching"""
    try:
        return db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.tenant_id == tenant_id
        ).first()
    except Exception:
        return None

async def batch_add_messages(db: Session, messages: List[ChatMessage]) -> None:
    """Batch add messages for better performance"""
    try:
        db.add_all(messages)
        db.flush()  # Ensure IDs are assigned
    except Exception as e:
        logger.error(f"Error batch adding messages: {e}")
        raise

@router.post("/{tenant_id}/query", response_model=ChatResponse)
@rate_limit_chat_endpoints()
async def chat_query(
    tenant_id: str,
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Public chat endpoint for widgets - rate limited for protection
    """
    try:
        # Rate limiting implemented via decorator
        
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            
            # Create new session
            chat_session = ChatSession(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                session_id=session_id
            )
            db.add(chat_session)
        else:
            # Update existing session activity
            chat_session = await get_cached_session(session_id, tenant_id, db)
            
            if not chat_session:
                # Session not found, create new one
                chat_session = ChatSession(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    session_id=session_id
                )
                db.add(chat_session)
                # Clear cache for this session
                cache.delete(f"chat_session:{hash(f'{session_id}{tenant_id}')}")
        
        # Prepare user message
        user_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            tenant_id=tenant_id,
            message_type="user",
            content=request.message
        )
        
        # Retrieve relevant context
        logger.error(f"Chat query: '{request.message}' for tenant: {tenant_id}")
        context_chunks = await retrieve_relevant_chunks(
            query=request.message,
            tenant_id=tenant_id,
            db=db,
            top_k=4
        )
        logger.error(f"Retrieved {len(context_chunks)} context chunks")
        
        # Generate answer
        response_data = await generate_answer(request.message, context_chunks)
        
        # Prepare assistant response
        assistant_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            tenant_id=tenant_id,
            message_type="assistant",
            content=response_data["answer"],
            metadata={
                "sources": response_data["sources"],
                "contact_info": response_data["contact_info"],
                "categories": response_data["categories"],
                "providers": response_data["providers"]
            }
        )
        
        # Batch add messages for better performance
        await batch_add_messages(db, [user_message, assistant_message])
        
        # Update session activity
        chat_session.last_activity = datetime.utcnow()
        
        db.commit()
        
        return ChatResponse(
            answer=response_data["answer"],
            session_id=session_id,
            sources=response_data["sources"],
            contact_info=response_data["contact_info"],
            categories=response_data["categories"],
            providers=response_data["providers"],
            message_id=str(assistant_message.id)
        )
        
    except Exception as e:
        logger.error(f"Error processing chat query for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat query"
        )

@router.post("/query", response_model=ChatResponse)
async def authenticated_chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Authenticated chat endpoint for admin interface
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        chat_session = await get_cached_session(session_id, tenant_id, db)
        
        if not chat_session:
            chat_session = ChatSession(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                session_id=session_id
            )
            db.add(chat_session)
        
        # Prepare user message
        user_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            tenant_id=tenant_id,
            message_type="user",
            content=request.message
        )
        
        # Retrieve relevant context
        logger.error(f"Chat query: '{request.message}' for tenant: {tenant_id}")
        context_chunks = await retrieve_relevant_chunks(
            query=request.message,
            tenant_id=tenant_id,
            db=db,
            top_k=4
        )
        logger.error(f"Retrieved {len(context_chunks)} context chunks")
        
        # Generate answer
        response_data = await generate_answer(request.message, context_chunks)
        
        # Prepare assistant response
        assistant_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            tenant_id=tenant_id,
            message_type="assistant",
            content=response_data["answer"],
            metadata={
                "sources": response_data["sources"],
                "contact_info": response_data["contact_info"],
                "categories": response_data["categories"],
                "providers": response_data["providers"]
            }
        )
        
        # Batch add messages for better performance
        await batch_add_messages(db, [user_message, assistant_message])
        
        # Update session activity
        chat_session.last_activity = datetime.utcnow()
        
        db.commit()
        
        return ChatResponse(
            answer=response_data["answer"],
            session_id=session_id,
            sources=response_data["sources"],
            contact_info=response_data["contact_info"],
            categories=response_data["categories"],
            providers=response_data["providers"],
            message_id=str(assistant_message.id)
        )
        
    except Exception as e:
        logger.error(f"Error processing authenticated chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat query"
        )

@router.get("/sessions", response_model=List[ChatHistoryResponse])
async def get_chat_sessions(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = 50
):
    """Get chat session history for authenticated user"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.tenant_id == tenant_id
        ).order_by(ChatSession.last_activity.desc()).limit(limit).all()
        
        session_responses = []
        for session in sessions:
            # Get messages for this session
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at.asc()).all()
            
            message_list = [
                {
                    "id": str(msg.id),
                    "type": msg.message_type,
                    "content": msg.content,
                    "created_at": msg.created_at,
                    "metadata": msg.meta_data or {}
                }
                for msg in messages
            ]
            
            session_responses.append(ChatHistoryResponse(
                session_id=session.session_id,
                messages=message_list,
                created_at=session.created_at,
                last_activity=session.last_activity
            ))
        
        return session_responses
        
    except Exception as e:
        logger.error(f"Error retrieving chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )

@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get specific chat session history"""
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.tenant_id == tenant_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Get messages for this session
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        message_list = [
            {
                "id": str(msg.id),
                "type": msg.message_type,
                "content": msg.content,
                "created_at": msg.created_at,
                "metadata": msg.meta_data or {}
            }
            for msg in messages
        ]
        
        return ChatHistoryResponse(
            session_id=session.session_id,
            messages=message_list,
            created_at=session.created_at,
            last_activity=session.last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session"
        )

async def stream_chat_response(
    message: str,
    tenant_id: str,
    session_id: str,
    db: Session
) -> AsyncGenerator[str, None]:
    """Stream chat response using Server-Sent Events"""
    try:
        # Retrieve relevant context
        context_chunks = await retrieve_relevant_chunks(
            query=message,
            tenant_id=tenant_id,
            db=db,
            top_k=4
        )
        
        # Stream the response with preserved formatting
        full_response = ""
        async for chunk in generate_streaming_response(message, context_chunks):
            full_response += chunk
            # Send chunk as SSE
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        # Extract metadata for completion event
        from app.core.rag import extract_contact_info, extract_categories_from_chunks
        import re
        
        chunk_categories = extract_categories_from_chunks(context_chunks) if context_chunks else []
        contact_info = extract_contact_info(context_chunks) if context_chunks else {}
        
        providers = []
        if context_chunks:
            for chunk in context_chunks:
                # Look for patterns like "● Name, MD" or "● Name, NP"
                provider_matches = re.findall(r'●\s*([^●\n]+?(?:,\s*(?:MD|NP|DO|PA|RN))[^●\n]*)', chunk)
                for match in provider_matches:
                    provider = match.strip()
                    if provider and provider not in providers:
                        providers.append(provider)
                
                # Also look for structured format
                if "PROVIDER:" in chunk:
                    provider = chunk.split("PROVIDER:")[1].split('\n')[0].strip()
                    if provider and provider not in providers:
                        providers.append(provider)
        
        # Send completion event with metadata
        completion_data = {
            'type': 'complete',
            'session_id': session_id,
            'sources': context_chunks,
            'contact_info': contact_info,
            'categories': chunk_categories,
            'providers': providers
        }
        yield f"data: {json.dumps(completion_data)}\n\n"
        
        # Save the assistant message to the database
        chat_session = await get_cached_session(session_id, tenant_id, db)
        if chat_session:
            assistant_message = ChatMessage(
                id=uuid.uuid4(),
                session_id=chat_session.id,
                tenant_id=tenant_id,
                message_type="assistant",
                content=full_response,
                metadata={
                    "sources": context_chunks,
                    "contact_info": contact_info,
                    "categories": chunk_categories,
                    "providers": providers
                }
            )
            db.add(assistant_message)
            chat_session.last_activity = datetime.utcnow()
            db.commit()
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {e}")
        error_data = {
            'type': 'error',
            'message': 'Failed to process chat query'
        }
        yield f"data: {json.dumps(error_data)}\n\n"

async def generate_streaming_response(message: str, context_chunks: List[str]) -> AsyncGenerator[str, None]:
    """Generate streaming response using Ollama - collect full response first, then stream with formatting intact"""
    try:
        # Import here to avoid circular imports
        from app.core.rag import generate_single_prompt_response
        
        # Get the complete formatted response from Ollama first
        full_response = await generate_single_prompt_response(message, context_chunks)
        
        # Now stream the complete response in chunks that preserve formatting
        # Split by lines to maintain structure
        lines = full_response.split('\n')
        
        for line in lines:
            if not line:  # Empty line - preserve it
                yield '\n'
                await asyncio.sleep(0.02)
                continue
            
            # For lines with content, stream them word by word but keep line breaks intact
            words = line.split()
            word_count = 0
            
            for word in words:
                yield word + ' '
                word_count += 1
                
                # Small delay between words for readability
                # Slightly faster for non-header lines
                if ':' in line and word_count == 1:
                    await asyncio.sleep(0.05)  # Slower for headers
                else:
                    await asyncio.sleep(0.015)  # Faster for regular content
            
            # Add line break after each line
            yield '\n'
            
            # Small pause between lines for better readability
            await asyncio.sleep(0.03)
                    
    except Exception as e:
        logger.error(f"Error generating streaming response: {e}")
        # Fallback - just yield a simple error message
        yield "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

@router.post("/{tenant_id}/stream")
@rate_limit_chat_endpoints()
async def stream_chat_query(
    tenant_id: str,
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Streaming chat endpoint for widgets - rate limited for protection
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        chat_session = await get_cached_session(session_id, tenant_id, db)
        if not chat_session:
            chat_session = ChatSession(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                session_id=session_id
            )
            db.add(chat_session)
            db.commit()
        
        # Save user message
        user_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            tenant_id=tenant_id,
            message_type="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        
        # Return streaming response
        return StreamingResponse(
            stream_chat_response(request.message, tenant_id, session_id, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process streaming chat query"
        )

@router.post("/stream")
async def authenticated_stream_chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Authenticated streaming chat endpoint for admin interface
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        chat_session = await get_cached_session(session_id, tenant_id, db)
        if not chat_session:
            chat_session = ChatSession(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                session_id=session_id
            )
            db.add(chat_session)
            db.commit()
        
        # Save user message
        user_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_session.id,
            tenant_id=tenant_id,
            message_type="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        
        # Return streaming response
        return StreamingResponse(
            stream_chat_response(request.message, tenant_id, session_id, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in authenticated streaming endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process streaming chat query"
        )