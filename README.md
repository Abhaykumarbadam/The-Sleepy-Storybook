# 🌙 The Sleepy Storybook

An AI-powered storytelling app for children (ages 5-10) that creates personalized bedtime stories with beautiful illustrations and AI-driven conversation.

## ✨ Features

### 🤖 AI-Powered Story Generation
- 💬   Interactive Chat   - Talk with "Storybuddy" who remembers your name and preferences
- 🧠   Context-Aware Conversations   - AI remembers your entire conversation history
- 📖   Custom Story Creation   - Generate unique stories based on your ideas
- 🔄   Multi-Agent Refinement   - Stories evaluated and refined 2-4 times using LangGraph workflow
- 🎯   Quality Assurance   - Judge agent ensures age-appropriateness and moral values

### 🎨 User Experience
- ⌨️   Typewriter Effect   - Stories appear character-by-character for immersive reading
- 🌓   Dark/Light Mode   - Animated theme toggle for comfortable reading
- 🔊   Text-to-Speech   - Built-in narration for bedtime listening
- �️   AI Illustrations   - Beautiful images generated via Pollinations.AI

### 🛡️ Safety & Monitoring
- ✅   Content Filtering   - Automatic safety checks for child-appropriate content
- 📊   LangSmith Tracing   - Full conversation and workflow monitoring
- �   LangGraph Studio   - Visual debugging of AI agent interactions

## 🏗️ Architecture

### Frontend
-   React 18   with TypeScript
-   Tailwind CSS   for styling
-   Vite   for fast development
-   REST API   integration

### Backend
-   FastAPI   - High-performance Python web framework
-   LangChain   - LLM orchestration framework
-   LangGraph   - Multi-agent workflow engine
-   Groq API   - Ultra-fast LLM inference
-   JSON Storage   - Local file storage for conversation history

### AI Agents
-   Conversational Agent   - Handles chat and story requests
-   Storyteller Agent   - Creates and refines stories
-   Judge Agent   - Evaluates quality and appropriateness
-   Paragraph Formatter   - Ensures proper story structure

## 🚀 Quick Start

### 1. Prerequisites
-   Node.js   16+ (for frontend)
-   Python 3.11+   (for backend/LangGraph)
-   Git   (for cloning)

### 2. Install Dependencies

```bash
# Clone repository
git clone https://github.com/Abhaykumarbadam/The-Sleepy-Storybook.git
cd The-Sleepy-Storybook

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install backend as package (required for LangGraph)
pip install -e .
```

### 3. Set Up Environment Variables

Create `backend/.env`:

```env
# Required: Groq API for LLM inference
GROQ_API_KEY=your_groq_api_key_here

# Optional: LangSmith for tracing (recommended)
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=bedtime-stories
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Optional: Server configuration
HOST=0.0.0.0
PORT=8000
```

  Get API Keys:  
-   Groq API  : https://console.groq.com (free tier available)
-   LangSmith  : https://smith.langchain.com (free tier for debugging)

### 4. Run the Application

#### Option 1: Standard Mode (FastAPI Server)

```bash
# Terminal 1: Start Backend
cd backend
python main.py

# Terminal 2: Start Frontend
npm run dev
```

#### Option 2: LangGraph Studio Mode (with Visual Debugging)

```bash
# Terminal 1: Start LangGraph Server
cd backend
langgraph dev --port 2024

# Terminal 2: Start Frontend
npm run dev
```

  Access Points:  
- 🎨   Frontend  : http://localhost:5173
- 🚀   Backend API  : http://localhost:8000
- 📚   API Docs  : http://localhost:8000/docs
- 🔍   LangGraph Studio  : https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

## 📂 Project Structure

```
The-Sleepy-Storybook/
├── src/                          # Frontend React app
│   ├── components/               # React components
│   │   ├── ChatInterface.tsx     # Main chat UI
│   │   ├── OpeningScreen.tsx     # Landing page
│   │   ├── StoryEditor.tsx       # Story display
│   │   └── ThemeToggle.tsx       # Dark mode toggle
│   ├── lib/
│   │   └── api.ts               # API client
│   └── styles/                   # CSS styles
│
├── backend/                      # Python backend
│   ├── main.py                  # FastAPI server
│   ├── agents.py                # AI agents (Storyteller, Judge)
│   ├── conversational_agent.py  # Chat handler
│   ├── langgraph_workflow.py    # Multi-agent workflows
│   ├── langgraph_server.py      # LangGraph API wrapper
│   ├── storage.py               # JSON storage operations
│   ├── langgraph.json           # LangGraph configuration
│   ├── setup.py                 # Package configuration
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables
│
├── SETUP_GUIDE.md               # Detailed setup instructions
└── README.md                    # This file
```

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
|   Frontend   | React, TypeScript, Tailwind CSS, Vite |
|   Backend   | FastAPI, Python 3.11+ |
|   AI/LLM   | LangChain, LangGraph, Groq API |
|   Storage   | JSON File Storage |
|   Monitoring   | LangSmith (tracing & debugging) |
|   Image Gen   | Pollinations.AI |
|   TTS   | gTTS (Google Text-to-Speech) |

## � Documentation

-   [SETUP_GUIDE.md](./SETUP_GUIDE.md)   - Comprehensive setup and troubleshooting
-   [backend/README.md](./backend/README.md)   - Backend architecture details
-   API Docs   - Interactive Swagger docs at `/docs` when server is running

## 🎯 Use Cases

1.   Bedtime Stories   - Parents can generate personalized stories for their children
2.   Educational Content   - Stories with moral lessons and age-appropriate themes
3.   Interactive Reading   - Children can request story modifications in real-time
4.   Language Learning   - Stories adapted for different reading levels

## 🔧 Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
npm test
```

### LangGraph Studio Debugging

1. Start LangGraph server: `langgraph dev --port 2024`
2. Open Studio: https://smith.langchain.com/studio
3. Connect to: http://127.0.0.1:2024
4. View real-time graph execution and agent interactions

### Environment Setup

  For LangGraph development   (requires Python 3.11+):
```bash
# Windows PowerShell
py -3.12 -m pip install -e .
py -3.12 -m pip install -U "langgraph-cli[inmem]"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request


  Happy Storytelling! 📚✨  

