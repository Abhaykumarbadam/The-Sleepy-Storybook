"""
Opik Configuration for LLM Evaluation and Tracing

Tracks LLM performance, story quality metrics, and workflow execution traces.
"""

import os
from typing import Optional
from contextvars import ContextVar
from opik import Opik, track
from opik.integrations.langchain import OpikTracer

_opik_client: Optional[Opik] = None
_opik_tracer: Optional[OpikTracer] = None
_current_trace: ContextVar[Optional[object]] = ContextVar('current_trace', default=None)


def initialize_opik(project_name: str = "Sleepy-Storybook") -> Opik:
    """
    Initialize Opik client for LLM evaluation in local mode
    
    Args:
        project_name: Name of the Opik project (default: "Sleepy-Storybook")
    
    Returns:
        Opik client instance
    """
    global _opik_client, _opik_tracer
    
    if _opik_client is not None:
        print("✅ Opik already initialized")
        return _opik_client
    
    try:
        print(f"🔧 Initializing Opik in LOCAL mode for project: {project_name}")
        _opik_client = Opik(
            host="http://localhost:8080",
            project_name=project_name
        )
        print("✅ Opik LOCAL mode initialized successfully!")
        print(f"📊 View traces at: http://localhost:5173/default/projects/{project_name}")
        print("💡 Opik API: http://localhost:8080 | UI: http://localhost:5173")
        
        _opik_tracer = OpikTracer(project_name=project_name)
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


def start_workflow_trace(name: str, input_data: dict, metadata: Optional[dict] = None):
    """
    Start a parent trace for the entire workflow
    
    Args:
        name: Name of the workflow (e.g., "Story Generation")
        input_data: Input data for the workflow
        metadata: Additional metadata
    
    Returns:
        Trace object or None if Opik is not enabled
    """
    if not is_opik_enabled():
        return None
    
    try:
        client = get_opik_client()
        trace = client.trace(
            name=name,
            input=input_data,
            metadata=metadata or {}
        )
        _current_trace.set(trace)
        return trace
    except Exception as e:
        print(f"⚠️ Failed to start workflow trace: {e}")
        return None


def end_workflow_trace(output_data: dict, metadata: Optional[dict] = None):
    """
    End the parent trace and log output
    
    Args:
        output_data: Final output data
        metadata: Additional metadata
    """
    if not is_opik_enabled():
        return
    
    try:
        trace = _current_trace.get()
        if trace:
            trace.update(
                output=output_data,
                metadata=metadata or {}
            )
            _current_trace.set(None)
    except Exception as e:
        print(f"⚠️ Failed to end workflow trace: {e}")


def get_current_trace():
    """Get the current parent trace"""
    return _current_trace.get()


# Decorator for tracking functions with Opik
def track_with_opik(name: Optional[str] = None, project_name: str = "Sleepy-Storybook"):
    """
    Decorator to track function execution with Opik
    
    Usage:
        @track_with_opik(name="story_creation", project_name="Sleepy-Storybook")
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
    Log an LLM call as a span under the current trace
    
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
        parent_trace = get_current_trace()
        if not parent_trace:
            # No parent trace, skip logging
            return
        
        span = parent_trace.span(
            name=f"LLM Call: {model_name}",
            input={"prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt},
            output={"completion": completion[:200] + "..." if len(completion) > 200 else completion},
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
        
        span.log_feedback_score(
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
    Log story evaluation as a span under the current trace
    
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
        parent_trace = get_current_trace()
        if not parent_trace:
            # No parent trace, skip logging
            return
        
        span = parent_trace.span(
            name=f"Story Evaluation (Iteration {iteration})",
            input={
                "title": story_title,
                "content_preview": story_content[:200] + "..." if len(story_content) > 200 else story_content
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
            span.log_feedback_score(
                name=metric_name,
                value=score / 10.0  # Normalize to 0-1
            )
        
        # Log overall score
        span.log_feedback_score(
            name="overall_quality",
            value=overall_score / 100.0  # Normalize to 0-1
        )
        
        # Log approval status
        span.log_feedback_score(
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
    Complete the workflow trace by adding final output and metrics
    
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
        parent_trace = get_current_trace()
        if not parent_trace:
            # No parent trace, skip logging
            return
        
        # Update the parent trace with final output
        end_workflow_trace(
            output_data={
                "story_title": final_story.get("title", ""),
                "story_content": final_story.get("content", "")[:300] + "...",
                "story_length": len(final_story.get("content", "")),
                "final_score": final_story.get("overall_score", 0),
                "iterations_needed": total_iterations
            },
            metadata={
                "total_iterations": total_iterations,
                "total_time_seconds": total_time_seconds,
                "llm_calls_count": llm_calls_count,
                "length_type": final_story.get("length_type", "unknown"),
                **(metadata or {})
            }
        )
        
        # Log efficiency metrics
        parent_trace.log_feedback_score(
            name="efficiency",
            value=1.0 / total_iterations if total_iterations > 0 else 1.0
        )
        
        parent_trace.log_feedback_score(
            name="quality",
            value=final_story.get("overall_score", 0) / 100.0
        )
        
    except Exception as e:
        print(f"⚠️ Failed to log workflow completion to Opik: {e}")
