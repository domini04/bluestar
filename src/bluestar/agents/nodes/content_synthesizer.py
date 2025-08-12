"""
ContentSynthesizer Node for BlueStar LangGraph Workflow

LLM-powered generation of blog posts from structured CommitAnalysis.
Supports both initial draft creation and iterative refinement based on user feedback.
"""
import logging
from typing import Dict, Any, List

from langchain.output_parsers import PydanticOutputParser
from pydantic import ValidationError

from ..state import AgentState
from ...core.llm import LLMClient
from ...core.exceptions import LLMError, ConfigurationError
from ...formats.llm_outputs import (
    BlogPostOutput,
    ContentBlock,
    ParagraphBlock,
    HeadingBlock,
    ListBlock,
    CodeBlock,
)
from ...prompts.initial_generation import initial_generation_prompt
from ...prompts.refinement_generation import refinement_generation_prompt
from ...utils.cli_progress import status
from ...utils.rendering import render_body_to_string

logger = logging.getLogger(__name__)


class ContentSynthesizerErrorHandler:
    """Helper utility for translating generation exceptions to user-friendly messages."""

    @staticmethod
    def get_user_message(exception: Exception, repo: str, commit_sha: str) -> str:
        """Translate technical exceptions to user-friendly error messages."""
        commit_short = commit_sha[:8]
        if isinstance(exception, ConfigurationError):
            return (
                f"LLM configuration error during content generation for commit {commit_short}. "
                f"Please check your LLM API key and configuration."
            )
        elif isinstance(exception, LLMError):
            if "rate limit" in str(exception).lower():
                return (
                    f"LLM API rate limit reached during content generation for commit {commit_short}. "
                    f"Please wait a few minutes and try again."
                )
            elif "timeout" in str(exception).lower():
                return (
                    f"LLM API request timed out during content generation for commit {commit_short}. "
                    f"Please try again."
                )
            else:
                return (
                    f"LLM API error during content generation for commit {commit_short}. "
                    f"This may be a temporary issue. Please try again."
                )
        elif isinstance(exception, ValidationError):
            return (
                f"LLM returned an invalid format for the blog post for commit {commit_short}. "
                f"This may indicate a temporary LLM issue. Please try again."
            )
        else:
            return (
                f"An unexpected error occurred during content generation for commit {commit_short}. "
                f"Please try again or contact support."
            )


def _extract_prompt_data(state: AgentState) -> Dict[str, Any]:
    """
    Extract and format data from AgentState for the appropriate prompt template.
    Handles both initial generation and refinement contexts.
    """
    commit_analysis = state.commit_analysis
    commit_data = state.commit_data

    # Common context available in both modes
    project_context = commit_data.project_structure or {}
    project_context_summary = (
        f"Repository: {state.repo_identifier}\\n"
        f"Description: {project_context.get('repository_metadata', {}).get('description', 'N/A')}\\n"
        f"README Summary: {project_context.get('readme_summary', 'N/A')}"
    )
    
    parser = PydanticOutputParser(pydantic_object=BlogPostOutput)
    format_instructions = parser.get_format_instructions()

    if state.user_feedback and state.blog_post:  # Refinement Mode
        logger.info("Assembling context for refinement generation.")
        previous_content_str = render_body_to_string(state.blog_post.body)
        return {
            "prompt": refinement_generation_prompt,
            "temperature": 0.2,
            "context": {
                "previous_title": state.blog_post.title,
                "previous_content": previous_content_str,
                "user_feedback": state.user_feedback,
                "tags": ", ".join(state.blog_post.tags),
                "change_type": commit_analysis.change_type,
                "technical_summary": commit_analysis.technical_summary,
                "business_impact": commit_analysis.business_impact,
                "key_changes": "\\n".join(f"- {c}" for c in commit_analysis.key_changes),
                "affected_components": ", ".join(commit_analysis.affected_components),
                "technical_details": "\\n".join(f"- {d}" for d in commit_analysis.technical_details),
                "narrative_angle": commit_analysis.narrative_angle,
                "project_context_summary": project_context_summary,
                "user_instructions": state.user_instructions or "No specific instructions provided.",
                "commit_author": commit_data.author,
                "commit_date": commit_data.date.isoformat(),
                "commit_message": commit_data.message,
                "format_instructions": format_instructions,
            },
        }
    else:  # Initial Generation Mode
        logger.info("Assembling context for initial blog post generation.")
        return {
            "prompt": initial_generation_prompt,
            "temperature": 0.7,
            "context": {
                "change_type": commit_analysis.change_type,
                "technical_summary": commit_analysis.technical_summary,
                "business_impact": commit_analysis.business_impact,
                "key_changes": "\\n".join(f"- {c}" for c in commit_analysis.key_changes),
                "affected_components": ", ".join(commit_analysis.affected_components),
                "technical_details": "\\n".join(f"- {d}" for d in commit_analysis.technical_details),
                "narrative_angle": commit_analysis.narrative_angle or "Direct technical explanation",
                "project_context_summary": project_context_summary,
                "user_instructions": state.user_instructions or "No specific instructions provided.",
                "commit_author": commit_data.author,
                "commit_date": commit_data.date.isoformat(),
                "commit_message": commit_data.message,
                "format_instructions": format_instructions,
            },
        }


def content_synthesizer_node(state: AgentState) -> AgentState:
    """
    ContentSynthesizer LangGraph node - LLM-powered blog post generation.
    """
    iteration = state.synthesis_iteration_count + 1
    logger.info(f"🔄 ContentSynthesizer: Generating blog post (iteration {iteration})...")

    # Prerequisite check
    if not state.commit_analysis or not state.commit_data:
        error_msg = "ContentSynthesizer requires commit analysis and data. Ensure previous nodes ran successfully."
        state.add_error(error_msg)
        logger.error(f"Missing commit_analysis or commit_data in state for {state.commit_sha}")
        state.mark_step_complete(f"content_synthesis_{iteration}")
        return state

    try:
        prompt_info = _extract_prompt_data(state)
        prompt = prompt_info["prompt"]
        temperature = prompt_info["temperature"]
        prompt_context = prompt_info["context"]

        # Build client using current (possibly overridden) config
        llm = LLMClient().get_client(temperature=temperature)
        parser = PydanticOutputParser(pydantic_object=BlogPostOutput)
        
        chain = prompt | llm | parser

        logger.debug("Executing LLM generation chain...")
        display_model = f"{LLMClient().provider}:{LLMClient().model}"
        with status(f"Generating draft (iteration {iteration}) with {display_model}..."):
            llm_output: BlogPostOutput = chain.invoke(prompt_context)

        # Update state with the new blog post
        state.blog_post = llm_output
        state.synthesis_iteration_count = iteration
        state.user_feedback = None  # Clear feedback after use

        logger.info(f"✅ ContentSynthesizer: Successfully generated blog post draft.")
        logger.debug(f"   Title: {state.blog_post.title}")

    except (ConfigurationError, LLMError, ValidationError) as e:
        user_msg = ContentSynthesizerErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.add_error(user_msg)
        logger.error(f"ContentSynthesizer error: {e}", exc_info=True)
    except Exception as e:
        user_msg = ContentSynthesizerErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.add_error(user_msg)
        logger.error(f"Unexpected error in ContentSynthesizer: {e}", exc_info=True)

    state.mark_step_complete(f"content_synthesis_{iteration}")
    return state
