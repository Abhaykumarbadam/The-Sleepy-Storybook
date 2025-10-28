"""
Validation Utilities

Common validation functions for input data, parameters, and business logic.
"""

import re
from typing import Optional, Tuple
from config.constants import ValidationRules, TextLimits, RegexPatterns, StoryLength


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_prompt(prompt: str) -> Tuple[bool, Optional[str]]:
    """
    Validate story prompt input.
    
    Args:
        prompt: User's story prompt
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    if len(prompt) > TextLimits.MAX_PROMPT_LENGTH:
        return False, f"Prompt too long (max {TextLimits.MAX_PROMPT_LENGTH} characters)"
    
    word_count = len(prompt.split())
    if word_count < ValidationRules.MIN_PROMPT_WORDS:
        return False, f"Prompt too short (min {ValidationRules.MIN_PROMPT_WORDS} words)"
    
    if word_count > ValidationRules.MAX_PROMPT_WORDS:
        return False, f"Prompt too long (max {ValidationRules.MAX_PROMPT_WORDS} words)"
    
    return True, None


def compress_prompt_to_keywords(prompt: str, max_words: int = 12) -> str:
    """
    Compress a potentially long prompt into a short keyword-style phrase.

    Strategy: keep only the first N words after sanitization. This keeps intent
    while ensuring we stay under word limits and reduce token usage.

    Args:
        prompt: Original prompt text
        max_words: Maximum number of words to keep (default: 12)

    Returns:
        Compressed prompt string
    """
    if not prompt:
        return ""

    # Normalize spaces and split into words
    words = prompt.strip().split()
    if len(words) <= max_words:
        return " ".join(words)

    return " ".join(words[:max_words])


def validate_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate conversational message input.
    
    Args:
        message: User's message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message or not message.strip():
        return False, "Message cannot be empty"
    
    if len(message) > TextLimits.MAX_MESSAGE_LENGTH:
        return False, f"Message too long (max {TextLimits.MAX_MESSAGE_LENGTH} characters)"
    
    return True, None


def validate_story_length(length_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate story length type.
    
    Args:
        length_type: Story length ('short', 'medium', 'long')
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_lengths = [e.value for e in StoryLength]
    
    if length_type not in valid_lengths:
        return False, f"Invalid length type. Must be one of: {', '.join(valid_lengths)}"
    
    return True, None


def validate_age(age: int) -> Tuple[bool, Optional[str]]:
    """
    Validate user age.
    
    Args:
        age: User's age
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(age, int):
        return False, "Age must be a number"
    
    if age < ValidationRules.MIN_USER_AGE:
        return False, f"Age must be at least {ValidationRules.MIN_USER_AGE}"
    
    if age > ValidationRules.MAX_USER_AGE:
        return False, f"Age must be at most {ValidationRules.MAX_USER_AGE}"
    
    return True, None


def validate_quality_score(score: int) -> Tuple[bool, Optional[str]]:
    """
    Validate quality feedback score.
    
    Args:
        score: Quality score
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(score, int):
        return False, "Score must be an integer"
    
    if score < ValidationRules.MIN_FEEDBACK_SCORE:
        return False, f"Score must be at least {ValidationRules.MIN_FEEDBACK_SCORE}"
    
    if score > ValidationRules.MAX_FEEDBACK_SCORE:
        return False, f"Score must be at most {ValidationRules.MAX_FEEDBACK_SCORE}"
    
    return True, None


def validate_session_id(session_id: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate session ID format.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if session_id is None:
        return True, None  # Session ID is optional
    
    if not isinstance(session_id, str):
        return False, "Session ID must be a string"
    
    # Basic length check (UUID is 36 characters)
    if len(session_id) > 100:  # Allow some flexibility
        return False, "Session ID too long"
    
    return True, None


def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate extracted user name.
    
    Args:
        name: User's name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    if len(name) < TextLimits.MIN_NAME_LENGTH:
        return False, f"Name too short (min {TextLimits.MIN_NAME_LENGTH} characters)"
    
    if len(name) > TextLimits.MAX_NAME_LENGTH:
        return False, f"Name too long (max {TextLimits.MAX_NAME_LENGTH} characters)"
    
    # Check if name contains only letters (basic validation)
    if not name.isalpha():
        return False, "Name should contain only letters"
    
    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text


def validate_story_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate story content.
    
    Args:
        content: Story content
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Story content cannot be empty"
    
    if len(content) > TextLimits.MAX_STORY_CONTENT_LENGTH:
        return False, f"Story content too long (max {TextLimits.MAX_STORY_CONTENT_LENGTH} characters)"
    
    return True, None


def validate_title(title: str) -> Tuple[bool, Optional[str]]:
    """
    Validate story title.
    
    Args:
        title: Story title
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Title cannot be empty"
    
    if len(title) > TextLimits.MAX_TITLE_LENGTH:
        return False, f"Title too long (max {TextLimits.MAX_TITLE_LENGTH} characters)"
    
    return True, None
