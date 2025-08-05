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
        
        # Import here to avoid circular imports
        from app.core.rag import generate_single_prompt_response
        
        # Stream the response
        full_response = ""
        async for chunk in generate_streaming_response(message, context_chunks):
            full_response += chunk
            # Send chunk as SSE
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        # Send completion event with metadata
        response_data = await generate_answer(message, context_chunks)
        completion_data = {
            'type': 'complete',
            'session_id': session_id,
            'sources': response_data['sources'],
            'contact_info': response_data['contact_info'],
            'categories': response_data['categories'],
            'providers': response_data['providers']
        }
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {e}")
        error_data = {
            'type': 'error',
            'message': 'Failed to process chat query'
        }
        yield f"data: {json.dumps(error_data)}\n\n"

async def generate_streaming_response(message: str, context_chunks: List[str]) -> AsyncGenerator[str, None]:
    """Generate streaming response using Ollama"""
    try:
        # Import here to avoid circular imports
        import ollama
        import os
        
        # Prepare context
        context = "\n---\n".join(context_chunks) if context_chunks else ""
        
        # Create prompt
        system_prompt = """You are Clara, a helpful and empathetic assistant that connects people with local aid services and resources."""
        
        user_prompt = f"""User Question: {message}

Available Information: {context}

Please provide a helpful response based on this information."""
        
        # Stream from Ollama
        host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        model = os.getenv('OLLAMA_CHAT_MODEL', 'llama3.2:3b-instruct-q4_0')
        
        def ollama_stream():
            return ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                stream=True,
                options={'host': host}
            )
        
        # Run Ollama stream in executor to avoid blocking
        loop = asyncio.get_event_loop()
        stream_generator = await loop.run_in_executor(None, ollama_stream)
        
        for chunk in stream_generator:
            if 'message' in chunk and 'content' in chunk['message']:
                content = chunk['message']['content']
                if content:
                    yield content
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
                    
    except Exception as e:
        logger.error(f"Error in Ollama streaming: {e}")
        # Fallback to non-streaming
        from app.core.rag import generate_single_prompt_response
        response = await generate_single_prompt_response(message, context_chunks)
        # Simulate streaming by sending chunks
        words = response.split()
        for i in range(0, len(words), 3):  # Send 3 words at a time
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.05)

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