"""
Bedtime Story Time - FastAPI Backend
A Python backend for AI-powered children's storytelling using LangChain + Groq
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal, List
import os
from datetime import datetime
from dotenv import load_dotenv
import re
from io import BytesIO
from gtts import gTTS

# Import our custom modules
from agents import StorytellerAgent, JudgeAgent
from conversational_agent import ConversationalAgent
from mongodb import mongodb

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Bedtime Story API",
    description="AI-powered storytelling for children aged 5-10",
    version="1.0.0"
)

# Configure CORS to allow frontend to communicate with backend
# This allows your React app to make requests to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],  # Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize our AI agents
conversational_agent = ConversationalAgent(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    langsmith_api_key=os.getenv("LANGSMITH_API_KEY")
)

storyteller = StorytellerAgent(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    langsmith_api_key=os.getenv("LANGSMITH_API_KEY")
)

judge = JudgeAgent(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    langsmith_api_key=os.getenv("LANGSMITH_API_KEY")
)


# ===== DATA MODELS =====
# These classes define the structure of our API requests and responses

class ConversationRequest(BaseModel):
    """Request model for conversational messages"""
    message: str  # User's message
    conversation_history: Optional[List[dict]] = []  
    session_id: Optional[str] = None

class StoryRequest(BaseModel):
    """Request model for generating a new story"""
    prompt: str  
    lengthType: Literal["short", "medium", "long"] = "medium"  
    conversation_history: Optional[List[dict]] = []  
    session_id: Optional[str] = None


class StoryFeedback(BaseModel):
    """Quality feedback from the Judge Agent"""
    clarity: int  # 1-10: Language simplicity
    moralValue: int  # 1-10: Positive lessons
    ageAppropriateness: int  # 1-10: Suitable for 5-10 year-olds
    score: int  # 1-10: Overall quality
    approved: bool  # Whether story meets quality standards
    feedback: str  # Specific improvement suggestions


class Story(BaseModel):
    """Complete story with all metadata"""
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
# ===== Utilities =====
def sanitize_text(text: str) -> str:
    """Remove stray tokens like 'undefined', 'null', 'None' and normalize whitespace."""
    if not isinstance(text, str):
        text = str(text or "")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\b(undefined|null)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(undefined|null|none)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = text.strip()
    return text


def count_paragraphs(text: str) -> int:
    """Count paragraphs separated by a blank line (double newline)."""
    if not isinstance(text, str):
        return 0
    norm = re.sub(r"\r\n?", "\n", text.strip())
    # Split by blank lines
    paras = [p.strip() for p in re.split(r"\n\s*\n", norm) if p.strip()]
    return len(paras)


def build_structure_feedback(length_type: str) -> str:
    need = 2 if length_type == "short" else 3
    if need == 2:
        return (
            "Please reformat the story into EXACTLY 2 paragraphs separated by a single blank line.\n"
            "Paragraph 1: Introduction (setup characters and setting).\n"
            "Paragraph 2: Conclusion (resolve the story and state the gentle moral).\n"
            "Do not add headings; keep the same content and tone, only adjust paragraph breaks."
        )
    else:
        return (
            "Please reformat the story into EXACTLY 3 paragraphs separated by a single blank line.\n"
            "Paragraph 1: Introduction (setup characters and setting).\n"
            "Paragraph 2: Extension/Development (the adventure or challenge grows).\n"
            "Paragraph 3: Conclusion (resolution and gentle moral).\n"
            "Do not add headings; keep the same content and tone, only adjust paragraph breaks."
        )


#API ENDPOINTS 

@app.get("/")
async def root():
    """
    Health check endpoint - confirms the API is running
    """
    return {
        "message": "Bedtime Story API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/api/tts")
async def tts_endpoint(payload: dict):
    """Generate natural-sounding speech audio (MP3) for provided text using gTTS.
    Expects: { "text": string, "lang": optional ISO code (default "en"), "slow": optional bool }
    """
    try:
        text = payload.get("text", "")
        lang = payload.get("lang", "en")
        slow = bool(payload.get("slow", False))
        if not text or not isinstance(text, str):
            raise HTTPException(status_code=400, detail="text is required")

        norm = re.sub(r"\s+", " ", text).strip()
        norm = re.sub(r"([\.!?])([^ \n])", r"\1 \2", norm)
        norm = re.sub(r"\n\s*\n", ". . . ", norm)

        mp3_buffer = BytesIO()
        tts = gTTS(text=norm, lang=lang, slow=slow)
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        return StreamingResponse(mp3_buffer, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ConversationRequest):
    """
    Conversational endpoint - handles natural conversation
    
    This endpoint:
    1. Remembers user context (name, preferences)
    2. Filters inappropriate content
    3. Responds naturally without always generating stories
    4. Determines when to actually create a story
    
    Args:
        request: ConversationRequest with message and history
        
    Returns:
        dict: Response with type, message, and whether to generate story
    """
    try:
        print(f"Chat message: '{request.message}'")
        
        # Process message through conversational agent
        result = conversational_agent.process_message(
            message=request.message,
            conversation_history=request.conversation_history,
            session_id=request.session_id,
        )
        
        print(f"📊 Response type: {result['type']}")
        
        return {
            "success": True,
            "type": result['type'],
            "response": result['response'],
            "should_generate_story": result['should_generate_story'],
            "story_prompt": result['story_prompt']
        }
        
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-story", response_model=dict)
async def generate_story(request: StoryRequest):
    """
    Main endpoint to generate a bedtime story
    
    This endpoint orchestrates the entire story generation process:
    1. Gets previous stories for context
    2. Creates initial story with Storyteller Agent
    3. Evaluates quality with Judge Agent
    4. Refines story iteratively (up to 5 times)
    5. Optionally generates AI image
    6. Saves story to database
    
    Args:
        request: StoryRequest containing prompt and length preference
        
    Returns:
        dict: Success status and generated story data
    """
    try:
        print(f"Generating story for prompt: '{request.prompt}' (length: {request.lengthType})")
        
        # Step 1: Get previous stories for context from MongoDB
        # This helps maintain consistent tone and style across stories
        all_stories = mongodb.get_all_stories(session_id=request.session_id)
        previous_stories = all_stories[-3:] if len(all_stories) > 0 else []
        print(f"Found {len(previous_stories)} previous stories for context")
        
        # Step 2: Define word count targets based on selected length
        word_count_map = {
            "short": "300-400",
            "medium": "500-700",
            "long": "700-1000"  # Longer stories for better reading experience
        }
        target_word_count = word_count_map[request.lengthType]
        
        # Step 3: Iterative story generation with quality feedback
        current_story = ""
        current_title = ""
        iterations = 0
        max_iterations = 5
        final_feedback = None
        
        print(f"Starting iterative refinement (max {max_iterations} iterations)")
        
        while iterations < max_iterations:
            iterations += 1
            print(f"\n--- Iteration {iterations}/{max_iterations} ---")
            
            # Generate or refine story using Storyteller Agent
            if iterations == 1:
                # First iteration: Create initial story
                result = storyteller.create_story(
                    prompt=request.prompt,
                    target_word_count=target_word_count,
                    length_type=request.lengthType,
                    previous_stories=previous_stories
                )
            else:
                # Subsequent iterations: Refine based on judge feedback
                result = storyteller.refine_story(
                    title=current_title,
                    content=current_story,
                    feedback=final_feedback["feedback"],
                    length_type=request.lengthType
                )
            
            current_title = result["title"]
            current_story = result["content"]
            print(f"Story created: '{current_title}' ({len(current_story.split())} words)")
            # Enforce paragraph structure before judging
            need_paras = 2 if request.lengthType == "short" else 3
            actual_paras = count_paragraphs(current_story)
            if actual_paras != need_paras:
                print(f"Paragraph structure mismatch: need {need_paras}, got {actual_paras}. Requesting reformat...")
                structure_feedback = build_structure_feedback(request.lengthType)
                reform = storyteller.refine_story(
                    title=current_title,
                    content=current_story,
                    feedback=structure_feedback,
                    length_type=request.lengthType
                )
                current_title = reform["title"]
                current_story = reform["content"]
                # Recount after reformat
                actual_paras = count_paragraphs(current_story)
                print(f"After reformat, paragraphs: {actual_paras}")
            
            # Evaluate story quality using Judge Agent
            evaluation = judge.evaluate_story(
                title=current_title,
                content=current_story
            )
            
            final_feedback = evaluation
            print(f"⭐ Judge Score: {evaluation['score']}/10 (Approved: {evaluation['approved']})")
            print(f"   - Clarity: {evaluation['clarity']}/10")
            print(f"   - Moral Value: {evaluation['moralValue']}/10")
            print(f"   - Age Appropriate: {evaluation['ageAppropriateness']}/10")
            
            # Check if story meets quality standards
            # Require PERFECT score (9+) OR all metrics >= 8 to demonstrate refinement loop
            # This ensures at least 2-3 iterations for demo purposes
            all_metrics_good = (
                evaluation["clarity"] >= 8 and 
                evaluation["moralValue"] >= 8 and 
                evaluation["ageAppropriateness"] >= 8
            )
            
            if evaluation["score"] >= 9 and all_metrics_good:
                print(f"Story approved after {iterations} iteration(s)!")
                break
            else:
                print(f"Story needs refinement. Feedback: {evaluation['feedback'][:100]}...")
        
        # Step 4: Save story to local JSON file
        print("\nSaving story to local storage...")
        # Sanitize content/title before saving
        clean_title = sanitize_text(current_title)
        clean_content = sanitize_text(current_story)

        story_data = {
            "title": clean_title,
            "content": clean_content,
            "prompt": request.prompt,
            "length_type": request.lengthType,
            "iterations": iterations,
            "final_score": final_feedback,
            "age_range": "5-10",
            "image_url": None,  # Images will be generated by Pollinations.AI on frontend
            "session_id": request.session_id or None
        }
        
        saved_story = mongodb.save_story(story_data)
        print(f"Story saved with ID: {saved_story.get('_id', 'unknown')}")
        
        # Step 6: Return success response
        return {
            "success": True,
            "story": saved_story
        }
        
    except Exception as e:
        msg = str(e)
        print(f"❌ Error generating story: {msg}")
        lower = msg.lower()
        if ("rate limit" in lower) or ("429" in lower) or ("limit" in lower and "token" in lower):
            raise HTTPException(status_code=429, detail="Rate limit reached for the current Groq model(s). Please try again in a few minutes. We've enabled automatic fallback to alternate models—if this persists, set GROQ_MODEL env to a list like 'llama-3.3-70b-versatile, llama-3.1-70b-versatile, llama-3.3-8b-instant'.")
        raise HTTPException(status_code=500, detail=msg)


@app.get("/api/stories", response_model=dict)
async def get_stories(limit: int = 10, session_id: Optional[str] = None):
    """
    Get previous stories from MongoDB
    
    Args:
        limit: Maximum number of stories to return (default: 10)
        session_id: Optional session id to scope stories to current session
        
    Returns:
        dict: Success status and list of stories
    """
    try:
        all_stories = mongodb.get_all_stories(session_id=session_id)
        # Return most recent stories (already sorted by created_at in MongoDB)
        recent_stories = all_stories[:limit]
        return {
            "success": True,
            "stories": recent_stories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stories/{story_id}", response_model=dict)
async def get_story(story_id: str):
    """
    Get a specific story by ID
    
    Args:
        story_id: MongoDB ObjectId of the story
        
    Returns:
        dict: Success status and story data
    """
    try:
        story = mongodb.get_story_by_id(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        return {
            "success": True,
            "story": story
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the server when this file is executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"""
     ===== Bedtime Story API =====
     Server starting on http://{host}:{port}
     API Docs: http://{host}:{port}/docs
     Health Check: http://{host}:{port}/
    ================================
    """)
    
    uvicorn.run(app, host=host, port=port)
