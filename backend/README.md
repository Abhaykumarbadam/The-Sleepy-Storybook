# Python Backend Setup Guide

## 🐍 Complete Python Backend with FastAPI + LangChain

This backend replaces the Supabase Edge Functions with a Python FastAPI server that's easier to understand, debug, and explain!

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI server with all API endpoints
├── agents.py              # Storyteller and Judge AI agents (LangChain + Groq)
├── database.py            # Supabase PostgreSQL integration
├── image_generator.py     # Optional AI image generation (Stability AI)
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (API keys)
```

## 🚀 Quick Start

### Step 1: Install Python Dependencies

Open a new terminal and navigate to the backend folder:

```powershell
cd backend
pip install -r requirements.txt
```

This installs:
- **FastAPI**: Web framework for building APIs
- **LangChain**: Framework for building LLM applications
- **Groq**: Fast LLM inference
- **Supabase**: Database client
- **And more...**

### Step 2: Configure Environment Variables

Edit `backend/.env` and add your Supabase Service Role Key:

```env
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key_here
```

To get your Service Role Key:
1. Go to https://supabase.com/dashboard/project/cvwuoxaaickndqcwuqgx/settings/api
2. Copy the `service_role` key (NOT the anon key)
3. Paste it in the .env file

Optional keys (for enhanced features):
- `LANGSMITH_API_KEY` - For LLM tracing
- `STABILITY_API_KEY` - For AI image generation
- `GROQ_MODEL` / `GROQ_MODEL_STORYTELLER` / `GROQ_MODEL_JUDGE` / `GROQ_MODEL_CONVERSATION` – Comma-separated list of Groq model IDs to try in order. Used for automatic fallback when a model hits rate limits (429) or capacity.

Model selection examples (any of these env vars accept a comma-separated list; the first available will be used):

```env
# Apply to all agents
GROQ_MODEL=llama-3.3-70b-versatile, llama-3.1-70b-versatile, llama-3.3-8b-instant

# Or set per agent
GROQ_MODEL_STORYTELLER=llama-3.3-70b-versatile, llama-3.3-8b-instant
GROQ_MODEL_JUDGE=llama-3.3-8b-instant, llama-3.1-70b-versatile
GROQ_MODEL_CONVERSATION=llama-3.3-8b-instant
```

On Windows PowerShell (temporary for the current session):

```powershell
$env:GROQ_MODEL = "llama-3.3-70b-versatile, llama-3.1-70b-versatile, llama-3.3-8b-instant"
python main.py
```

### Step 3: Start the Backend Server

```powershell
python main.py
```

You should see:

```
🌙 ===== Bedtime Story API =====
📡 Server starting on http://0.0.0.0:8000
📖 API Docs: http://0.0.0.0:8000/docs
🔍 Health Check: http://0.0.0.0:8000/
================================
```

### Step 4: Start the Frontend

In a **separate terminal**:

```powershell
npm run dev
```

Your app is now running with Python backend! 🎉

## 📖 How It Works

### The Two-Agent System

```python
# 1. STORYTELLER AGENT (agents.py)
# Creates bedtime stories based on user prompts

storyteller = StorytellerAgent(groq_api_key)
story = storyteller.create_story(
    prompt="A brave little bunny",
    target_word_count="300-400"
)
# Returns: {"title": "...", "content": "..."}
```

```python
# 2. JUDGE AGENT (agents.py)
# Evaluates story quality on multiple dimensions

judge = JudgeAgent(groq_api_key)
evaluation = judge.evaluate_story(
    title=story["title"],
    content=story["content"]
)
# Returns: {
#   "clarity": 8,
#   "moralValue": 9,
#   "ageAppropriateness": 10,
#   "score": 9,
#   "approved": True,
#   "feedback": "Excellent story!"
# }
```

### The Iterative Refinement Loop

```python
# In main.py - The magic happens here!

iterations = 0
max_iterations = 5

while iterations < max_iterations:
    iterations += 1
    
    # Step 1: Create or refine story
    if iterations == 1:
        story = storyteller.create_story(prompt, word_count)
    else:
        story = storyteller.refine_story(title, content, feedback)
    
    # Step 2: Judge evaluates the story
    evaluation = judge.evaluate_story(title, content)
    
    # Step 3: Check if approved
    if evaluation["approved"] or evaluation["score"] >= 8:
        break  # Story is good enough!
    
    # Otherwise, loop continues with judge's feedback
```

### Database Operations

```python
# Save story to Supabase PostgreSQL
db = Database(url, service_role_key)

saved_story = db.save_story({
    "title": "The Brave Bunny",
    "content": "Once upon a time...",
    "prompt": "A brave little bunny",
    "length_type": "medium",
    "iterations": 3,
    "final_score": evaluation,
    "image_url": "https://..."
})
```

## 🎯 API Endpoints

### 1. Health Check

```bash
GET http://localhost:8000/
```

Response:
```json
{
  "message": "Bedtime Story API is running!",
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Generate Story

```bash
POST http://localhost:8000/api/generate-story
Content-Type: application/json

{
  "prompt": "A dragon who loves cookies",
  "lengthType": "medium"
}
```

Response:
```json
{
  "success": true,
  "story": {
    "id": "uuid-here",
    "title": "Sparkle the Cookie Dragon",
    "content": "Once upon a time...",
    "iterations": 2,
    "final_score": {
      "clarity": 9,
      "moralValue": 8,
      "ageAppropriateness": 10,
      "score": 9,
      "approved": true,
      "feedback": "Excellent story!"
    },
    ...
  }
}
```

### 3. Get Previous Stories

```bash
GET http://localhost:8000/api/stories?limit=10
```

Response:
```json
{
  "success": true,
  "stories": [
    {
      "id": "...",
      "title": "...",
      "content": "...",
      ...
    }
  ]
}
```

## 📚 Interactive API Documentation

FastAPI automatically generates interactive API docs!

Visit: **http://localhost:8000/docs**

Here you can:
- See all available endpoints
- Test API calls directly in your browser
- View request/response schemas
- Try different parameters

## 🔍 Code Walkthrough

### main.py - The Core Application

```python
@app.post("/api/generate-story")
async def generate_story(request: StoryRequest):
    """
    This function handles the entire story generation process
    
    Flow:
    1. Get previous stories for context
    2. Start iteration loop (max 5 times)
    3. Storyteller creates/refines story
    4. Judge evaluates quality
    5. Check if approved (score ≥ 8)
    6. If not approved, loop continues
    7. Optionally generate AI image
    8. Save to database
    9. Return to frontend
    """
```

### agents.py - The AI Brain

```python
class StorytellerAgent:
    """
    Uses Groq's LLM (llama-3.3-70b-versatile) to create stories
    
    - Temperature 0.8: Creative but not random
    - Structured prompts: Ensures consistent output
    - Context aware: References previous stories
    """
    
class JudgeAgent:
    """
    Uses same LLM but as a quality evaluator
    
    - Temperature 0.3: More consistent evaluation
    - Scores 4 dimensions: clarity, moral, age, overall
    - Provides actionable feedback
    """
```

### database.py - Data Persistence

```python
class Database:
    """
    Handles all Supabase PostgreSQL operations
    
    - save_story(): Insert new story
    - get_story(): Fetch by ID
    - get_previous_stories(): Get recent stories for context
    - update_story(): Modify existing story
    - delete_story(): Remove story
    """
```

## 🐛 Troubleshooting
### Groq 429 rate limit (tokens per day)

We now automatically fall back to alternate models when the primary model is rate limited. If all candidates are rate-limited or unavailable, the API returns HTTP 429 with a clear message. To tune the fallback order, set one of the `GROQ_MODEL*` env vars described above.

Recommended quick fix (PowerShell):

```powershell
$env:GROQ_MODEL = "llama-3.3-70b-versatile, llama-3.1-70b-versatile, llama-3.3-8b-instant"; python main.py
```


### "Module not found" error

```powershell
pip install -r requirements.txt
```

### "Cannot connect to database" error

1. Check `.env` has correct `SUPABASE_SERVICE_ROLE_KEY`
2. Get it from: https://supabase.com/dashboard/project/cvwuoxaaickndqcwuqgx/settings/api
3. Copy the `service_role` key (NOT anon key)

### "Frontend can't connect to backend"

1. Make sure backend is running (`python main.py`)
2. Check it's on port 8000: http://localhost:8000
3. Frontend expects backend at `http://localhost:8000`

### Port 8000 already in use

Change port in `.env`:
```env
PORT=8001
```

Also update frontend `.env`:
```env
VITE_API_URL=http://localhost:8001
```

## ✨ Why Python?

**Advantages over Supabase Edge Functions:**

1. **Easier to Understand**: Plain Python, clear code flow
2. **Better Debugging**: Use print statements, debuggers
3. **Faster Development**: No deployment needed, instant changes
4. **More Control**: Full access to Python ecosystem
5. **Better Error Messages**: See exact errors in terminal
6. **Explainable**: Perfect for demonstrations and teaching

## 🎓 Learning Resources

### Understanding the Code

Each file has extensive comments explaining:
- What each function does
- Why we use specific parameters
- How data flows through the system
- What each API call returns

### FastAPI Documentation

- Official Docs: https://fastapi.tiangolo.com/
- Tutorial: https://fastapi.tiangolo.com/tutorial/

### LangChain Documentation

- Official Docs: https://python.langchain.com/
- Groq Integration: https://python.langchain.com/docs/integrations/chat/groq

## 🚀 Next Steps

1. **Start the backend** (`python main.py`)
2. **Visit API docs** (http://localhost:8000/docs)
3. **Test an endpoint** (try the `/api/generate-story` endpoint)
4. **Read the code** (each file has detailed comments)
5. **Customize prompts** (modify agent prompts in `agents.py`)
6. **Add features** (the code is modular and extensible)

## 📊 Performance

- **Story generation**: 10-30 seconds (depending on iterations)
- **Groq LLM**: Very fast inference (~1-2 seconds per call)
- **Database operations**: <100ms
- **Image generation**: 5-10 seconds (if enabled)

## 🎉 You're Ready!

The Python backend is complete and documented. Every line has comments explaining what it does and why. Perfect for learning, presenting, and extending!

---

**Need help?** Check the comments in each Python file - they explain everything! 🐍✨
