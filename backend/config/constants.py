"""
Application Constants

Centralizes all hardcoded strings, magic numbers, and constant values
used throughout the application.
"""

from enum import Enum
from typing import Dict, List


# ============================================================================
# API CONSTANTS
# ============================================================================

class HTTPStatus:
    """HTTP status code constants."""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    TOO_MANY_REQUESTS = 429


class APIMessages:
    """Standard API response messages."""
    STORY_CREATED = "Story generated successfully"
    STORY_RETRIEVED = "Story retrieved successfully"
    STORY_NOT_FOUND = "Story not found"
    STORIES_RETRIEVED = "Stories retrieved successfully"
    CONVERSATION_SUCCESS = "Message processed successfully"
    AUDIO_GENERATED = "Audio generated successfully"
    
    # Error Messages
    ERROR_STORY_GENERATION = "Failed to generate story"
    ERROR_STORY_RETRIEVAL = "Failed to retrieve story"
    ERROR_DATABASE = "Database operation failed"
    ERROR_INVALID_INPUT = "Invalid input parameters"
    ERROR_API_KEY_MISSING = "API key configuration missing"
    INTERNAL_ERROR = "An internal server error occurred"
    RATE_LIMIT_ERROR = "Rate limit reached for the current Groq model(s). Please try again in a few minutes."


# ============================================================================
# STORY GENERATION CONSTANTS
# ============================================================================

class StoryLength(str, Enum):
    """Allowed story length types."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class QualityMetrics:
    """Story quality evaluation thresholds."""
    
    MIN_CLARITY_SCORE = 7
    MIN_MORAL_VALUE_SCORE = 7
    MIN_AGE_APPROPRIATENESS_SCORE = 7
    MIN_OVERALL_SCORE = 7
    
    MAX_SCORE = 10
    MIN_SCORE = 1


# ============================================================================
# PROMPT TEMPLATES PATH (for future extraction)
# ============================================================================

class PromptPaths:
    """Paths to prompt template files (future enhancement)."""
    
    STORYTELLER_SYSTEM = "prompts/storyteller_system.txt"
    STORYTELLER_USER = "prompts/storyteller_user.txt"
    JUDGE_SYSTEM = "prompts/judge_system.txt"
    REFINEMENT = "prompts/refinement.txt"
    CONVERSATION_SYSTEM = "prompts/conversation_system.txt"


# ============================================================================
# TEXT PROCESSING CONSTANTS
# ============================================================================

class TextLimits:
    """Text processing limits."""
    
    MAX_PROMPT_LENGTH = 500
    MAX_MESSAGE_LENGTH = 1000
    MAX_TITLE_LENGTH = 100
    MAX_STORY_CONTENT_LENGTH = 10000
    MAX_STORY_CONTENT = 10000  # Alias for compatibility
    
    # Name extraction
    MAX_NAME_LENGTH = 50
    MIN_NAME_LENGTH = 2


class RegexPatterns:
    """Common regex patterns."""
    
    # Name extraction patterns
    NAME_PATTERNS = [
        r"my name is (\w+)",
        r"i'm (\w+)",
        r"i am (\w+)",
        r"call me (\w+)",
        r"this is (\w+)"
    ]
    
    # Age extraction
    AGE_PATTERN = r"i(?:'m| am) (\d+) years? old"
    
    # Story validation
    PARAGRAPH_SPLIT = r'\n\s*\n'
    WORD_COUNT_PATTERN = r'\b\w+\b'


# ============================================================================
# STORAGE CONSTANTS
# ============================================================================

class StorageFiles:
    """JSON storage file names."""
    STORIES = "stories.json"
    CONVERSATIONS = "conversations.json"
    SESSIONS = "sessions.json"


class StorageKeys:
    """JSON storage object keys."""
    STORY_ID = "id"
    SESSION_ID = "session_id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# ============================================================================
# LOGGING CONSTANTS
# ============================================================================

class LogMessages:
    """Standard log messages."""
    
    # Initialization
    AGENT_INITIALIZED = "✅ {agent_type} Agent initialized with models: {models}"
    SERVER_STARTED = "🚀 Server started on {host}:{port}"
    STORAGE_CONNECTED = "📊 Connected to JSON Storage: {storage_dir}"
    
    # Operations
    STORY_GENERATION_START = "📖 Starting story generation: {prompt}"
    STORY_GENERATION_COMPLETE = "✅ Story generated in {iterations} iterations"
    STORY_REFINEMENT = "🔄 Refining story (iteration {current}/{max})"
    CONTENT_FILTERED = "⚠️ Content filter: Message flagged as inappropriate"
    
    # Errors
    MODEL_FAILED = "⚠️ {agent_type} model '{model}' failed: {error}"
    MODEL_RETRY = "↪️ Trying next model..."
    ALL_MODELS_FAILED = "❌ All models failed for {agent_type}"
    DATABASE_ERROR = "❌ Database error: {error}"
    
    # User Info
    NAME_LEARNED = "📝 Learned user's name: {name}"
    AGE_LEARNED = "📝 Learned user's age: {age}"
    CONTEXT_GENERATED = "💡 Context-aware prompt generated: {prompt}"


# ============================================================================
# UI/UX CONSTANTS (for frontend reference)
# ============================================================================

class UIMessages:
    """User-facing messages."""
    
    # Success Messages
    STORY_READY = "Your story is ready!"
    GENERATING_STORY = "Creating your magical story..."
    
    # Error Messages  
    GENERATION_FAILED = "Oops! We couldn't create your story. Please try again."
    NO_CONNECTION = "Can't connect to the story server. Please check your connection."
    INAPPROPRIATE_CONTENT = "That story idea isn't quite right for bedtime. Let's try something else!"
    
    # Prompts
    ENTER_STORY_IDEA = "What kind of story would you like?"
    STORY_LENGTH_PROMPT = "How long should your story be?"


# ============================================================================
# FEATURE FLAGS (for gradual rollout)
# ============================================================================

class FeatureFlags:
    """Feature toggle flags."""
    
    ENABLE_LANGSMITH_TRACING = True
    ENABLE_STORY_CACHING = False
    ENABLE_RATE_LIMITING = False
    ENABLE_AUDIO_GENERATION = True
    ENABLE_IMAGE_GENERATION = False  # Future feature


# ============================================================================
# RETRY AND TIMEOUT SETTINGS
# ============================================================================

class RetryConfig:
    """Retry configuration for various operations."""
    
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1
    EXPONENTIAL_BACKOFF_MULTIPLIER = 2
    
    # Database
    DB_MAX_RETRIES = 3
    DB_RETRY_DELAY_MS = 100
    
    # API Calls
    API_MAX_RETRIES = 3
    API_TIMEOUT_SECONDS = 30


# ============================================================================
# VALIDATION RULES
# ============================================================================

class ValidationRules:
    """Input validation rules."""
    
    # Story prompt
    MIN_PROMPT_WORDS = 2
    MAX_PROMPT_WORDS = 100
    
    # Age validation
    MIN_USER_AGE = 3
    MAX_USER_AGE = 18
    
    # Session
    SESSION_ID_LENGTH = 36  # UUID length
    
    # Feedback scores
    MIN_FEEDBACK_SCORE = 1
    MAX_FEEDBACK_SCORE = 10


# ============================================================================
# EXPORT ALL CONSTANTS
# ============================================================================

__all__ = [
    'HTTPStatus',
    'APIMessages',
    'StoryLength',
    'QualityMetrics',
    'PromptPaths',
    'TextLimits',
    'RegexPatterns',
    'CollectionNames',
    'IndexNames',
    'LogMessages',
    'UIMessages',
    'FeatureFlags',
    'RetryConfig',
    'ValidationRules',
]
