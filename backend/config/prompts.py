"""
System Prompts for AI Agents

This module centralizes all system prompts used by the storytelling agents.
All prompts are managed here to ensure consistency and ease of modification.
"""

from typing import Tuple


# ============================================================================
# CONVERSATIONAL AGENT PROMPTS
# ============================================================================

class ConversationalPrompts:
    """Prompts for the conversational agent (Storybuddy)."""
    
    @staticmethod
    def get_content_safety_prompt(message: str) -> str:
        """
        Prompt for checking if content is appropriate for children.
        
        Args:
            message: The user's message to check
            
        Returns:
            Formatted content safety prompt
        """
        return f"""Is this story request appropriate for children aged 5-14?

INAPPROPRIATE ONLY IF it contains:
- Explicit violence, gore, death, killing
- Weapons used for harm (guns, knives for violence)
- Horror/scary monsters meant to frighten
- Adult content, drugs, alcohol
- Real-world crime or danger

APPROPRIATE (these are GOOD for kids):
- Friendly animals (mice, rabbits, dogs, cats, etc.)
- Adventure, exploration, quests
- Magic, fantasy, imagination
- Brave/courageous characters facing challenges
- Space, dinosaurs, robots
- Friendship, kindness, helping others
- Overcoming fears, learning lessons

Message: "{message}"

Answer APPROPRIATE or INAPPROPRIATE (default to APPROPRIATE if uncertain):"""
    
    @staticmethod
    def get_conversational_prompt(
        context: str,
        history: str,
        age_range: Tuple[int, int]
    ) -> str:
        """
        Main prompt for Storybuddy conversational agent.
        
        Args:
            context: User context (name, age, preferences)
            history: Recent conversation history
            age_range: Tuple of (min_age, max_age)
            
        Returns:
            Formatted conversational agent prompt
        """
        min_age, max_age = age_range
        return f"""You are Storybuddy, a friendly AI storytelling companion for kids aged {min_age}-{max_age}.

Be warm, encouraging, and brief (2-3 sentences). Use simple words and occasional emojis 😊✨

When they want a story, respond with excitement: "Great idea! Let me create that for you! ✨"

REFUSE inappropriate content (violence, scary, adult themes) and redirect positively:
"That's too scary! How about friendly dragons or space adventure instead? 🐉🚀"

{context if context else ""}

Recent chat:
{history}

Be helpful and fun! ✨"""
    
    @staticmethod
    def get_context_analyzer_prompt(conversation: str, request: str) -> str:
        """
        Prompt for analyzing conversation context to enhance story requests.
        
        Args:
            conversation: Recent conversation history
            request: Current story request
            
        Returns:
            Formatted context analyzer prompt
        """
        return f"""ANALYZE CONTEXT AND FORMAT OUTPUT - DO NOT EXPLAIN OR DISCUSS

Conversation:
{conversation}

User request: "{request}"

IF conversation contains "STORY_CONTENT:", this is a MODIFICATION:

Format:
MODIFY_STORY: {request}
LENGTH: [extract length: "short", "medium", or "long" based on request, default "short"]

PREVIOUS_STORY:
[copy full story after STORY_CONTENT:]

Length detection rules:
- "longer", "long", "make it long", "more paragraphs" → "long"
- "shorter", "short", "make it short" → "short"
- "medium", "medium length" → "medium"
- No mention → "short"

IF NO "STORY_CONTENT:", return 2-10 keywords only.

OUTPUT FORMAT ONLY - NO EXPLANATIONS OR REASONING:"""



    @staticmethod
    def get_user_info_extraction_prompt(message: str) -> str:
        """
        Prompt for extracting user information (name, age) from messages.
        
        Args:
            message: User's message
            
        Returns:
            Formatted extraction prompt
        """
        return f"""Extract user information ONLY if the user is introducing THEMSELVES.

DO NOT extract names if:
- Requesting a story about someone ("tell me a story about Justin")
- Mentioning story characters ("add a boy named Vamshi")
- Talking about other people

ONLY extract if user introduces themselves:
- "My name is John"
- "I'm Sarah"
- "Call me Alex"
- "I am 7 years old"

Message: "{message}"

Return JSON:
{{
  "name": "user's name ONLY if introducing themselves, null otherwise",
  "age": "user's age as number if mentioned, null otherwise"
}}

Return ONLY the JSON, nothing else."""

    @staticmethod
    def get_story_request_detection_prompt(message: str) -> str:
        """
        Prompt for detecting if message is requesting a story.
        
        Args:
            message: User's message
            
        Returns:
            Formatted detection prompt
        """
        return f"""Is this a story request?

Message: "{message}"

Story requests: "tell me a story", "add a lion", "change the ending", "continue"

Answer YES or NO:"""

    @staticmethod
    def get_self_inquiry_detection_prompt(message: str) -> str:
        """
        Prompt for detecting if user is asking about themselves.
        
        Args:
            message: User's message
            
        Returns:
            Formatted detection prompt
        """
        return f"""Is this message asking about the user's own information (name, age, etc.)?

Examples:
- "what is my name?"
- "do you remember me?"
- "who am I?"

Message: "{message}"

Answer with ONLY "yes" or "no"."""


# ============================================================================
# STORYTELLER AGENT PROMPTS
# ============================================================================

class StorytellerPrompts:
    """Prompts for the storyteller agent."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        System prompt for storyteller agent.
        
        Returns:
            Storyteller system prompt
        """
        return """You are a master children's storyteller who creates magical, engaging stories for kids aged 5-14 years old.

Your storytelling style:
- Warm, engaging, and imaginative
- Uses simple, clear language that kids understand
- Creates relatable characters children love
- Builds exciting but age-appropriate adventures
- Includes positive messages and gentle life lessons
- Perfect for reading aloud or bedtime
- Always appropriate and safe for children"""

    @staticmethod
    def get_story_creation_prompt(
        prompt: str,
        target_word_count: str,
        length_type: str,
        previous_context: str = ""
    ) -> str:
        """
        Prompt for creating a new story or modifying an existing one.
        
        Args:
            prompt: Story idea/theme OR modification request with PREVIOUS_STORY
            target_word_count: Target word count range (e.g., "300-400")
            length_type: "short", "medium", or "long"
            previous_context: Optional context from previous stories
            
        Returns:
            Formatted story creation prompt
        """
        # Check if this is a modification request
        if "MODIFY_STORY:" in prompt and "PREVIOUS_STORY:" in prompt:
            # Extract modification request and previous story
            parts = prompt.split("PREVIOUS_STORY:")
            modification_request = parts[0].replace("MODIFY_STORY:", "").strip()
            previous_story = parts[1].strip()
            
            # Paragraph structure requirements based on length type
            if length_type == "short":
                structure = "EXACTLY 2 paragraphs"
            else:
                structure = "EXACTLY 3 paragraphs"
            
            return f"""MODIFY the following story based on the user's request.

USER'S MODIFICATION REQUEST: "{modification_request}"

PREVIOUS STORY:
{previous_story}

CRITICAL INSTRUCTIONS:
✓ Keep the SAME title, characters, setting, and plot structure
✓ Only ADD or CHANGE what the user specifically requested
✓ Maintain the same tone, style, and moral
✓ Keep it {structure} with single blank line separators
✓ Target word count: {target_word_count} words
✓ Age range: 5-14 years old

Example modifications:
- "add a boy named Vamshi" → Insert Vamshi as a new character, keep everything else
- "add a lion" → Introduce a lion into the existing story without changing the plot
- "change the ending" → Keep the story the same but write a different conclusion

📝 FORMAT:
TITLE: [Keep the SAME title]
STORY: [Modified story with user's changes incorporated]"""
        
        # Regular new story creation
        # Paragraph structure requirements based on length type
        if length_type == "short":
            structure = """
STRUCTURE (IMPORTANT):
- Write the story in EXACTLY 2 paragraphs.
  1) Introduction (setup characters and setting)
  2) Conclusion (resolve and state the gentle moral)
- Separate paragraphs with a single blank line.
"""
        else:
            structure = """
STRUCTURE (IMPORTANT):
- Write the story in EXACTLY 3 paragraphs.
  1) Introduction (setup characters and setting)
  2) Extension/Development (the adventure or challenge grows)
  3) Conclusion (resolution and gentle moral)
- Separate paragraphs with a single blank line.
"""

        return f"""Create a wonderful story based on this idea: "{prompt}"

📖 STORY REQUIREMENTS:
✓ Word count: {target_word_count} words
✓ Age range: 5-14 years old
✓ Language: Simple, clear, easy to understand
✓ Tone: Warm, friendly, and encouraging
✓ Content: 100% child-appropriate (no violence, scary content, or adult themes)

✨ STORY ELEMENTS TO INCLUDE:
- A catchy, short title (3-7 words)
- Engaging characters children can relate to
- A clear beginning, middle, and end
- Exciting but safe adventures
- A gentle moral or positive lesson (kindness, courage, friendship, honesty, etc.)
- Descriptive language that sparks imagination
- Dialogue that feels natural and fun

🎨 STORYTELLING TIPS:
- Make it fun and engaging to read
- Use sensory details (sounds, colors, feelings)
- Keep sentences short and clear
- Include moments of excitement or wonder
- End on a positive, satisfying note
- Make it memorable!{previous_context}
{structure}

📝 FORMAT (IMPORTANT):
TITLE: [Your creative story title]
STORY: [Your complete story here]"""

    @staticmethod
    def get_refinement_prompt(
        title: str,
        content: str,
        feedback: str,
        length_type: str = None
    ) -> str:
        """
        Prompt for refining an existing story based on feedback.
        
        Args:
            title: Current story title
            content: Current story content
            feedback: Judge's feedback
            length_type: Optional story length type
            
        Returns:
            Formatted refinement prompt
        """
        # Structure guidance for revision if provided
        structure = ""
        if length_type:
            if length_type == "short":
                structure = """
STRUCTURE (KEEP THIS):
- Keep EXACTLY 2 paragraphs: Introduction, then Conclusion.
- Separate paragraphs with a single blank line.
"""
            else:
                structure = """
STRUCTURE (KEEP THIS):
- Keep EXACTLY 3 paragraphs: Introduction, Extension/Development, Conclusion.
- Separate paragraphs with a single blank line.
"""

        return f"""The story needs improvement based on this feedback:

{feedback}

📝 YOUR TASK:
Revise the story to address the feedback while keeping the core idea and what makes it special.

CURRENT STORY:
TITLE: {title}
STORY: {content}

GUIDELINES FOR REVISION:
- Fix any issues mentioned in feedback
- Keep the story fun and engaging
- Maintain child-appropriate language (ages 5-14)
- Ensure the moral/lesson is clear but not preachy
- Keep the magical feeling of the story
- Make improvements without changing the main idea
{structure}

FORMAT YOUR RESPONSE:
TITLE: [improved story title]
STORY: [improved story content]"""

    @staticmethod
    def get_refinement_system_prompt() -> str:
        """
        System prompt for story refinement.
        
        Returns:
            Refinement system prompt
        """
        return """You are a master children's storyteller who creates magical, engaging stories for kids aged 5-14 years old.
You excel at taking feedback and improving stories while keeping what makes them special."""


# ============================================================================
# JUDGE AGENT PROMPTS
# ============================================================================

class JudgePrompts:
    """Prompts for the judge agent."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        System prompt for judge agent.
        
        Returns:
            Judge system prompt
        """
        return "You are a children's content quality judge."

    @staticmethod
    def get_evaluation_prompt(title: str, content: str) -> str:
        """
        Prompt for evaluating story quality.
        
        Args:
            title: Story title
            content: Story content
            
        Returns:
            Formatted evaluation prompt
        """
        return f"""Evaluate this bedtime story for ages 5-10.

Story Title: {title}
Story Content:
{content}

Evaluate this story on:
1. Clarity (1-10): Is the language simple and clear for 5-10 year olds?
2. Moral Value (1-10): Does it teach a gentle, positive lesson?
3. Age Appropriateness (1-10): Is it suitable and engaging for the target age?

Provide your evaluation in this exact format:
CLARITY: [score]
MORAL: [score]
AGE_APPROPRIATE: [score]
OVERALL: [score out of 10]
APPROVED: [YES or NO]
FEEDBACK: [specific suggestions for improvement if not approved, or praise if approved]"""


# ============================================================================
# EXPORT ALL PROMPT CLASSES
# ============================================================================

__all__ = [
    'ConversationalPrompts',
    'StorytellerPrompts',
    'JudgePrompts',
]
