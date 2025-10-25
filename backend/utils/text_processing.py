"""
Text Processing Utilities

Common text manipulation, extraction, and analysis functions.
"""

import re
from typing import Optional, List, Tuple
from config.constants import RegexPatterns, TextLimits


def extract_name_from_message(message: str) -> Optional[str]:
    """
    Extract user's name from a message using pattern matching.
    
    Args:
        message: User's message
        
    Returns:
        Extracted name (capitalized) or None
    """
    message_lower = message.lower()
    
    for pattern in RegexPatterns.NAME_PATTERNS:
        match = re.search(pattern, message_lower)
        if match:
            name = match.group(1).capitalize()
            # Basic validation
            if len(name) >= TextLimits.MIN_NAME_LENGTH and len(name) <= TextLimits.MAX_NAME_LENGTH:
                return name
    
    return None


def extract_age_from_message(message: str) -> Optional[int]:
    """
    Extract user's age from a message using pattern matching.
    
    Args:
        message: User's message
        
    Returns:
        Extracted age or None
    """
    message_lower = message.lower()
    
    match = re.search(RegexPatterns.AGE_PATTERN, message_lower)
    if match:
        try:
            age = int(match.group(1))
            # Basic range validation
            if 0 <= age <= 150:
                return age
        except ValueError:
            pass
    
    return None


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    if not text:
        return 0
    
    # Use regex to match word boundaries
    words = re.findall(RegexPatterns.WORD_COUNT_PATTERN, text)
    return len(words)


def count_paragraphs(text: str) -> int:
    """
    Count paragraphs in text.
    
    Args:
        text: Text to count paragraphs in
        
    Returns:
        Number of paragraphs
    """
    if not text:
        return 0
    
    # Split by blank lines
    paragraphs = re.split(RegexPatterns.PARAGRAPH_SPLIT, text.strip())
    # Filter out empty paragraphs
    return len([p for p in paragraphs if p.strip()])


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Strip leading/trailing whitespace
    return text.strip()


def extract_title_and_content(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract title and content from generated story text.
    
    Expects format like:
    Title: The Adventure Begins
    
    Story content here...
    
    Args:
        text: Generated story text
        
    Returns:
        Tuple of (title, content)
    """
    lines = text.strip().split('\n')
    
    title = None
    content_start_idx = 0
    
    # Look for "Title:" or "**Title:**" pattern in first few lines
    for i, line in enumerate(lines[:5]):
        # Remove markdown bold markers
        clean_line = line.replace('**', '').strip()
        
        if clean_line.lower().startswith('title:'):
            title = clean_line[6:].strip()
            content_start_idx = i + 1
            break
    
    # Get content (skip empty lines after title)
    content_lines = []
    for line in lines[content_start_idx:]:
        if line.strip() or content_lines:  # Start including once we hit non-empty
            content_lines.append(line)
    
    content = '\n'.join(content_lines).strip() if content_lines else None
    
    return title, content


def format_conversation_history(history: List[dict], max_entries: int = 10) -> str:
    """
    Format conversation history for display or context.
    
    Args:
        history: List of conversation messages
        max_entries: Maximum number of entries to include
        
    Returns:
        Formatted conversation string
    """
    if not history:
        return ""
    
    formatted = []
    for msg in history[-max_entries:]:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        # Truncate long messages
        if len(content) > 100:
            content = truncate_text(content, 100)
        
        role_label = "User" if role == 'user' else "Assistant"
        formatted.append(f"{role_label}: {content}")
    
    return '\n'.join(formatted)


def is_question(text: str) -> bool:
    """
    Determine if text is a question.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a question
    """
    if not text:
        return False
    
    text = text.strip()
    
    # Check for question mark
    if text.endswith('?'):
        return True
    
    # Check for question words at start
    question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does']
    first_word = text.split()[0].lower() if text.split() else ""
    
    return first_word in question_words


def remove_markdown(text: str) -> str:
    """
    Remove common markdown formatting from text.
    
    Args:
        text: Text with markdown
        
    Returns:
        Plain text
    """
    if not text:
        return ""
    
    # Remove bold
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove italic
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove links
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    return text


def capitalize_sentences(text: str) -> str:
    """
    Ensure sentences start with capital letters.
    
    Args:
        text: Text to capitalize
        
    Returns:
        Text with capitalized sentences
    """
    if not text:
        return ""
    
    # Split into sentences
    sentences = re.split(r'([.!?]\s+)', text)
    
    result = []
    for i, part in enumerate(sentences):
        if i % 2 == 0 and part:  # Sentence content (not delimiter)
            result.append(part[0].upper() + part[1:] if part else part)
        else:
            result.append(part)
    
    return ''.join(result)
