"""
Conversational Agent for Bedtime Story Time
Handles natural conversation, context memory, and content filtering
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List, Optional
import os
import re


class ConversationalAgent:
    """
    A conversational AI agent that:
    1. Remembers user context (name, preferences)
    2. Filters inappropriate content
    3. Responds naturally without always generating stories
    4. Determines when to actually create a story
    """
    
    def __init__(self, groq_api_key: str, langsmith_api_key: Optional[str] = None):
        """Initialize the conversational agent"""
        
        # Set up LangSmith tracing (optional)
        if langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "bedtime-stories")
        
        # Groq model fallback setup
        self.groq_api_key = groq_api_key
        env_list = os.getenv("GROQ_MODEL_CONVERSATION") or os.getenv("GROQ_MODEL") or ""
        self.model_candidates = [m.strip() for m in env_list.split(",") if m.strip()] or [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]
        self.temperature = 0.7
        self.max_tokens = 500
        self.llm = None

        # Session-scoped user context memory { session_id: { name, age, ... } }
        self.sessions: Dict[str, Dict[str, any]] = {}

        # Inappropriate topics for children (5-10 years old)
        self.inappropriate_keywords = [
            'murder', 'kill', 'death', 'die', 'blood', 'violence', 'gun', 'weapon',
            'scary', 'horror', 'nightmare', 'ghost', 'monster', 'demon', 'evil',
            'adult', 'sex', 'drug', 'alcohol', 'cigarette', 'war', 'fight', 'hurt',
            'abuse', 'kidnap', 'steal', 'crime', 'prison', 'jail'
        ]
        
        print("Conversational Agent initialized (Groq) with model fallback:", ", ".join(self.model_candidates))

    def _invoke_with_fallback(self, messages):
        last_err = None
        for model in self.model_candidates:
            try:
                self.llm = ChatGroq(
                    model=model,
                    api_key=self.groq_api_key,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return self.llm.invoke(messages)
            except Exception as e:
                msg = str(e).lower()
                last_err = e
                print(f"⚠️ Conversation model '{model}' failed: {e}")
                if ("rate limit" in msg) or ("429" in msg) or ("limit" in msg and "token" in msg) or ("decommission" in msg) or ("invalid" in msg):
                    print("↪️ Trying next Groq model due to rate limit or model issue...")
                    continue
                else:
                    break
        raise last_err if last_err else RuntimeError("All Groq models failed for conversation")
    
    def _get_session(self, session_id: Optional[str]) -> Dict[str, any]:
        sid = session_id or "default"
        if sid not in self.sessions:
            self.sessions[sid] = {}
        return self.sessions[sid]

    def extract_user_info(self, message: str, session_id: Optional[str]) -> None:
        """Extract and store user information from message"""
        ctx = self._get_session(session_id)
        
        # Extract name
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"call me (\w+)",
            r"this is (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message.lower())
            if match:
                ctx['name'] = match.group(1).capitalize()
                print(f"📝 Learned user's name: {ctx['name']}")
                break
        
        # Extract age
        age_pattern = r"i(?:'m| am) (\d+) years? old"
        age_match = re.search(age_pattern, message.lower())
        if age_match:
            ctx['age'] = int(age_match.group(1))
            print(f"Learned user's age: {ctx['age']}")
    
    def is_inappropriate_content(self, message: str) -> bool:
        """Check if message contains inappropriate content for children"""
        message_lower = message.lower()
        
        for keyword in self.inappropriate_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    def should_generate_story(self, message: str) -> bool:
        """Determine if the message is requesting a story"""
        
        story_request_keywords = [
            'tell me a story', 'story about', 'write a story', 'create a story',
            'make a story', 'i want a story', 'can you tell', 'tell a story',
            'story time', 'bedtime story', 'once upon a time'
        ]
        
        message_lower = message.lower()
        
        for keyword in story_request_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    def is_question_about_self(self, message: str) -> bool:
        """Check if user is asking about themselves (name, age, etc.)"""
        
        self_questions = [
            'what is my name', 'what\'s my name', 'whats my name',
            'do you know my name', 'remember my name', 'my name',
            'who am i', 'do you remember me', 'what do you know about me'
        ]
        
        message_lower = message.lower()
        
        for question in self_questions:
            if question in message_lower:
                return True
        
        return False
    
    def generate_conversational_response(self, message: str, conversation_history: List[dict], session_id: Optional[str]) -> str:
        """Generate a natural conversational response"""
        ctx = self._get_session(session_id)
        # Build conversation context
        context = ""
        if ctx.get('name'):
            context += f"User's name: {ctx['name']}\n"
        if ctx.get('age'):
            context += f"User's age: {ctx['age']}\n"
        
        # Create comprehensive system message with personality
        system_prompt = f"""You are Storybuddy, a magical AI friend and storytelling companion for children aged 5-14 years old.

🎭 YOUR PERSONALITY:
- Warm, friendly, and enthusiastic like a favorite teacher
- Patient, encouraging, and always positive  
- Playful and imaginative but also helpful and informative
- You LOVE stories, reading, and creativity
- You remember details about your friends (the children you talk to)
- You speak in a simple, clear way that kids understand

💬 HOW YOU TALK:
- Use simple words and short sentences
- Be conversational and natural (like talking to a friend)
- Use emojis occasionally to be engaging 😊 ✨ 📚
- Ask questions to understand what they want
- Show excitement about their ideas!
- Keep responses brief (2-4 sentences usually)
- Never use complex words or adult language

🎨 WHAT YOU CAN DO:
1. Have normal conversations (greetings, how are you, what's your favorite color, etc.)
2. Answer questions about stories, books, characters, imagination
3. Help brainstorm story ideas and characters
4. Chat about their day, interests, hobbies
5. Tell jokes and riddles appropriate for kids
6. Remember their name, age, and preferences
7. Suggest story modifications (make it funnier, add a character, change ending)
8. Be a creative companion and friend

❌ WHAT YOU DON'T DO IN CHAT:
- Don't write full stories in chat (you detect when they want a story and trigger the story generator)
- Don't use scary, violent, or inappropriate content
- Don't be preachy or lecture-like
- Don't use complicated explanations

📖 WHEN THEY ASK FOR A STORY:
When they say things like "write a story about..." or "tell me a story...", you respond with brief enthusiasm like:
"Ooh, I love that idea! Let me create that story for you! ✨"
(The system will then generate the actual story in a separate story editor with images)

🛡️ SAFETY:
- If they ask for inappropriate content (violence, scary, adult topics), gently redirect:
  "That might be too scary! How about we make a fun adventure story instead? 🌟"
- Always keep language appropriate for ages 5-14
- Be encouraging and build confidence

{context if context else ""}

Recent conversation:
{self._format_conversation_history(conversation_history[-4:])}

Remember: You're a friend who makes reading and storytelling magical! Be helpful, fun, and kind! ✨"""
        
        # Generate response
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        response = self._invoke_with_fallback(messages)
        return response.content
    
    def _format_conversation_history(self, history: List[dict]) -> str:
        """Format conversation history for context"""
        formatted = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "You"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    def _build_context_aware_prompt(self, message: str, conversation_history: List[dict], session_id: Optional[str]) -> str:
        ctx = self._get_session(session_id)
        
        # If message already contains specific details, use it directly
        if any(word in message.lower() for word in ['about', 'with', 'where', 'who', 'dragon', 'princess', 'knight', 'space', 'ocean']):
            return message
        
        # Get last 5-8 messages for context analysis
        recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
        
        if not recent_history:
            # No history, just use the raw message
            return message
        
        # Build conversation context for LLM to analyze
        conversation_context = self._format_conversation_history(recent_history)
        
        # Ask LLM to extract story themes from conversation
        system_prompt = """You are a context analyzer. Your job is to read a conversation and figure out what story the user wants.

RULES:
1. Look at the recent conversation for hints about interests, topics, places, or themes
2. If user mentioned specific interests (like "I love Japan", "I like dragons", "space is cool"), incorporate those
3. If user has a name/age, you can reference that
4. Create a brief story prompt (1-2 sentences) that captures their interests
5. If there's NO useful context, just return a generic prompt like "an exciting adventure"

Examples:
- User talked about Japan → "A story about exploring Japan"
- User loves dragons → "A story about a friendly dragon"  
- User mentioned being scared of dark → "A comforting bedtime story with gentle magic"
- No context → "An exciting adventure"

Conversation:
{conversation}

User's request: "{request}"

Return ONLY the story prompt (1-2 sentences), nothing else."""

        try:
            messages = [
                SystemMessage(content=system_prompt.format(
                    conversation=conversation_context,
                    request=message
                )),
                HumanMessage(content="What story prompt should I use based on this conversation?")
            ]
            
            response = self._invoke_with_fallback(messages)
            context_aware_prompt = response.content.strip()
            
            print(f"💡 Context-aware prompt generated: '{context_aware_prompt}'")
            return context_aware_prompt
            
        except Exception as e:
            print(f"⚠️ Error building context-aware prompt: {e}")
            # Fallback to original message
            return message
    
    def process_message(self, message: str, conversation_history: List[dict] = None, session_id: Optional[str] = None) -> Dict:
        """
        Process user message and determine appropriate response
        
        Returns:
            {
                'type': 'conversation' | 'story_request' | 'inappropriate',
                'response': str,
                'should_generate_story': bool,
                'story_prompt': Optional[str]
            }
        """
        if conversation_history is None:
            conversation_history = []
        
        # Extract user info
        self.extract_user_info(message, session_id)
        
        # Check for inappropriate content
        if self.is_inappropriate_content(message):
            ctx = self._get_session(session_id)
            name_part = f"{ctx.get('name', 'friend')}, " if ctx.get('name') else ""
            return {
                'type': 'inappropriate',
                'response': f"Oh {name_part}I'm sorry, but I can only create stories that are fun and safe for children. How about we try a different adventure? Maybe something with friendly animals, magic, or exploring new places? 🌟",
                'should_generate_story': False,
                'story_prompt': None
            }
        
        # Check if asking about themselves
        if self.is_question_about_self(message):
            ctx = self._get_session(session_id)
            if ctx.get('name'):
                response = f"Of course I remember you, {ctx['name']}! 😊 "
                if ctx.get('age'):
                    response += f"You're {ctx['age']} years old. "
                response += "Is there anything else you'd like to tell me about yourself, or shall we create a story?"
            else:
                response = "I don't think you've told me your name yet! What should I call you? 😊"
            
            return {
                'type': 'conversation',
                'response': response,
                'should_generate_story': False,
                'story_prompt': None
            }
        
        # Check if requesting a story
        if self.should_generate_story(message):
            # Use user's name in confirmation if available
            ctx = self._get_session(session_id)
            name_part = f"{ctx.get('name')}, " if ctx.get('name') else ""
            
            # Build context-aware story prompt from conversation history
            context_prompt = self._build_context_aware_prompt(message, conversation_history, session_id)
            
            return {
                'type': 'story_request',
                'response': f"Great idea, {name_part}let me create that story for you! ✨",
                'should_generate_story': True,
                'story_prompt': context_prompt  # Use context-aware prompt instead of raw message
            }
        
        # Regular conversation
        response = self.generate_conversational_response(message, conversation_history, session_id)
        
        return {
            'type': 'conversation',
            'response': response,
            'should_generate_story': False,
            'story_prompt': None
        }
