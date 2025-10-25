"""
API Package

Provides routers, dependencies, and middleware for the FastAPI application.
"""

from api.routes import conversation_router, stories_router, audio_router
from api.dependencies import (
    get_conversational_agent,
    get_storyteller_agent,
    get_judge_agent,
    get_database,
    get_settings,
)

__all__ = [
    # Routers
    "conversation_router",
    "stories_router",
    "audio_router",
    # Dependencies
    "get_conversational_agent",
    "get_storyteller_agent",
    "get_judge_agent",
    "get_database",
    "get_settings",
]
