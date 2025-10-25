"""
Stories Routes Module

Handles story generation, retrieval, and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Literal, List
import os
from datetime import datetime

from langchain_core.tracers.context import tracing_v2_enabled

from api.dependencies import get_storyteller_agent, get_judge_agent, get_database
from agents import StorytellerAgent, JudgeAgent
from langgraph_workflow import create_complete_workflow, run_story_generation
from utils import (
    validate_prompt, 
    sanitize_input,
    count_paragraphs,
    setup_logger
)
from config import settings, HTTPStatus, APIMessages

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["stories"])


# ===== Request/Response Models =====

class StoryRequest(BaseModel):
    """Request model for generating a new story."""
    prompt: str
    lengthType: Literal["short", "medium", "long"] = "medium"
    conversation_history: Optional[List[dict]] = []
    session_id: Optional[str] = None


class StoryFeedback(BaseModel):
    """Quality feedback from the Judge Agent."""
    clarity: int
    moralValue: int
    ageAppropriateness: int
    score: int
    approved: bool
    feedback: str


class Story(BaseModel):
    """Complete story with all metadata."""
    id: str
    title: str
    content: str
    prompt: str
    length_type: str
    iterations: int
    final_score: Optional[StoryFeedback]
    age_range: str = "5-10"
    image_url: Optional[str] = None
    created_at: str
    updated_at: str


# ===== Routes =====

@router.post("/generate-story", response_model=dict)
async def generate_story(
    request: StoryRequest,
    storyteller: StorytellerAgent = Depends(get_storyteller_agent),
    judge: JudgeAgent = Depends(get_judge_agent),
    db = Depends(get_database)
):
    """
    Main endpoint to generate a bedtime story.
    
    This endpoint orchestrates the entire story generation process:
    1. Gets previous stories for context
    2. Creates initial story with Storyteller Agent
    3. Evaluates quality with Judge Agent
    4. Refines story iteratively (up to configured max)
    5. Saves story to database
    
    Uses session-level tracing to group all LLM calls in one trace.
    
    Args:
        request: StoryRequest containing prompt and length preference
        storyteller: StorytellerAgent dependency
        judge: JudgeAgent dependency
        db: Database dependency
        
    Returns:
        dict: Success status and generated story data
    """
    try:
        # Validate input
        is_valid, error_message = validate_prompt(request.prompt)
        if not is_valid:
            logger.warning(f"❌ Invalid prompt: {error_message}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=error_message
            )
        
        # Sanitize input
        clean_prompt = sanitize_input(request.prompt)
        logger.info(
            f"📖 Generating story for prompt: '{clean_prompt[:50]}...' "
            f"(length: {request.lengthType})"
        )
        
        # Check if LangSmith tracing is enabled
        langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        
        # Wrap the entire story generation process in one trace
        if langsmith_enabled:
            with tracing_v2_enabled(
                project_name=os.getenv("LANGCHAIN_PROJECT", "bedtime-stories")
            ):
                return await _generate_story_internal(
                    request, clean_prompt, storyteller, judge, db
                )
        else:
            return await _generate_story_internal(
                request, clean_prompt, storyteller, judge, db
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating story: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=APIMessages.ERROR_STORY_GENERATION
        )


async def _generate_story_internal(
    request: StoryRequest,
    clean_prompt: str,
    storyteller: StorytellerAgent,
    judge: JudgeAgent,
    db
) -> dict:
    """
    Internal story generation using LangGraph workflow.
    
    This creates beautiful multi-agent traces in LangSmith with:
    - Named nodes (StoryCreator, StoryEvaluator, etc.)
    - Conditional routing visualization
    - State management across iterations
    
    Args:
        request: StoryRequest
        clean_prompt: Sanitized prompt
        storyteller: StorytellerAgent (not used directly, kept for compatibility)
        judge: JudgeAgent (not used directly, kept for compatibility)
        db: Database instance
        
    Returns:
        dict with story data
    """
    logger.info(f"🎨 Generating story via LangGraph workflow")
    
    # Get API keys
    groq_api_key = os.getenv("GROQ_API_KEY")
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    # Create LangGraph workflow (this creates the beautiful graph structure!)
    _, story_app = create_complete_workflow(
        groq_api_key=groq_api_key,
        langsmith_api_key=langsmith_api_key
    )
    
    # Run story generation through the graph
    logger.info(f"🚀 Running story generation graph for prompt: '{clean_prompt[:50]}...'")
    final_story = run_story_generation(
        graph=story_app,
        prompt=clean_prompt,
        length_type=request.lengthType,
        session_id=request.session_id or "default"
    )
    
    # Check if we got a valid result
    if not final_story or not isinstance(final_story, dict):
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Story generation failed to produce a valid result"
        )
    
    logger.info(
        f"✅ Story generated in {final_story.get('iterations', 0)} iterations "
        f"(score: {final_story.get('overall_score', 0)}/10)"
    )
    
    # Save to database
    story_data = {
        "title": final_story["title"],
        "content": final_story["content"],
        "prompt": clean_prompt,
        "length_type": request.lengthType,
        "iterations": final_story["iterations"],
        "final_score": {
            "clarity": final_story["final_scores"]["clarity"],
            "moralValue": final_story["final_scores"]["moral_value"],
            "ageAppropriateness": final_story["final_scores"]["age_appropriateness"],
            "score": final_story["overall_score"],
            "approved": True,
            "feedback": f"Story approved after {final_story['iterations']} iterations"
        },
        "session_id": request.session_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    saved_story = db.save_story(story_data)
    
    logger.info(f"💾 Story saved to database with ID: {saved_story.get('id', 'N/A')}")
    
    return {
        "success": True,
        "story": saved_story,
        "message": "Story generated successfully via LangGraph workflow!"
    }


@router.get("/stories", response_model=dict)
async def get_stories(
    limit: int = 10,
    session_id: Optional[str] = None,
    db = Depends(get_database)
):
    """
    Get previous stories from database.
    
    Args:
        limit: Maximum number of stories to return (default: 10)
        session_id: Optional session id to scope stories
        db: Database dependency
        
    Returns:
        dict: Success status and list of stories
    """
    try:
        all_stories = db.get_all_stories(session_id=session_id)
        recent_stories = all_stories[:limit]
        
        logger.info(f"📚 Retrieved {len(recent_stories)} stories")
        
        return {
            "success": True,
            "stories": recent_stories
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving stories: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=APIMessages.INTERNAL_ERROR
        )


@router.get("/stories/{story_id}", response_model=dict)
async def get_story(
    story_id: str,
    db = Depends(get_database)
):
    """
    Get a specific story by ID.
    
    Args:
        story_id: Unique ID of the story
        db: Storage dependency
        
    Returns:
        dict: Success status and story data
    """
    try:
        story = db.get_story_by_id(story_id)
        
        if not story:
            logger.warning(f"❌ Story not found: {story_id}")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=APIMessages.STORY_NOT_FOUND
            )
        
        logger.info(f"📖 Retrieved story: {story_id}")
        
        return {
            "success": True,
            "story": story
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving story {story_id}: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=APIMessages.INTERNAL_ERROR
        )
