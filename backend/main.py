"""
Bedtime Story Time - FastAPI Backend
A Python backend for AI-powered children's storytelling using LangChain + Groq

This is the main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import conversation_router, stories_router, audio_router
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Bedtime Story API",
        description="AI-powered storytelling for children",
        version="2.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.CORS_ORIGINS,
        allow_credentials=settings.server.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.server.CORS_ALLOW_METHODS,
        allow_headers=settings.server.CORS_ALLOW_HEADERS,
    )
    
    app.include_router(conversation_router)
    app.include_router(stories_router)
    app.include_router(audio_router)
    
    return app


app = create_application()


@app.get("/")
async def root():
    """
    Health check endpoint - confirms the API is running.
    
    Returns:
        dict: API status information
    """
    return {
        "message": "Bedtime Story API is running!",
        "status": "healthy",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint.
    
    Returns:
        dict: Detailed health status
    """
    return {
        "status": "healthy",
        "api": "operational",
        "storage": "connected",
        "llm": "configured"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    logger.info("🌙 ===== Bedtime Story API Starting =====")
    logger.info(f"📡 Server: {settings.server.HOST}:{settings.server.PORT}")
    logger.info(f"🔧 Debug Mode: {settings.server.DEBUG}")
    logger.info(f"🎯 Max Iterations: {settings.story.MAX_ITERATIONS}")
    logger.info("✅ Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    logger.info("👋 Bedtime Story API shutting down...")
    logger.info("✅ Cleanup complete")


if __name__ == "__main__":
    import uvicorn
    
    host = settings.server.HOST
    port = settings.server.PORT
    debug = settings.server.DEBUG
    
    print(f"""
    🌙 ===== Bedtime Story API =====
    📡 Server: http://{host}:{port}
    📖 API Docs: http://{host}:{port}/docs
    🔍 Health: http://{host}:{port}/health
    🔧 Debug: {debug}
    🎯 Max Iterations: {settings.story.MAX_ITERATIONS}
    ================================
    """)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )
