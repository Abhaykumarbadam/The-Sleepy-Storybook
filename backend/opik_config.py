"""
Opik Configuration for LLM Evaluation and Tracing

This module sets up Opik for tracking:
- LLM performance (latency, tokens, model used)
- Story quality evaluation metrics
- Workflow execution traces

Opik can run in two modes:
1. Local mode: For development/testing (no account needed)
2. Cloud mode: Connected to Comet ML for team collaboration
"""

import os
from typing import Optional
from opik import Opik, track
from opik.integrations.langchain import OpikTracer

_opik_client: Optional[Opik] = None
_opik_tracer: Optional[OpikTracer] = None


def initialize_opik(
    use_local: bool = True,
    api_key: Optional[str] = None,
    workspace: Optional[str] = None
) -> Opik:
    """
    Initialize Opik client for LLM evaluation
    
    Args:
        use_local: If True, runs in local mode (no Comet ML account needed)
        api_key: Comet ML API key (only needed for cloud mode)
        workspace: Comet ML workspace name (only needed for cloud mode)
    
    Returns:
        Opik client instance
    """
    global _opik_client, _opik_tracer
    
    if _opik_client is not None:
        print("✅ Opik already initialized")
        return _opik_client
    
    try:
        if use_local:
            print("🔧 Initializing Opik in LOCAL mode (no Comet ML account needed)")
            _opik_client = Opik(use_local=True)
            print("✅ Opik LOCAL mode initialized successfully!")
            print("📊 View traces at: http://localhost:5173 (run 'opik ui' to start)")
        else:
            print("🔧 Initializing Opik in CLOUD mode (Comet ML)")
            
            # Get credentials from environment if not provided
            api_key = api_key or os.getenv("OPIK_API_KEY") or os.getenv("COMET_API_KEY")
            workspace = workspace or os.getenv("OPIK_WORKSPACE") or os.getenv("COMET_WORKSPACE")
            
            if not api_key:
                raise ValueError(
                    "Opik API key required for cloud mode! "
                    "Set OPIK_API_KEY or COMET_API_KEY environment variable, "
                    "or pass api_key parameter"
                )
            
            _opik_client = Opik(
                api_key=api_key,
                workspace=workspace
            )
            print(f"✅ Opik CLOUD mode initialized! Workspace: {workspace}")
            print(f"📊 View traces at: https://www.comet.com/{workspace}/opik/traces")
        
        # Initialize LangChain tracer integration
        _opik_tracer = OpikTracer()
        print("✅ Opik LangChain tracer initialized")
        
        return _opik_client
        
    except Exception as e:
        print(f"⚠️ Failed to initialize Opik: {e}")
        print("Continuing without Opik evaluation...")
        return None


def get_opik_client() -> Optional[Opik]:
    """Get the initialized Opik client"""
    return _opik_client


def get_opik_tracer() -> Optional[OpikTracer]:
    """Get the Opik LangChain tracer for automatic LLM call tracking"""
    return _opik_tracer


def is_opik_enabled() -> bool:
    """Check if Opik is initialized and enabled"""
    return _opik_client is not None


# Decorator for tracking functions with Opik
def track_with_opik(name: Optional[str] = None, project_name: str = "bedtime-stories"):
    """
    Decorator to track function execution with Opik
    
    Usage:
        @track_with_opik(name="story_creation", project_name="bedtime-stories")
        def create_story(prompt: str):
            # Your code here
            return story
    """
    def decorator(func):
        if is_opik_enabled():
            return track(name=name or func.__name__, project_name=project_name)(func)
        return func
    return decorator


def log_llm_call(
    model_name: str,
    prompt: str,
    completion: str,
    latency_ms: float,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    metadata: Optional[dict] = None
):
    """
    Log an LLM call to Opik for performance tracking
    
    Args:
        model_name: Name of the model used (e.g., "llama-3.3-70b-versatile")
        prompt: Input prompt sent to the model
        completion: Model's response
        latency_ms: Response time in milliseconds
        input_tokens: Number of input tokens (if available)
        output_tokens: Number of output tokens (if available)
        metadata: Additional metadata (agent name, iteration, etc.)
    """
    if not is_opik_enabled():
        return
    
    try:
        client = get_opik_client()
        
        trace = client.trace(
            name=f"LLM Call: {model_name}",
            input={"prompt": prompt},
            output={"completion": completion},
            metadata={
                "model": model_name,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                **(metadata or {})
            }
        )
        
        if latency_ms < 2000:
            score = 1.0  # Fast
        elif latency_ms < 5000:
            score = 0.7  # Medium
        else:
            score = 0.4  # Slow
        
        trace.log_feedback_score(
            name="response_speed",
            value=score
        )
        
    except Exception as e:
        print(f"⚠️ Failed to log LLM call to Opik: {e}")


def log_story_evaluation(
    story_title: str,
    story_content: str,
    quality_scores: dict,
    overall_score: int,
    iteration: int,
    approved: bool,
    metadata: Optional[dict] = None
):
    """
    Log story evaluation results to Opik
    
    Args:
        story_title: Title of the evaluated story
        story_content: Full story content
        quality_scores: Dictionary of quality metrics (clarity, moral_value, etc.)
        overall_score: Overall quality score (0-100)
        iteration: Which iteration this evaluation is from
        approved: Whether the story was approved
        metadata: Additional metadata
    """
    if not is_opik_enabled():
        return
    
    try:
        client = get_opik_client()
        
        trace = client.trace(
            name=f"Story Evaluation: {story_title}",
            input={
                "title": story_title,
                "content_preview": story_content[:200] + "..."
            },
            output={
                "quality_scores": quality_scores,
                "overall_score": overall_score,
                "approved": approved
            },
            metadata={
                "iteration": iteration,
                "story_length": len(story_content),
                "word_count": len(story_content.split()),
                **(metadata or {})
            }
        )
        
        # Log individual quality scores as feedback
        for metric_name, score in quality_scores.items():
            trace.log_feedback_score(
                name=metric_name,
                value=score / 10.0  # Normalize to 0-1
            )
        
        # Log overall score
        trace.log_feedback_score(
            name="overall_quality",
            value=overall_score / 100.0  # Normalize to 0-1
        )
        
        # Log approval status
        trace.log_feedback_score(
            name="approved",
            value=1.0 if approved else 0.0
        )
        
    except Exception as e:
        print(f"⚠️ Failed to log story evaluation to Opik: {e}")


def log_workflow_completion(
    prompt: str,
    final_story: dict,
    total_iterations: int,
    total_time_seconds: float,
    llm_calls_count: int,
    metadata: Optional[dict] = None
):
    """
    Log complete workflow execution to Opik
    
    Args:
        prompt: Original user prompt
        final_story: Final story dictionary with all metadata
        total_iterations: Number of iterations needed
        total_time_seconds: Total execution time
        llm_calls_count: Total number of LLM calls made
        metadata: Additional metadata
    """
    if not is_opik_enabled():
        return
    
    try:
        client = get_opik_client()
        
        # Create trace for workflow
        trace = client.trace(
            name="Story Generation Workflow",
            input={"prompt": prompt},
            output={
                "story_title": final_story.get("title", ""),
                "story_length": len(final_story.get("content", "")),
                "final_score": final_story.get("overall_score", 0)
            },
            metadata={
                "total_iterations": total_iterations,
                "total_time_seconds": total_time_seconds,
                "llm_calls_count": llm_calls_count,
                "iterations_needed": total_iterations,
                **(metadata or {})
            }
        )
        
        # Log efficiency metrics
        trace.log_feedback_score(
            name="efficiency",
            value=1.0 / total_iterations  # Fewer iterations = better
        )
        
        trace.log_feedback_score(
            name="quality",
            value=final_story.get("overall_score", 0) / 100.0
        )
        
    except Exception as e:
        print(f"⚠️ Failed to log workflow completion to Opik: {e}")
