"""
AI Agents Module - Storyteller and Judge Agents using LangChain + Groq

This module implements the two-agent system:
1. Storyteller Agent - Creates bedtime stories for children
2. Judge Agent - Evaluates story quality and provides feedback

Integrated with:
- LangSmith: For development tracing and debugging
- Opik: For LLM performance evaluation and metrics
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List, Optional
import os
import re
import time

from config.prompts import StorytellerPrompts, JudgePrompts
from opik_config import log_llm_call, get_opik_tracer


class StorytellerAgent:
    """
    The Storyteller Agent creates engaging bedtime stories for children aged 5-10
    
    This agent uses the Groq LLM to generate stories based on user prompts.
    It can create new stories or refine existing ones based on judge feedback.
    """
    
    def __init__(self, groq_api_key: str, langsmith_api_key: Optional[str] = None):
        """
        Initialize the Storyteller Agent
        
        Args:
            groq_api_key: API key for Groq LLM service
            langsmith_api_key: Optional API key for LangSmith tracing
        """
        if langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "bedtime-stories")
        
        self.groq_api_key = groq_api_key
        env_list = os.getenv("GROQ_MODEL_STORYTELLER") or os.getenv("GROQ_MODEL") or ""
        self.model_candidates = [m.strip() for m in env_list.split(",") if m.strip()] or [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]
        self.temperature = 0.8
        self.max_tokens = 700
        
        self.llm = ChatGroq(
            api_key=self.groq_api_key,
            model=self.model_candidates[0], 
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        self.current_model = self.model_candidates[0]
        
        print("Storyteller Agent initialized (Groq) with model fallback:", ", ".join(self.model_candidates))

    def _invoke_with_fallback(self, messages, agent_name="storyteller"):
        """Invoke LLM with fallback and Opik tracking"""
        last_err = None
        for model in self.model_candidates:
            try:
                start_time = time.time()
                
                if model != self.current_model:
                    print(f"Switching to model: {model}")
                    self.llm = ChatGroq(
                        api_key=self.groq_api_key,
                        model=model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    self.current_model = model
                
                opik_tracer = get_opik_tracer()
                config = {"callbacks": [opik_tracer]} if opik_tracer else {}
                
                response = self.llm.invoke(messages, config=config)
                
                latency_ms = (time.time() - start_time) * 1000
                
                log_llm_call(
                    model_name=model,
                    prompt=str(messages),
                    completion=response.content,
                    latency_ms=latency_ms,
                    input_tokens=getattr(response, 'usage', {}).get('prompt_tokens'),
                    output_tokens=getattr(response, 'usage', {}).get('completion_tokens'),
                    metadata={
                        "agent": agent_name,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                
                return response
                
            except Exception as e:
                msg = str(e).lower()
                last_err = e
                print(f"⚠️ Storyteller model '{model}' failed: {e}")
                if ("rate limit" in msg) or ("429" in msg) or ("limit" in msg and "token" in msg) or ("decommission" in msg) or ("invalid" in msg):
                    print("↪️ Trying next Groq model due to rate limit or model issue...")
                    continue
                else:
                    break
        raise last_err if last_err else RuntimeError("All Groq models failed for storyteller")
    
    def create_story(
        self, 
        prompt: str, 
        target_word_count: str,
        length_type: str,
        previous_stories: List[Dict] = None
    ) -> Dict[str, str]:
        """
        Create a new bedtime story based on user prompt
        
        Args:
            prompt: What the user wants the story to be about
            target_word_count: Target range like "300-400"
            previous_stories: List of previous stories for context
            
        Returns:
            Dict with 'title' and 'content' keys
        """
        previous_context = ""
        if previous_stories and len(previous_stories) > 0:
            previous_context = "\n\nHere are some examples of previously created stories to match the tone and style:\n"
            for story in previous_stories:
                previous_context += f"\nTitle: {story['title']}\n{story['content'][:200]}...\n"
        
        # Get system prompt from prompts module
        system_prompt = StorytellerPrompts.get_system_prompt()
        
        # Get user prompt from prompts module
        user_prompt = StorytellerPrompts.get_story_creation_prompt(
            prompt=prompt,
            target_word_count=target_word_count,
            length_type=length_type,
            previous_context=previous_context
        )
        
        # Send messages to the LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        print(f"Storyteller Agent: Creating story for '{prompt}'...")
        response = self._invoke_with_fallback(messages)
        
        # Parse the response to extract title and story
        return self._parse_story_response(response.content)
    
    def refine_story(
        self,
        title: str,
        content: str,
        feedback: str,
        length_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Refine an existing story based on judge feedback
        
        Args:
            title: Current story title
            content: Current story content
            feedback: Feedback from the Judge Agent
            
        Returns:
            Dict with improved 'title' and 'content'
        """
        system_prompt = StorytellerPrompts.get_refinement_system_prompt()
        user_prompt = StorytellerPrompts.get_refinement_prompt(
            title=title,
            content=content,
            feedback=feedback,
            length_type=length_type
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        print(f"Storyteller Agent: Refining story based on feedback...")
        response = self._invoke_with_fallback(messages)
        
        return self._parse_story_response(response.content)
    
    def _parse_story_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse LLM response to extract title and story content
        
        The LLM responds in format:
        TITLE: [title]
        STORY: [content]
        
        This function extracts those parts using regex
        """
        title_match = re.search(r'TITLE:\s*(.+?)\n', response_text, re.IGNORECASE)
        story_match = re.search(r'STORY:\s*([\s\S]+)', response_text, re.IGNORECASE)
        
        title = title_match.group(1).strip() if title_match else "A Bedtime Story"
        content = story_match.group(1).strip() if story_match else response_text
        
        return {
            "title": title,
            "content": content
        }


class JudgeAgent:
    """
    The Judge Agent evaluates story quality and provides feedback
    
    This agent reviews stories on multiple dimensions:
    - Clarity: Is the language simple and clear?
    - Moral Value: Does it teach positive lessons?
    - Age Appropriateness: Is it suitable for 5-10 year-olds?
    """
    
    def __init__(self, groq_api_key: str, langsmith_api_key: Optional[str] = None):
        """
        Initialize the Judge Agent
        
        Args:
            groq_api_key: API key for Groq LLM service
            langsmith_api_key: Optional API key for LangSmith tracing
        """
        # Configure LangSmith if available
        if langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "bedtime-stories")
        
        self.groq_api_key = groq_api_key
        env_list = os.getenv("GROQ_MODEL_JUDGE") or os.getenv("GROQ_MODEL") or ""
        self.model_candidates = [m.strip() for m in env_list.split(",") if m.strip()] or [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]
        self.temperature = 0.3
        self.max_tokens = 300
        
        self.llm = ChatGroq(
            api_key=self.groq_api_key,
            model=self.model_candidates[0],  
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        self.current_model = self.model_candidates[0]
        
        print("Judge Agent initialized (Groq) with model fallback:", ", ".join(self.model_candidates))

    def _invoke_with_fallback(self, messages):
        """Invoke LLM with fallback and Opik tracking"""
        last_err = None
        for model in self.model_candidates:
            try:
                start_time = time.time()
                
                if model != self.current_model:
                    print(f"🔄 Judge switching to model: {model}")
                    self.llm = ChatGroq(
                        api_key=self.groq_api_key,
                        model=model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    self.current_model = model
                
                # Get Opik tracer for automatic LangChain integration
                opik_tracer = get_opik_tracer()
                config = {"callbacks": [opik_tracer]} if opik_tracer else {}
                
                # Invoke with Opik tracing
                response = self.llm.invoke(messages, config=config)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Log to Opik for performance tracking
                log_llm_call(
                    model_name=model,
                    prompt=str(messages),
                    completion=response.content,
                    latency_ms=latency_ms,
                    input_tokens=getattr(response, 'usage', {}).get('prompt_tokens'),
                    output_tokens=getattr(response, 'usage', {}).get('completion_tokens'),
                    metadata={
                        "agent": "judge",
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                
                return response
                
            except Exception as e:
                msg = str(e).lower()
                last_err = e
                print(f"⚠️ Judge model '{model}' failed: {e}")
                if ("rate limit" in msg) or ("429" in msg) or ("limit" in msg and "token" in msg) or ("decommission" in msg) or ("invalid" in msg):
                    print("↪️ Trying next Groq model due to rate limit or model issue...")
                    continue
                else:
                    break
        raise last_err if last_err else RuntimeError("All Groq models failed for judge")
    
    def evaluate_story(self, title: str, content: str) -> Dict:
        """
        Evaluate a story's quality across multiple dimensions
        
        Args:
            title: Story title
            content: Story content
            
        Returns:
            Dict containing scores and feedback:
            {
                'clarity': int (1-10),
                'moralValue': int (1-10),
                'ageAppropriateness': int (1-10),
                'score': int (1-10) overall,
                'approved': bool,
                'feedback': str
            }
        """
        system_prompt = JudgePrompts.get_system_prompt()
        user_prompt = JudgePrompts.get_evaluation_prompt(title=title, content=content)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        print(f"Judge Agent: Evaluating story '{title}'...")
        response = self._invoke_with_fallback(messages)
        
        # Parse the judge's response
        return self._parse_evaluation(response.content)
    
    def _parse_evaluation(self, response_text: str) -> Dict:
        """
        Parse judge's evaluation response
        
        Extracts numerical scores and feedback from the structured response
        """
        # Extract scores using regex
        clarity_match = re.search(r'CLARITY:\s*(\d+)', response_text, re.IGNORECASE)
        moral_match = re.search(r'MORAL:\s*(\d+)', response_text, re.IGNORECASE)
        age_match = re.search(r'AGE_APPROPRIATE:\s*(\d+)', response_text, re.IGNORECASE)
        overall_match = re.search(r'OVERALL:\s*(\d+)', response_text, re.IGNORECASE)
        approved_match = re.search(r'APPROVED:\s*(YES|NO)', response_text, re.IGNORECASE)
        feedback_match = re.search(r'FEEDBACK:\s*([\s\S]+)', response_text, re.IGNORECASE)
        
        # Parse scores (default to 7 if not found)
        clarity = int(clarity_match.group(1)) if clarity_match else 7
        moral = int(moral_match.group(1)) if moral_match else 7
        age_appropriate = int(age_match.group(1)) if age_match else 7
        overall = int(overall_match.group(1)) if overall_match else 7
        approved = approved_match.group(1).upper() == "YES" if approved_match else False
        feedback = feedback_match.group(1).strip() if feedback_match else "Story evaluated."
        
        return {
            "clarity": clarity,
            "moralValue": moral,
            "ageAppropriateness": age_appropriate,
            "score": overall,
            "approved": approved,
            "feedback": feedback
        }
