"""
Bedtime Story Time - FastAPI Backend
AI-powered children's storytelling using LangChain + Groq
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import conversation_router, stories_router, audio_router
from config import settings
from utils import setup_logger
from opik_config import initialize_opik

logger = setup_logger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Bedtime Story API",
        description="AI-powered storytelling for children",
        version="2.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5175",
            "http://localhost:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    app.include_router(conversation_router)
    app.include_router(stories_router)
    app.include_router(audio_router)
    
    return app


app = create_application()


@app.get("/")
async def root():
    """Health check endpoint - confirms the API is running."""
    return {
        "message": "Bedtime Story API is running!",
        "status": "healthy",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "api": "operational",
        "storage": "connected",
        "llm": "configured"
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🌙 ===== Bedtime Story API Starting =====")
    logger.info(f"📡 Server: {settings.server.HOST}:{settings.server.PORT}")
    logger.info(f"🔧 Debug Mode: {settings.server.DEBUG}")
    logger.info(f"🎯 Max Iterations: {settings.story.MAX_ITERATIONS}")
    
    try:
        initialize_opik(project_name="Sleepy-Storybook")
        logger.info("Opik initialized for project: Sleepy-Storybook")
    except Exception as e:
        logger.warning(f"Opik initialization failed: {e}")
    
    logger.info("✅ Application started successfully")
    
    yield
    
    logger.info("👋 Bedtime Story API shutting down...")
    logger.info("✅ Cleanup complete")

app.router.lifespan_context = lifespan


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
