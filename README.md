# 🌙 The Sleepy Storybook

An AI-powered storytelling app for children (ages 5-14) that creates personalized bedtime stories with beautiful illustrations.

## ✨ Features
- 💬 Chat with AI companion "Storybuddy" who remembers your name
- 🧠 **Context-Aware Stories** - AI remembers your conversation (like ChatGPT!)
- 📖 Generate custom stories with AI illustrations  
- 🔄 **Iterative Refinement** - Stories refined 2-4 times for perfect quality
- ⌨️ Typewriter effect - stories appear character-by-character
- 🌓 Animated dark mode toggle
- 🔊 Text-to-speech narration
- 🛡️ Automatic content filtering for child safety
- 📊 LangSmith monitoring for conversation tracking

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create `backend/.env`:
```
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

**Get API Keys:**
- **Groq API**: https://console.groq.com
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas/register
  1. Create free M0 cluster
  2. Create database user
  3. Whitelist IP (0.0.0.0/0 for dev)
  4. Get connection string (Drivers > Python)
  5. URL-encode special chars in password (@ = %40)

### 3. Run the App
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
npm run dev
```

Open: `http://localhost:5173`

## 🛠️ Tech Stack
- **Frontend:** React + TypeScript + Tailwind CSS
- **Backend:** Python + FastAPI + LangChain + Groq API
- **Database:** MongoDB Atlas (cloud storage)

