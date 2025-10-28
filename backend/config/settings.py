"""
Configuration Settings Module

Centralizes all application configuration including environment variables,
API settings, and application constants.
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class APIConfig:
    """API and service configuration."""
    
    # API Keys
    GROQ_API_KEY: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    LANGSMITH_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("LANGSMITH_API_KEY"))
    
    # LangSmith Configuration
    LANGSMITH_PROJECT: str = field(default_factory=lambda: os.getenv("LANGSMITH_PROJECT", "bedtime-stories"))
    LANGCHAIN_TRACING_V2: str = "true"
    
    def __post_init__(self):
        """Validate required configuration."""
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")


@dataclass
class LLMConfig:
    """LLM model configuration."""
    
    # Model Selection
    DEFAULT_MODELS: List[str] = field(default_factory=lambda: [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ])
    
    # Storyteller Configuration
    STORYTELLER_TEMPERATURE: float = 0.8
    STORYTELLER_MAX_TOKENS: int = 700
    STORYTELLER_MODELS: Optional[List[str]] = field(default_factory=lambda: (
        [m.strip() for m in os.getenv("GROQ_MODEL_STORYTELLER", "").split(",") if m.strip()]
        or None
    ))
    
    # Judge Configuration  
    JUDGE_TEMPERATURE: float = 0.3
    JUDGE_MAX_TOKENS: int = 300
    JUDGE_MODELS: Optional[List[str]] = field(default_factory=lambda: (
        [m.strip() for m in os.getenv("GROQ_MODEL_JUDGE", "").split(",") if m.strip()]
        or None
    ))
    
    # Conversational Agent Configuration
    CONVERSATION_TEMPERATURE: float = 0.7
    CONVERSATION_MAX_TOKENS: int = 300
    CONVERSATION_MODELS: Optional[List[str]] = field(default_factory=lambda: (
        [m.strip() for m in os.getenv("GROQ_MODEL_CONVERSATION", "").split(",") if m.strip()]
        or None
    ))
    
    def get_models(self, agent_type: str) -> List[str]:
        """
        Get model list for specific agent type with fallback to defaults.
        
        Args:
            agent_type: 'storyteller', 'judge', or 'conversation'
            
        Returns:
            List of model names to try
        """
        if agent_type == "storyteller":
            return self.STORYTELLER_MODELS or self.DEFAULT_MODELS
        elif agent_type == "judge":
            return self.JUDGE_MODELS or self.DEFAULT_MODELS
        elif agent_type == "conversation":
            return self.CONVERSATION_MODELS or self.DEFAULT_MODELS
        return self.DEFAULT_MODELS


@dataclass
class ServerConfig:
    """Server and CORS configuration."""
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://localhost:3000"
    ])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class StorageConfig:
    """JSON storage configuration."""
    
    STORAGE_DIR: str = "backend/data"
    STORIES_FILE: str = "stories.json"
    CONVERSATIONS_FILE: str = "conversations.json"


@dataclass
class StoryConfig:
    """Story generation configuration."""
    
    # Age Range
    MIN_AGE: int = 5
    MAX_AGE: int = 10
    
    # Word Count Targets
    WORD_COUNTS: dict = field(default_factory=lambda: {
        "short": {"min": 150, "max": 220, "target": "180"},
        "medium": {"min": 250, "max": 320, "target": "300"},
        "long": {"min": 350, "max": 420, "target": "400"}
    })
    
    # Story Generation
    MAX_ITERATIONS: int = 3
    MIN_QUALITY_SCORE: int = 7
    
    # Paragraph Structure
    PARAGRAPH_STRUCTURE: dict = field(default_factory=lambda: {
        "short": 2,
        "medium": 3,
        "long": 3
    })


class Settings:
    """
    Application settings container.
    
    Provides centralized access to all configuration settings.
    """
    
    def __init__(self):
        self.api = APIConfig()
        self.llm = LLMConfig()
        self.server = ServerConfig()
        self.storage = StorageConfig()
        self.story = StoryConfig()
    
    def validate(self) -> bool:
        """
        Validate all configuration settings.
        
        Returns:
            True if all settings are valid
            
        Raises:
            ValueError: If any required settings are missing or invalid
        """
        # APIConfig validation happens in __post_init__
        return True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings instance with all configuration
    """
    return settings
