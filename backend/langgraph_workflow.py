"""
LangGraph Multi-Agent Workflow for Bedtime Story Application

This module implements a sophisticated multi-agent system using LangGraph that combines:
1. **Conversational Agent** - Handles natural interactions, collects preferences, detects story requests
2. **Storyteller Agent** - Creates engaging bedtime stories
3. **Judge Agent** - Evaluates and provides feedback for iterative improvement
4. **Paragraph Formatter** - Ensures proper story structure

The graph is fully visible in LangSmith Studio showing all agent nodes, state transitions,
and decision points.

Architecture:
    conversation_agent -> [story_requested?] -> story_creator -> story_evaluator 
    -> [approved?] -> paragraph_formatter -> final_story
    -> [not approved?] -> increment_iteration -> story_creator (loop)
"""

from typing import TypedDict, Annotated, Literal, Optional, List, Dict
from dataclasses import dataclass
import operator
import os

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from conversational_agent import ConversationalAgent
from agents import StorytellerAgent, JudgeAgent
from utils import count_paragraphs, setup_logger
from config import settings

logger = setup_logger(__name__)


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class ConversationState(TypedDict):
    """
    State for conversational interaction phase.
    
    Tracks user messages, extracted preferences, and determines if story
    generation should be triggered.
    """
    # Messages
    messages: Annotated[list[BaseMessage], operator.add]
    user_message: str
    agent_response: str
    
    # User Context
    session_id: str
    user_name: Optional[str]
    user_age: Optional[int]
    
    # Story Request Detection
    should_generate_story: bool
    story_prompt: Optional[str]
    story_length: Literal["short", "medium", "long"]
    
    # Navigation
    next_step: Literal["continue_chat", "generate_story", "end"]


class StoryGenerationState(TypedDict):
    """
    State for story generation phase with iterative refinement.
    
    Implements a reflection pattern where the story is created, evaluated,
    and refined until it meets quality standards or max iterations reached.
    """
    # Input
    prompt: str
    length_type: Literal["short", "medium", "long"]
    session_id: str
    
    # Story Content
    story_title: str
    story_content: str
    
    # Quality Control
    iteration: int
    max_iterations: int
    evaluation_feedback: str
    quality_scores: Dict[str, int]  # clarity, moral_value, age_appropriate
    overall_score: int
    approved: bool
    
    # Paragraph Structure
    target_paragraphs: int
    actual_paragraphs: int
    structure_correct: bool
    
    # History & Output
    revision_history: Annotated[list[dict], operator.add]
    final_story: Optional[Dict]
    
    # Navigation
    next_step: Literal["evaluate", "refine", "format_paragraphs", "finalize", "end"]


# ============================================================================
# CONVERSATION NODES
# ============================================================================

class ConversationNode:
    """
    Handles natural conversation and detects story requests.
    
    This node uses the ConversationalAgent to:
    - Respond to greetings, questions, and general chat
    - Extract user information (name, age)
    - Detect when user wants a story
    - Build context-aware story prompts
    """
    
    def __init__(self, agent: ConversationalAgent):
        self.agent = agent
        
    def __call__(self, state: ConversationState) -> ConversationState:
        """Process user message through conversational agent"""
        
        logger.info(f"💬 Conversation Node: Processing message")
        
        # Process message
        result = self.agent.process_message(
            message=state["user_message"],
            conversation_history=[],  # Can be extended to use state["messages"]
            session_id=state["session_id"]
        )
        
        # Update state based on agent response
        updates = {
            "agent_response": result["response"],
            "should_generate_story": result["should_generate_story"],
            "messages": [
                HumanMessage(content=state["user_message"]),
                AIMessage(content=result["response"])
            ]
        }
        
        # If story requested, extract details
        if result["should_generate_story"]:
            updates["story_prompt"] = result.get("story_prompt", state["user_message"])
            updates["next_step"] = "generate_story"
            logger.info(f"📖 Story requested: '{updates['story_prompt']}'")
        else:
            updates["next_step"] = "end"
        
        return updates


def route_after_conversation(state: ConversationState) -> Literal["generate_story", "end"]:
    """
    Routing logic after conversation.
    
    Decides whether to move to story generation or end the conversation.
    """
    next_step = state.get("next_step", "end")
    logger.info(f"🔀 Routing: {next_step}")
    return next_step


# ============================================================================
# STORY GENERATION NODES
# ============================================================================

class StoryCreatorNode:
    """
    Creates or refines stories based on iteration state.
    
    - First iteration: Creates initial story from prompt
    - Subsequent iterations: Refines story based on judge feedback
    """
    
    def __init__(self, storyteller: StorytellerAgent):
        self.storyteller = storyteller
        
    def __call__(self, state: StoryGenerationState) -> StoryGenerationState:
        """Create or refine story"""
        
        iteration = state.get("iteration", 1)
        is_refinement = iteration > 1
        
        if is_refinement:
            logger.info(f"🔄 Story Creator (Iteration {iteration}): Refining based on feedback")
            
            result = self.storyteller.refine_story(
                title=state["story_title"],
                content=state["story_content"],
                feedback=state["evaluation_feedback"],
                length_type=state["length_type"]
            )
        else:
            logger.info(f"✨ Story Creator (Iteration {iteration}): Creating initial story")
            
            # Get target word count from settings
            word_config = settings.story.WORD_COUNTS[state["length_type"]]
            target_word_count = f"{word_config['min']}-{word_config['max']}"
            
            result = self.storyteller.create_story(
                prompt=state["prompt"],
                target_word_count=target_word_count,
                length_type=state["length_type"],
                previous_stories=[]
            )
        
        # Count paragraphs
        actual_paras = count_paragraphs(result["content"])
        target_paras = settings.story.PARAGRAPH_STRUCTURE[state["length_type"]]
        
        # Track revision
        revision_entry = {
            "iteration": iteration,
            "title": result["title"],
            "content_preview": result["content"][:150] + "...",
            "paragraph_count": actual_paras
        }
        
        return {
            "story_title": result["title"],
            "story_content": result["content"],
            "actual_paragraphs": actual_paras,
            "target_paragraphs": target_paras,
            "structure_correct": actual_paras == target_paras,
            "revision_history": [revision_entry],
            "next_step": "evaluate"
        }


class StoryEvaluatorNode:
    """
    Evaluates story quality using the Judge Agent.
    
    Checks:
    - Clarity (simple, clear language)
    - Moral Value (positive lessons)
    - Age Appropriateness (suitable for 5-14 year olds)
    """
    
    def __init__(self, judge: JudgeAgent):
        self.judge = judge
        
    def __call__(self, state: StoryGenerationState) -> StoryGenerationState:
        """Evaluate story quality"""
        
        logger.info(f"⚖️ Story Evaluator: Judging story quality")
        
        evaluation = self.judge.evaluate_story(
            title=state["story_title"],
            content=state["story_content"]
        )
        
        # Determine approval (strict criteria for quality)
        # Note: Judge returns camelCase keys: moralValue, ageAppropriateness
        approved = (
            evaluation["score"] >= 9 and
            evaluation["clarity"] >= 8 and
            evaluation["moralValue"] >= 8 and
            evaluation["ageAppropriateness"] >= 8
        )
        
        logger.info(
            f"📊 Evaluation: Score={evaluation['score']}/10, "
            f"Approved={approved}"
        )
        
        # Decide next step
        if approved and state["structure_correct"]:
            next_step = "finalize"
        elif not state["structure_correct"]:
            next_step = "format_paragraphs"
        elif state["iteration"] >= state["max_iterations"]:
            # Max iterations reached, finalize anyway
            next_step = "finalize"
        else:
            next_step = "refine"
        
        return {
            "quality_scores": {
                "clarity": evaluation["clarity"],
                "moral_value": evaluation["moralValue"],
                "age_appropriateness": evaluation["ageAppropriateness"]
            },
            "overall_score": evaluation["score"],
            "evaluation_feedback": evaluation["feedback"],
            "approved": approved,
            "next_step": next_step
        }


class ParagraphFormatterNode:
    """
    Ensures story has correct paragraph structure.
    
    Different lengths require different structures:
    - Short: 2 paragraphs
    - Medium: 3 paragraphs  
    - Long: 3 paragraphs
    """
    
    def __init__(self, storyteller: StorytellerAgent):
        self.storyteller = storyteller
        
    def __call__(self, state: StoryGenerationState) -> StoryGenerationState:
        """Format story into correct paragraph structure"""
        
        if state["structure_correct"]:
            logger.info("✅ Paragraph structure already correct")
            return {"next_step": "evaluate"}
        
        logger.info(
            f"🧩 Paragraph Formatter: Restructuring from "
            f"{state['actual_paragraphs']} to {state['target_paragraphs']} paragraphs"
        )
        
        # Build structure feedback
        target = state["target_paragraphs"]
        if target == 2:
            feedback = (
                "Please reformat the story into EXACTLY 2 paragraphs separated by a blank line.\n"
                "Paragraph 1: Introduction and setup.\n"
                "Paragraph 2: Conclusion and moral.\n"
                "Keep the same content, only adjust paragraph breaks."
            )
        else:
            feedback = (
                "Please reformat the story into EXACTLY 3 paragraphs separated by blank lines.\n"
                "Paragraph 1: Introduction and setup.\n"
                "Paragraph 2: Development and adventure.\n"
                "Paragraph 3: Resolution and moral.\n"
                "Keep the same content, only adjust paragraph breaks."
            )
        
        result = self.storyteller.refine_story(
            title=state["story_title"],
            content=state["story_content"],
            feedback=feedback,
            length_type=state["length_type"]
        )
        
        actual_paras = count_paragraphs(result["content"])
        structure_correct = actual_paras == target
        
        logger.info(f"📐 After formatting: {actual_paras} paragraphs")
        
        return {
            "story_title": result["title"],
            "story_content": result["content"],
            "actual_paragraphs": actual_paras,
            "structure_correct": structure_correct,
            "next_step": "evaluate"
        }


class IncrementIterationNode:
    """Simple node to increment the iteration counter"""
    
    def __call__(self, state: StoryGenerationState) -> StoryGenerationState:
        """Increment iteration for next refinement loop"""
        new_iteration = state.get("iteration", 1) + 1
        logger.info(f"🔢 Incrementing to iteration {new_iteration}")
        
        return {
            "iteration": new_iteration,
            "next_step": "refine"
        }


class FinalizeStoryNode:
    """Packages the final approved story with all metadata"""
    
    def __call__(self, state: StoryGenerationState) -> StoryGenerationState:
        """Create final story package"""
        
        logger.info("✅ Finalizing approved story")
        
        final_story = {
            "title": state["story_title"],
            "content": state["story_content"],
            "prompt": state["prompt"],
            "length_type": state["length_type"],
            "iterations": state["iteration"],
            "final_scores": state["quality_scores"],
            "overall_score": state["overall_score"],
            "paragraph_count": state["actual_paragraphs"],
            "revision_history": state.get("revision_history", [])
        }
        
        return {
            "final_story": final_story,
            "next_step": "end"
        }


def route_after_evaluation(
    state: StoryGenerationState
) -> Literal["refine", "format_paragraphs", "finalize"]:
    """
    Routing logic after story evaluation.
    
    Decision tree:
    1. If structure incorrect -> format_paragraphs
    2. Elif approved and structure correct -> finalize
    3. Elif max iterations reached -> finalize (accept as-is)
    4. Else -> refine (continue improvement loop)
    """
    next_step = state.get("next_step", "finalize")
    logger.info(f"🔀 Routing after evaluation: {next_step}")
    return next_step


# ============================================================================
# GRAPH BUILDERS
# ============================================================================

def create_conversation_graph(agent: ConversationalAgent) -> StateGraph:
    """
    Build the conversation graph.
    
    Simple linear flow:
    conversation_agent -> END
    (The routing decision is handled externally by checking the state)
    """
    graph = StateGraph(ConversationState)
    
    # Add nodes
    conversation_node = ConversationNode(agent)
    graph.add_node("conversation_agent", conversation_node)
    
    # Set entry point
    graph.set_entry_point("conversation_agent")
    
    # Always end after conversation node
    # The decision to generate a story is handled by checking state.should_generate_story
    graph.add_edge("conversation_agent", END)
    
    return graph


def create_story_generation_graph(
    storyteller: StorytellerAgent,
    judge: JudgeAgent
) -> StateGraph:
    """
    Build the story generation graph with reflection pattern.
    
    Flow:
    story_creator -> story_evaluator -> [decision]
    
    Decision branches:
    - If structure wrong -> format_paragraphs -> story_evaluator
    - If approved -> finalize -> END
    - If not approved and under max iterations -> increment -> story_creator (loop)
    - If max iterations reached -> finalize -> END
    """
    graph = StateGraph(StoryGenerationState)
    
    # Add nodes
    story_creator = StoryCreatorNode(storyteller)
    story_evaluator = StoryEvaluatorNode(judge)
    paragraph_formatter = ParagraphFormatterNode(storyteller)
    increment_iteration = IncrementIterationNode()
    finalize_story = FinalizeStoryNode()
    
    graph.add_node("story_creator", story_creator)
    graph.add_node("story_evaluator", story_evaluator)
    graph.add_node("paragraph_formatter", paragraph_formatter)
    graph.add_node("increment_iteration", increment_iteration)
    graph.add_node("finalize_story", finalize_story)
    
    # Set entry point
    graph.set_entry_point("story_creator")
    
    # Add edges
    graph.add_edge("story_creator", "story_evaluator")
    graph.add_edge("paragraph_formatter", "story_evaluator")
    graph.add_edge("increment_iteration", "story_creator")
    graph.add_edge("finalize_story", END)
    
    # Add conditional routing after evaluation
    graph.add_conditional_edges(
        "story_evaluator",
        route_after_evaluation,
        {
            "format_paragraphs": "paragraph_formatter",
            "refine": "increment_iteration",
            "finalize": "finalize_story"
        }
    )
    
    return graph


def create_complete_workflow(
    groq_api_key: str,
    langsmith_api_key: Optional[str] = None
):
    """
    Create the complete bedtime story workflow with both graphs.
    
    This creates two separate but connected graphs:
    1. Conversation Graph - handles user interaction
    2. Story Generation Graph - creates and refines stories
    
    Both graphs are visible in LangSmith Studio for debugging and monitoring.
    
    Args:
        groq_api_key: Groq API key for LLM access
        langsmith_api_key: Optional LangSmith API key for tracing
        
    Returns:
        Tuple of (conversation_app, story_generation_app)
    """
    
    # Initialize agents
    conversational_agent = ConversationalAgent(
        groq_api_key=groq_api_key,
        langsmith_api_key=langsmith_api_key
    )
    
    storyteller_agent = StorytellerAgent(
        groq_api_key=groq_api_key,
        langsmith_api_key=langsmith_api_key
    )
    
    judge_agent = JudgeAgent(
        groq_api_key=groq_api_key,
        langsmith_api_key=langsmith_api_key
    )
    
    # Build graphs
    conversation_graph = create_conversation_graph(conversational_agent)
    story_graph = create_story_generation_graph(storyteller_agent, judge_agent)
    
    # Compile with memory
    memory = MemorySaver()
    conversation_app = conversation_graph.compile(checkpointer=memory)
    story_app = story_graph.compile(checkpointer=memory)
    
    logger.info("✅ LangGraph workflow created successfully")
    logger.info("   - Conversation Graph: Ready")
    logger.info("   - Story Generation Graph: Ready")
    logger.info("   - Graphs visible in LangSmith Studio")
    
    return conversation_app, story_app


# ============================================================================
# HELPER FUNCTIONS FOR INTEGRATION
# ============================================================================

def run_conversation(
    graph,
    user_message: str,
    session_id: str = "default",
    story_length: str = "medium"
) -> Dict:
    """
    Run a conversation turn through the graph.
    
    Args:
        graph: Compiled conversation graph
        user_message: User's input message
        session_id: Session identifier for context
        story_length: Preferred story length
        
    Returns:
        Dict with response, should_generate_story, and story_prompt
    """
    
    config = {"configurable": {"thread_id": session_id}}
    
    initial_state: ConversationState = {
        "messages": [],
        "user_message": user_message,
        "agent_response": "",
        "session_id": session_id,
        "user_name": None,
        "user_age": None,
        "should_generate_story": False,
        "story_prompt": None,
        "story_length": story_length,
        "next_step": "continue_chat"
    }
    
    result = graph.invoke(initial_state, config)
    
    return {
        "response": result["agent_response"],
        "should_generate_story": result["should_generate_story"],
        "story_prompt": result.get("story_prompt"),
        "story_length": result.get("story_length", "medium")
    }


def run_story_generation(
    graph,
    prompt: str,
    length_type: str = "medium",
    session_id: str = "default",
    max_iterations: int = None
) -> Dict:
    """
    Run story generation through the reflection graph.
    
    Args:
        graph: Compiled story generation graph
        prompt: Story prompt/theme
        length_type: "short", "medium", or "long"
        session_id: Session identifier
        max_iterations: Max refinement iterations (default from settings)
        
    Returns:
        Final story dict with title, content, and metadata
    """
    
    if max_iterations is None:
        max_iterations = settings.story.MAX_ITERATIONS
    
    config = {"configurable": {"thread_id": session_id}}
    
    target_paragraphs = settings.story.PARAGRAPH_STRUCTURE[length_type]
    
    initial_state: StoryGenerationState = {
        "prompt": prompt,
        "length_type": length_type,
        "session_id": session_id,
        "story_title": "",
        "story_content": "",
        "iteration": 1,
        "max_iterations": max_iterations,
        "evaluation_feedback": "",
        "quality_scores": {},
        "overall_score": 0,
        "approved": False,
        "target_paragraphs": target_paragraphs,
        "actual_paragraphs": 0,
        "structure_correct": False,
        "revision_history": [],
        "final_story": None,
        "next_step": "evaluate"
    }
    
    result = graph.invoke(initial_state, config)
    
    return result.get("final_story", {})


# ============================================================================
# EXPORT FOR LANGGRAPH SERVER
# ============================================================================

def get_conversation_graph():
    """
    Export conversation graph for LangGraph Server.
    
    Usage in langgraph.json:
    {
      "graphs": {
        "conversation": "langgraph_workflow:get_conversation_graph"
      }
    }
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable required")
    
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    agent = ConversationalAgent(groq_api_key, langsmith_api_key)
    graph = create_conversation_graph(agent)
    
    return graph.compile(checkpointer=MemorySaver())


def get_story_generation_graph():
    """
    Export story generation graph for LangGraph Server.
    
    Usage in langgraph.json:
    {
      "graphs": {
        "story_generation": "langgraph_workflow:get_story_generation_graph"
      }
    }
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable required")
    
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    storyteller = StorytellerAgent(groq_api_key, langsmith_api_key)
    judge = JudgeAgent(groq_api_key, langsmith_api_key)
    
    graph = create_story_generation_graph(storyteller, judge)
    
    return graph.compile(checkpointer=MemorySaver())
