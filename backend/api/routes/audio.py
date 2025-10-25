"""
Audio Routes Module

Handles text-to-speech audio generation.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from io import BytesIO
import re

from gtts import gTTS
from utils import setup_logger
from config import HTTPStatus, APIMessages, TextLimits

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["audio"])


# ===== Request/Response Models =====

class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str
    lang: str = "en"
    slow: bool = False


# ===== Helper Functions =====

def normalize_text_for_speech(text: str) -> str:
    """
    Normalize text for better speech synthesis.
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text suitable for TTS
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    # Add space after punctuation if missing
    text = re.sub(r"([\.!?])([^ \n])", r"\1 \2", text)
    
    # Replace paragraph breaks with pauses
    text = re.sub(r"\n\s*\n", ". . . ", text)
    
    return text


# ===== Routes =====

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate natural-sounding speech audio (MP3) for provided text using gTTS.
    
    Args:
        request: TTSRequest with text, language, and speed settings
        
    Returns:
        StreamingResponse with MP3 audio data
    """
    try:
        # Validate input
        if not request.text or not isinstance(request.text, str):
            logger.warning("❌ TTS request missing text")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Text is required"
            )
        
        if len(request.text) > TextLimits.MAX_STORY_CONTENT:
            logger.warning(f"❌ TTS text too long: {len(request.text)} chars")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Text too long (max {TextLimits.MAX_STORY_CONTENT} characters)"
            )
        
        # Normalize text for better speech
        normalized_text = normalize_text_for_speech(request.text)
        logger.info(f"🔊 Generating TTS audio ({len(normalized_text)} chars, lang={request.lang})")
        
        # Generate audio
        mp3_buffer = BytesIO()
        tts = gTTS(text=normalized_text, lang=request.lang, slow=request.slow)
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        
        logger.info("✅ TTS audio generated successfully")
        
        return StreamingResponse(mp3_buffer, media_type="audio/mpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating TTS audio: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=APIMessages.INTERNAL_ERROR
        )
