"""
LangGraph Server - FastAPI Wrapper for LangGraph Workflows

This provides a REST API to interact with the LangGraph conversation and story generation graphs.
Run with: uvicorn langgraph_server:app --port 2024 --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
import os
from dotenv import load_dotenv

load_dotenv()

from langgraph_workflow import (
    create_complete_workflow,
    run_conversation,
    run_story_generation
)

# Initialize FastAPI app
app = FastAPI(
    title="Bedtime Stories LangGraph API",
    description="LangGraph-powered multi-agent workflow for bedtime stories",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graphs
conversation_graph = None
story_graph = None


@app.on_event("startup")
async def startup_event():
    """Initialize LangGraph workflows on startup"""
    global conversation_graph, story_graph
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
    
    print("🚀 Initializing LangGraph workflows...")
    conversation_graph, story_graph = create_complete_workflow(
        groq_api_key=groq_api_key,
        langsmith_api_key=langsmith_api_key
    )
    print("✅ LangGraph server ready!")


# Request/Response Models
class ConversationRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    story_length: Literal["short", "medium", "long"] = "medium"


class ConversationResponse(BaseModel):
    response: str
    should_generate_story: bool
    story_prompt: Optional[str] = None
    story_length: str


class StoryRequest(BaseModel):
    prompt: str
    length_type: Literal["short", "medium", "long"] = "medium"
    session_id: Optional[str] = "default"
    max_iterations: Optional[int] = 3


class StoryResponse(BaseModel):
    title: str
    content: str
    prompt: str
    length_type: str
    iterations: int
    final_scores: dict
    overall_score: int
    paragraph_count: int


# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "LangGraph Bedtime Stories API",
        "endpoints": {
            "conversation": "/api/conversation",
            "story": "/api/story",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "conversation_graph": conversation_graph is not None,
        "story_graph": story_graph is not None
    }


@app.post("/api/conversation", response_model=ConversationResponse)
async def conversation_endpoint(request: ConversationRequest):
    """
    Process a conversation message through the LangGraph conversation workflow.
    
    This handles natural conversation, detects story requests, and extracts user preferences.
    """
    if conversation_graph is None:
        raise HTTPException(status_code=503, detail="Conversation graph not initialized")
    
    try:
        result = run_conversation(
            graph=conversation_graph,
            user_message=request.message,
            session_id=request.session_id,
            story_length=request.story_length
        )
        
        return ConversationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation error: {str(e)}")


@app.post("/api/story", response_model=StoryResponse)
async def story_endpoint(request: StoryRequest):
    """
    Generate a bedtime story through the LangGraph story generation workflow.
    
    This uses the reflection pattern with iterative improvement via the Judge agent.
    """
    if story_graph is None:
        raise HTTPException(status_code=503, detail="Story graph not initialized")
    
    try:
        result = run_story_generation(
            graph=story_graph,
            prompt=request.prompt,
            length_type=request.length_type,
            session_id=request.session_id,
            max_iterations=request.max_iterations
        )
        
        return StoryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation error: {str(e)}")


@app.get("/api/graphs")
async def list_graphs():
    """List available LangGraph workflows"""
    return {
        "graphs": [
            {
                "name": "conversation",
                "description": "Natural conversation with story request detection",
                "status": "ready" if conversation_graph else "not initialized"
            },
            {
                "name": "story_generation",
                "description": "Iterative story creation with reflection pattern",
                "status": "ready" if story_graph else "not initialized"
            }
        ],
        "langsmith_enabled": os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "langsmith_project": os.getenv("LANGSMITH_PROJECT", "bedtime-stories")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2024)
