"""
Conversation Routes Module

Handles conversational interactions with users.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import os

from langchain_core.tracers.context import tracing_v2_enabled

from api.dependencies import get_conversational_agent
from conversational_agent import ConversationalAgent
from utils import validate_message, sanitize_input, setup_logger
from config import HTTPStatus, APIMessages

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["conversation"])


# ===== Request/Response Models =====

class ConversationRequest(BaseModel):
    """Request model for conversational messages."""
    message: str
    conversation_history: Optional[List[dict]] = []
    session_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response model for conversation endpoint."""
    success: bool
    type: str
    response: str
    should_generate_story: bool
    story_prompt: Optional[str] = None


# ===== Routes =====

@router.post("/chat", response_model=ConversationResponse)
async def chat(
    request: ConversationRequest,
    agent: ConversationalAgent = Depends(get_conversational_agent)
):
    """
    Conversational endpoint - handles natural conversation.
    
    This endpoint:
    1. Remembers user context (name, preferences)
    2. Filters inappropriate content
    3. Responds naturally without always generating stories
    4. Determines when to actually create a story
    
    Uses session-level tracing to group all LLM calls in one trace.
    
    Args:
        request: ConversationRequest with message and history
        agent: ConversationalAgent dependency injection
        
    Returns:
        ConversationResponse with type, message, and story generation flag
    """
    try:
        # Validate input
        is_valid, error_message = validate_message(request.message)
        if not is_valid:
            logger.warning(f"❌ Invalid message: {error_message}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=error_message
            )
        
        # Sanitize input
        clean_message = sanitize_input(request.message)
        logger.info(f"💬 Chat message: '{clean_message[:50]}...'")
        
        # Check if LangSmith tracing is enabled
        langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        
        # Process message with session-level tracing
        if langsmith_enabled:
            # One trace for the entire conversation session
            with tracing_v2_enabled(
                project_name=os.getenv("LANGCHAIN_PROJECT", "bedtime-stories")
            ):
                result = agent.process_message(
                    message=clean_message,
                    conversation_history=request.conversation_history,
                    session_id=request.session_id,
                )
        else:
            # No tracing
            result = agent.process_message(
                message=clean_message,
                conversation_history=request.conversation_history,
                session_id=request.session_id,
            )
        
        logger.info(f"📊 Response type: {result['type']}")
        
        return ConversationResponse(
            success=True,
            type=result['type'],
            response=result['response'],
            should_generate_story=result['should_generate_story'],
            story_prompt=result.get('story_prompt')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in chat: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=APIMessages.INTERNAL_ERROR
        )
