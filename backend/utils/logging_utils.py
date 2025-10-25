"""
Logging Utilities

Centralized logging configuration and helper functions.
"""

import logging
import sys
from typing import Optional
from datetime import datetime
from config.constants import LogMessages


# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_file: Optional file path for file logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_agent_init(logger: logging.Logger, agent_type: str, models: list):
    """
    Log agent initialization.
    
    Args:
        logger: Logger instance
        agent_type: Type of agent (storyteller, judge, conversation)
        models: List of model names
    """
    message = LogMessages.AGENT_INITIALIZED.format(
        agent_type=agent_type.capitalize(),
        models=", ".join(models)
    )
    logger.info(message)


def log_story_generation_start(logger: logging.Logger, prompt: str):
    """
    Log start of story generation.
    
    Args:
        logger: Logger instance
        prompt: Story prompt
    """
    message = LogMessages.STORY_GENERATION_START.format(
        prompt=prompt[:100] + "..." if len(prompt) > 100 else prompt
    )
    logger.info(message)


def log_story_generation_complete(logger: logging.Logger, iterations: int):
    """
    Log completion of story generation.
    
    Args:
        logger: Logger instance
        iterations: Number of iterations taken
    """
    message = LogMessages.STORY_GENERATION_COMPLETE.format(
        iterations=iterations
    )
    logger.info(message)


def log_story_refinement(logger: logging.Logger, current: int, max_iter: int):
    """
    Log story refinement iteration.
    
    Args:
        logger: Logger instance
        current: Current iteration number
        max_iter: Maximum iterations
    """
    message = LogMessages.STORY_REFINEMENT.format(
        current=current,
        max=max_iter
    )
    logger.info(message)


def log_model_failure(logger: logging.Logger, agent_type: str, model: str, error: str):
    """
    Log model failure with error.
    
    Args:
        logger: Logger instance
        agent_type: Type of agent
        model: Model name that failed
        error: Error message
    """
    message = LogMessages.MODEL_FAILED.format(
        agent_type=agent_type,
        model=model,
        error=str(error)
    )
    logger.warning(message)


def log_database_error(logger: logging.Logger, error: str):
    """
    Log database error.
    
    Args:
        logger: Logger instance
        error: Error message
    """
    message = LogMessages.DATABASE_ERROR.format(error=str(error))
    logger.error(message)


def log_user_info_learned(logger: logging.Logger, info_type: str, value: str):
    """
    Log user information learned.
    
    Args:
        logger: Logger instance
        info_type: Type of info (name, age)
        value: The learned value
    """
    if info_type == "name":
        message = LogMessages.NAME_LEARNED.format(name=value)
    elif info_type == "age":
        message = LogMessages.AGE_LEARNED.format(age=value)
    else:
        message = f"📝 Learned user's {info_type}: {value}"
    
    logger.info(message)


def log_content_filtered(logger: logging.Logger):
    """
    Log content filter activation.
    
    Args:
        logger: Logger instance
    """
    logger.warning(LogMessages.CONTENT_FILTERED)


def log_context_generated(logger: logging.Logger, prompt: str):
    """
    Log context-aware prompt generation.
    
    Args:
        logger: Logger instance
        prompt: Generated prompt
    """
    message = LogMessages.CONTEXT_GENERATED.format(
        prompt=prompt[:100] + "..." if len(prompt) > 100 else prompt
    )
    logger.info(message)
