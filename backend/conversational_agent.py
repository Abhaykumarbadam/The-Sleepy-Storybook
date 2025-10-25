"""
Conversational Agent for Bedtime Story Time

This module provides an intelligent conversational agent that:
- Maintains session-based context (user name, preferences)
- Filters inappropriate content using LLM-based analysis
- Responds naturally to user queries
- Detects story requests and builds context-aware prompts

Author: Refactored for production use
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import os
import re
import uuid

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import ConversationalPrompts


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AgentConfig:
    """Configuration constants for the conversational agent."""
    
    # Model Configuration
    DEFAULT_MODELS: List[str] = field(default_factory=lambda: [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ])
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 500
    
    # Age Range
    MIN_AGE: int = 5
    MAX_AGE: int = 14
    
    # Context History
    MAX_CONVERSATION_HISTORY: int = 4
    MAX_CONTEXT_ANALYSIS_HISTORY: int = 8
    
    # Session Configuration
    DEFAULT_SESSION_ID: str = "default"
    
    # LangSmith Configuration
    LANGSMITH_PROJECT_DEFAULT: str = "bedtime-stories"


# ============================================================================
# MAIN AGENT CLASS
# ============================================================================

class ConversationalAgent:
    """
    Intelligent conversational agent for children's storytelling application.
    
    This agent handles natural conversations with children, filters inappropriate
    content, remembers context across a session, and generates context-aware
    story prompts when requested.
    
    Features:
        - Session-based context memory (names, preferences, age)
        - LLM-powered content safety filtering
        - Natural conversation without always generating stories
        - Context-aware story prompt generation
        - LangSmith tracing support for debugging and monitoring
        - Automatic model fallback on failures
    
    Example:
        ```python
        agent = ConversationalAgent(
            groq_api_key="your-api-key",
            langsmith_api_key="optional-langsmith-key"
        )
        
        result = agent.process_message(
            "Tell me a story about dragons",
            conversation_history=[],
            session_id="user123"
        )
        ```
    """
    
    def __init__(
        self, 
        groq_api_key: str, 
        langsmith_api_key: Optional[str] = None,
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize the conversational agent.
        
        Args:
            groq_api_key: API key for Groq LLM service (required)
            langsmith_api_key: Optional API key for LangSmith tracing
            config: Optional configuration object (uses defaults if not provided)
        """
        self.config = config or AgentConfig()
        self.groq_api_key = groq_api_key
        
        # Initialize LangSmith tracing if API key provided
        self._setup_langsmith_tracing(langsmith_api_key)
        
        # Configure LLM models
        self.model_candidates = self._load_model_candidates()
        self.llm = None
        
        # Session management: stores context per session
        self.sessions: Dict[str, Dict[str, any]] = {}
        
        self._log_initialization()
    
    # ------------------------------------------------------------------------
    # INITIALIZATION HELPERS
    # ------------------------------------------------------------------------
    
    def _setup_langsmith_tracing(self, api_key: Optional[str]) -> None:
        """
        Configure LangSmith tracing for observability.
        
        Args:
            api_key: LangSmith API key (None to disable tracing)
        """
        self.langsmith_enabled = False
        
        if api_key:
            os.environ["LANGSMITH_API_KEY"] = api_key
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = os.getenv(
                "LANGSMITH_PROJECT", 
                self.config.LANGSMITH_PROJECT_DEFAULT
            )
            self.langsmith_enabled = True
    
    def _load_model_candidates(self) -> List[str]:
        """
        Load model candidates from environment or use defaults.
        
        Checks GROQ_MODEL_CONVERSATION and GROQ_MODEL environment variables
        before falling back to default models.
        
        Returns:
            List of model names to try in fallback order
        """
        env_models = (
            os.getenv("GROQ_MODEL_CONVERSATION") or 
            os.getenv("GROQ_MODEL") or 
            ""
        )
        models = [m.strip() for m in env_models.split(",") if m.strip()]
        
        return models if models else self.config.DEFAULT_MODELS
    
    def _log_initialization(self) -> None:
        """Log successful initialization with configuration details."""
        print(
            f"✅ Conversational Agent initialized (Groq) with model fallback: "
            f"{', '.join(self.model_candidates)}"
        )
    
    # ------------------------------------------------------------------------
    # SESSION MANAGEMENT
    # ------------------------------------------------------------------------
    
    def _get_session(self, session_id: Optional[str] = None) -> Dict[str, any]:
        """
        Retrieve or create a session context.
        
        Each session maintains user information (name, age) and a unique
        trace ID for LangSmith tracking.
        
        Args:
            session_id: Optional session identifier (uses default if None)
            
        Returns:
            Session context dictionary with user data and trace_id
        """
        sid = session_id or self.config.DEFAULT_SESSION_ID
        
        if sid not in self.sessions:
            self.sessions[sid] = {
                'trace_id': str(uuid.uuid4()),
                'name': None,
                'age': None
            }
        
        return self.sessions[sid]
    
    # ------------------------------------------------------------------------
    # LLM INVOCATION
    # ------------------------------------------------------------------------
    
    def _invoke_with_fallback(
        self, 
        messages: List, 
        session_id: Optional[str] = None
    ):
        """
        Invoke LLM with automatic model fallback on failure.
        
        Tries each model in the candidate list until one succeeds or all fail.
        Note: Tracing should be handled at the request/session level, not here.
        
        Args:
            messages: List of chat messages (SystemMessage, HumanMessage)
            session_id: Optional session ID for context (not used for tracing)
            
        Returns:
            LLM response object
            
        Raises:
            RuntimeError: If all model candidates fail
        """
        last_error = None
        
        # Try each model in sequence
        for attempt, model_name in enumerate(self.model_candidates, 1):
            try:
                # Initialize model
                self.llm = ChatGroq(
                    model=model_name,
                    api_key=self.groq_api_key,
                    temperature=self.config.TEMPERATURE,
                    max_tokens=self.config.MAX_TOKENS
                )
                
                # Simple invoke without per-call tracing
                # Tracing is handled at the session level by the route
                return self.llm.invoke(messages)
                    
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                print(f"⚠️ Model '{model_name}' failed (attempt {attempt}/{len(self.model_candidates)}): {e}")
                
                # Determine if we should retry with next model
                is_retryable = any(
                    keyword in error_msg 
                    for keyword in ["rate limit", "429", "decommission", "invalid", "token"]
                )
                
                if is_retryable and attempt < len(self.model_candidates):
                    print("↪️ Trying next Groq model...")
                    continue
                else:
                    break
        
        # All models failed
        raise last_error or RuntimeError("All Groq models failed for conversation")
    
    # ------------------------------------------------------------------------
    # USER INFORMATION EXTRACTION
    # ------------------------------------------------------------------------
    
    def extract_user_info(self, message: str, session_id: Optional[str] = None) -> None:
        """
        Extract and store user information (name, age) from message.
        
        Uses regex patterns to detect when users introduce themselves or
        mention their age. Updates the session context accordingly.
        
        Args:
            message: User's message text
            session_id: Session ID to update
        """
        ctx = self._get_session(session_id)
        
        # Use LLM to extract user information intelligently
        extraction_prompt = ConversationalPrompts.get_user_info_extraction_prompt(message)
        
        try:
            messages = [
                SystemMessage(content=extraction_prompt),
                HumanMessage(content="Extract the information")
            ]
            
            response = self._invoke_with_fallback(messages, session_id=session_id)
            
            # Parse JSON response
            import json
            info = json.loads(response.content.strip())
            
            if info.get('name'):
                ctx['name'] = info['name'].capitalize()
                print(f"📝 Learned user's name: {ctx['name']}")
            
            if info.get('age'):
                ctx['age'] = int(info['age'])
                print(f"📝 Learned user's age: {ctx['age']}")
                
        except Exception as e:
            # Silently fail if extraction doesn't work
            pass
    
    # ------------------------------------------------------------------------
    # CONTENT SAFETY
    # ------------------------------------------------------------------------
    
    def is_inappropriate_content(
        self, 
        message: str, 
        session_id: Optional[str] = None
    ) -> bool:
        """
        Check if message contains inappropriate content using LLM analysis.
        
        This is more sophisticated than keyword matching as it understands
        context and nuance (e.g., "friendly dragon" vs "scary dragon").
        
        Args:
            message: User's message to check
            session_id: Optional session ID for tracing
            
        Returns:
            True if content is inappropriate for children, False otherwise
        """
        prompt = ConversationalPrompts.get_content_safety_prompt(message)
        
        try:
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="Check if appropriate:")
            ]
            
            response = self._invoke_with_fallback(messages, session_id=session_id)
            result = response.content.strip().upper()
            
            is_inappropriate = "INAPPROPRIATE" in result
            
            if is_inappropriate:
                print(f"⚠️ Content filter: Message flagged as inappropriate")
            
            return is_inappropriate
            
        except Exception as e:
            print(f"⚠️ Error in content filtering: {e}")
            # Conservative: allow message if filtering fails
            # Main system prompt will still provide safety guidance
            return False
    
    # ------------------------------------------------------------------------
    # MESSAGE CLASSIFICATION
    # ------------------------------------------------------------------------
    
    def should_generate_story(self, message: str) -> bool:
        """
        Determine if the message is requesting a story using LLM intelligence.
        
        Args:
            message: User's message text
            
        Returns:
            True if message contains story request
        """
        detection_prompt = ConversationalPrompts.get_story_request_detection_prompt(message)
        
        try:
            messages = [
                SystemMessage(content=detection_prompt),
                HumanMessage(content="Is this a story request?")
            ]
            
            response = self._invoke_with_fallback(messages)
            answer = response.content.strip().lower()
            
            return 'yes' in answer
        except:
            # Fallback: simple keyword check if LLM fails
            message_lower = message.lower()
            return 'story' in message_lower or 'tale' in message_lower
    
    def is_question_about_self(self, message: str) -> bool:
        """
        Check if user is asking about themselves using LLM intelligence.
        
        Args:
            message: User's message text
            
        Returns:
            True if message is a self-inquiry
        """
        detection_prompt = ConversationalPrompts.get_self_inquiry_detection_prompt(message)
        
        try:
            messages = [
                SystemMessage(content=detection_prompt),
                HumanMessage(content="Is this asking about self?")
            ]
            
            response = self._invoke_with_fallback(messages)
            answer = response.content.strip().lower()
            
            return 'yes' in answer
        except:
            # Fallback
            message_lower = message.lower()
            return 'my name' in message_lower or 'who am i' in message_lower
    
    # ------------------------------------------------------------------------
    # CONVERSATION GENERATION
    # ------------------------------------------------------------------------
    
    def generate_conversational_response(
        self, 
        message: str, 
        conversation_history: List[dict], 
        session_id: Optional[str] = None
    ) -> str:
        """
        Generate a natural conversational response (not a story).
        
        Args:
            message: User's message
            conversation_history: List of previous messages
            session_id: Session identifier
            
        Returns:
            Agent's conversational response text
        """
        ctx = self._get_session(session_id)
        
        # Build user context string
        context = ""
        if ctx.get('name'):
            context += f"User's name: {ctx['name']}\n"
        if ctx.get('age'):
            context += f"User's age: {ctx['age']}\n"
        
        # Format recent conversation history
        recent_history = conversation_history[-self.config.MAX_CONVERSATION_HISTORY:]
        history_text = self._format_conversation_history(recent_history)
        
        # Get conversational prompt
        age_range = (self.config.MIN_AGE, self.config.MAX_AGE)
        system_prompt = ConversationalPrompts.get_conversational_prompt(
            context=context,
            history=history_text,
            age_range=age_range
        )
        
        # Generate response
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        response = self._invoke_with_fallback(messages, session_id=session_id)
        return response.content
    
    def _format_conversation_history(self, history: List[dict]) -> str:
        """
        Format conversation history for prompt context.
        
        Args:
            history: List of conversation messages
            
        Returns:
            Formatted string representation of conversation
        """
        formatted = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "You"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    # ------------------------------------------------------------------------
    # CONTEXT-AWARE STORY PROMPTS
    # ------------------------------------------------------------------------
    
    def _build_context_aware_prompt(
        self, 
        message: str, 
        conversation_history: List[dict], 
        session_id: Optional[str] = None
    ) -> str:
        """
        Build a context-aware story prompt from conversation history.
        
        Uses LLM to analyze recent conversation and extract themes, interests,
        or topics that can enhance the story prompt.
        
        Args:
            message: User's current message
            conversation_history: Previous conversation messages
            session_id: Session identifier
            
        Returns:
            Enhanced story prompt incorporating conversation context
        """
        # Let the LLM determine if the message already has enough context
        # No hardcoded keyword checking
        
        # Get recent conversation for context analysis
        recent_history = conversation_history[-self.config.MAX_CONTEXT_ANALYSIS_HISTORY:]
        
        if not recent_history:
            return message
        
        # Analyze conversation context
        conversation_text = self._format_conversation_history(recent_history)
        prompt = ConversationalPrompts.get_context_analyzer_prompt(
            conversation=conversation_text,
            request=message
        )
        
        try:
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="What story prompt should I use based on this conversation?")
            ]
            
            response = self._invoke_with_fallback(messages, session_id=session_id)
            context_aware_prompt = response.content.strip()
            
            print(f"💡 Context-aware prompt generated: '{context_aware_prompt}'")
            return context_aware_prompt
            
        except Exception as e:
            print(f"⚠️ Error building context-aware prompt: {e}")
            return message
    
    # ------------------------------------------------------------------------
    # MAIN PROCESSING
    # ------------------------------------------------------------------------
    
    def process_message(
        self, 
        message: str, 
        conversation_history: Optional[List[dict]] = None, 
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Process user message and determine appropriate response.
        
        This is the main entry point for message processing. It:
        1. Extracts user information (name, age)
        2. Checks content safety
        3. Classifies message type (conversation, story request, self-inquiry)
        4. Generates appropriate response
        
        Args:
            message: User's message text
            conversation_history: List of previous messages (optional)
            session_id: Session identifier (optional)
            
        Returns:
            Dictionary containing:
                - type: 'conversation' | 'story_request' | 'inappropriate'
                - response: Agent's response text
                - should_generate_story: Boolean indicating if story should be generated
                - story_prompt: Enhanced prompt for story generation (if applicable)
        """
        if conversation_history is None:
            conversation_history = []
        
        # Extract user information from message
        self.extract_user_info(message, session_id)
        
        # Content safety check
        if self.is_inappropriate_content(message, session_id):
            return self._handle_inappropriate_content(session_id)
        
        # Handle self-inquiry questions
        if self.is_question_about_self(message):
            return self._handle_self_inquiry(session_id)
        
        # Handle story requests
        if self.should_generate_story(message):
            return self._handle_story_request(message, conversation_history, session_id)
        
        # Regular conversation
        return self._handle_conversation(message, conversation_history, session_id)
    
    def _handle_inappropriate_content(self, session_id: Optional[str]) -> Dict:
        """Generate response for inappropriate content requests."""
        ctx = self._get_session(session_id)
        name_part = f"{ctx.get('name', 'friend')}, " if ctx.get('name') else ""
        
        return {
            'type': 'inappropriate',
            'response': (
                f"Oh {name_part}I'm sorry, but I can only create stories that are fun and safe for children. "
                "How about we try a different adventure? Maybe something with friendly animals, magic, "
                "or exploring new places? 🌟"
            ),
            'should_generate_story': False,
            'story_prompt': None
        }
    
    def _handle_self_inquiry(self, session_id: Optional[str]) -> Dict:
        """Generate response for self-inquiry questions."""
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
    
    def _handle_story_request(
        self, 
        message: str, 
        conversation_history: List[dict], 
        session_id: Optional[str]
    ) -> Dict:
        """Generate response for story requests."""
        ctx = self._get_session(session_id)
        name_part = f"{ctx.get('name')}, " if ctx.get('name') else ""
        
        # Build context-aware story prompt
        context_prompt = self._build_context_aware_prompt(
            message, 
            conversation_history, 
            session_id
        )
        
        return {
            'type': 'story_request',
            'response': f"Great idea, {name_part}let me create that story for you! ✨",
            'should_generate_story': True,
            'story_prompt': context_prompt
        }
    
    def _handle_conversation(
        self, 
        message: str, 
        conversation_history: List[dict], 
        session_id: Optional[str]
    ) -> Dict:
        """Generate response for regular conversation."""
        response = self.generate_conversational_response(
            message, 
            conversation_history, 
            session_id
        )
        
        return {
            'type': 'conversation',
            'response': response,
            'should_generate_story': False,
            'story_prompt': None
        }
