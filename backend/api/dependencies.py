"""
API Dependencies Module

Provides dependency injection for agents and services.
This centralizes agent initialization and makes testing easier.
"""

from functools import lru_cache
from agents import StorytellerAgent, JudgeAgent
from conversational_agent import ConversationalAgent
from storage import storage
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)


# ===== Agent Singletons =====

_conversational_agent = None
_storyteller_agent = None
_judge_agent = None


def get_conversational_agent() -> ConversationalAgent:
    """
    Get or create ConversationalAgent singleton.
    
    Returns:
        ConversationalAgent instance
    """
    global _conversational_agent
    if _conversational_agent is None:
        logger.info("🤖 Initializing ConversationalAgent...")
        _conversational_agent = ConversationalAgent(
            groq_api_key=settings.api.GROQ_API_KEY,
            langsmith_api_key=settings.api.LANGSMITH_API_KEY
        )
    return _conversational_agent


def get_storyteller_agent() -> StorytellerAgent:
    """
    Get or create StorytellerAgent singleton.
    
    Returns:
        StorytellerAgent instance
    """
    global _storyteller_agent
    if _storyteller_agent is None:
        logger.info("📖 Initializing StorytellerAgent...")
        _storyteller_agent = StorytellerAgent(
            groq_api_key=settings.api.GROQ_API_KEY,
            langsmith_api_key=settings.api.LANGSMITH_API_KEY
        )
    return _storyteller_agent


def get_judge_agent() -> JudgeAgent:
    """
    Get or create JudgeAgent singleton.
    
    Returns:
        JudgeAgent instance
    """
    global _judge_agent
    if _judge_agent is None:
        logger.info("⚖️ Initializing JudgeAgent...")
        _judge_agent = JudgeAgent(
            groq_api_key=settings.api.GROQ_API_KEY,
            langsmith_api_key=settings.api.LANGSMITH_API_KEY
        )
    return _judge_agent


@lru_cache()
def get_database():
    """
    Get JSON storage instance.
    
    Returns:
        JSONStorage instance
    """
    return storage


def get_settings():
    """
    Get application settings.
    
    Returns:
        Settings instance
    """
    return settings
