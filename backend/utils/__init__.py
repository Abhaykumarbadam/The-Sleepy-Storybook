"""
Utilities Package

Common utility functions for validation, text processing, and logging.
"""

from .validation import (
    ValidationError,
    validate_prompt,
    validate_message,
    validate_story_length,
    validate_age,
    validate_quality_score,
    validate_session_id,
    validate_name,
    sanitize_input,
    compress_prompt_to_keywords,
    validate_story_content,
    validate_title
)

from .text_processing import (
    extract_name_from_message,
    extract_age_from_message,
    count_words,
    count_paragraphs,
    truncate_text,
    clean_whitespace,
    extract_title_and_content,
    format_conversation_history,
    is_question,
    remove_markdown,
    capitalize_sentences
)

from .logging_utils import (
    setup_logger,
    log_agent_init,
    log_story_generation_start,
    log_story_generation_complete,
    log_story_refinement,
    log_model_failure,
    log_database_error,
    log_user_info_learned,
    log_content_filtered,
    log_context_generated
)

__all__ = [
    # Validation
    'ValidationError',
    'validate_prompt',
    'validate_message',
    'validate_story_length',
    'validate_age',
    'validate_quality_score',
    'validate_session_id',
    'validate_name',
    'sanitize_input',
    'compress_prompt_to_keywords',
    'validate_story_content',
    'validate_title',
    
    # Text Processing
    'extract_name_from_message',
    'extract_age_from_message',
    'count_words',
    'count_paragraphs',
    'truncate_text',
    'clean_whitespace',
    'extract_title_and_content',
    'format_conversation_history',
    'is_question',
    'remove_markdown',
    'capitalize_sentences',
    
    # Logging
    'setup_logger',
    'log_agent_init',
    'log_story_generation_start',
    'log_story_generation_complete',
    'log_story_refinement',
    'log_model_failure',
    'log_database_error',
    'log_user_info_learned',
    'log_content_filtered',
    'log_context_generated',
]
