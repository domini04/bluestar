"""
CommitAnalyzer Node for BlueStar LangGraph Workflow

LLM-powered analysis of Git commits with project context for blog generation.
Produces structured CommitAnalysis for use by ContentSynthesizer.
"""

import logging
from typing import Dict, Any, Optional
from langchain.output_parsers import PydanticOutputParser
from pydantic import ValidationError

from ..state import AgentState
from ...core.llm import LLMClient
from ...core.exceptions import LLMError, ConfigurationError
from ...prompts import create_commit_analysis_prompt
from ...formats.commit_data import CommitAnalysis 
from ...utils.cli_progress import status

logger = logging.getLogger(__name__)


class CommitAnalyzerErrorHandler:
    """Helper utility for translating analysis exceptions to user-friendly messages."""
    
    @staticmethod
    def get_user_message(exception: Exception, repo: str, commit_sha: str) -> str:
        """
        Translate technical exceptions to user-friendly error messages.
        
        Args:
            exception: The caught exception
            repo: Repository identifier for context
            commit_sha: Commit SHA for context
            
        Returns:
            User-friendly error message with actionable guidance
        """
        commit_short = commit_sha[:8] if len(commit_sha) >= 8 else commit_sha
        
        if isinstance(exception, ConfigurationError):
            return (
                f"LLM configuration error while analyzing commit {commit_short}.... "
                f"Please check your LLM API key and configuration."
            )
        
        elif isinstance(exception, LLMError):
            if "rate limit" in str(exception).lower():
                return (
                    f"LLM API rate limit reached while analyzing commit {commit_short}.... "
                    f"Please wait a few minutes and try again."
                )
            elif "timeout" in str(exception).lower():
                return (
                    f"LLM API request timed out while analyzing commit {commit_short}.... "
                    f"Please try again. If the problem persists, the service may be experiencing issues."
                )
            else:
                return (
                    f"LLM API error while analyzing commit {commit_short}.... "
                    f"This may be a temporary issue. Please try again in a few moments."
                )
        
        elif isinstance(exception, ValidationError):
            return (
                f"LLM returned invalid analysis format for commit {commit_short}.... "
                f"This may indicate a temporary LLM issue. Please try again."
            )
        
        else:
            return (
                f"Unexpected error while analyzing commit {commit_short}.... "
                f"Please try again or contact support if the issue persists."
            )


def _extract_prompt_data(state: AgentState) -> Dict[str, Any]:
    """
    Extract and format data from AgentState for prompt template.
    
    Args:
        state: AgentState with commit_data populated
        
    Returns:
        Dictionary with formatted data for prompt template
    """
    commit_data = state.commit_data
    project_context = commit_data.project_structure or {}
    
    # Format files changed as readable list
    files_changed = "\n".join(f"  • {file}" for file in commit_data.files_changed) if commit_data.files_changed else "No files listed"
    
    # Combine all diff content from all files (token management)
    if commit_data.diffs:
        all_diffs = []
        total_length = 0
        for diff in commit_data.diffs:
            # Add file header for clarity
            file_header = f"\n--- File: {diff.file_path} ({diff.change_type}) ---\n"
            diff_section = file_header + diff.diff_content
            
            # Check if adding this diff would exceed our token limit
            if total_length + len(diff_section) > 50000:
                all_diffs.append("\n... [remaining diffs truncated for brevity]")
                break
            
            all_diffs.append(diff_section)
            total_length += len(diff_section)
        
        diff_content = "\n".join(all_diffs)
    else:
        diff_content = "No diff available"
    
    # Extract project context components
    repository_metadata = project_context.get("repository_metadata", {})
    readme_summary = project_context.get("readme_summary", "No README available")
    primary_config = project_context.get("primary_config") # Keep as None if not found
    project_type = project_context.get("project_type", "unknown")
    
    # Format metadata as readable text
    repo_meta_text = f"Description: {repository_metadata.get('description', 'None')}, Language: {repository_metadata.get('language', 'Unknown')}, Topics: {repository_metadata.get('topics', [])}"
    
    if primary_config:
        config_text = f"File: {primary_config.get('file_name', 'None')}, Type: {primary_config.get('project_type', 'unknown')}"
    else:
        config_text = "No primary configuration file found."
        
    # Generate format instructions for prompt template
    from langchain.output_parsers import PydanticOutputParser
    from ...formats.commit_data import CommitAnalysis
    parser = PydanticOutputParser(pydantic_object=CommitAnalysis)
    format_instructions = parser.get_format_instructions()
    
    return {
        "repo_identifier": state.repo_identifier,
        "commit_message": commit_data.message,
        "commit_author": commit_data.author,
        "commit_date": commit_data.date.isoformat() if commit_data.date else "Unknown",
        "files_changed": files_changed,
        "diff_content": diff_content,
        "repository_metadata": repo_meta_text,
        "readme_summary": readme_summary,
        "primary_config": config_text,
        "project_type": project_type,
        "user_instructions": state.user_instructions or "No specific instructions provided",
        "format_instructions": format_instructions
    }


def commit_analyzer_node(state: AgentState) -> AgentState:
    """
    CommitAnalyzer LangGraph node - LLM-powered commit analysis.
    
    Analyzes commit data with project context to generate structured insights
    for blog post generation. Includes context completeness assessment for
    progressive enhancement routing.
    
    Args:
        state: AgentState with validated commit_data from CommitFetcher
        
    Returns:
        Updated AgentState with commit_analysis populated and context assessment
        
    Note: Requires commit_data to be populated by CommitFetcher node.
    """
    logger.info(f"🔄 CommitAnalyzer: Analyzing commit {state.commit_sha[:8]}... with LLM")
    
    # Validate prerequisites
    if not state.commit_data:
        error_msg = "CommitAnalyzer requires commit data from CommitFetcher. Please ensure CommitFetcher completed successfully."
        state.add_error(error_msg)
        logger.error(f"Missing commit_data in state for {state.commit_sha}")
        state.mark_step_complete("commit_analysis")
        return state
    
    try:
        # Initialize LLM client with analysis-appropriate settings
        logger.debug("Initializing LLM client for commit analysis")
        llm = LLMClient().get_client(
            temperature=0.3,      # Conservative for factual analysis
            max_tokens=4096,      # Reduced from 200k to prevent duplication/run-on
            timeout=60            # 1 minute timeout as requested
        )
        
        # Create prompt and parser
        prompt = create_commit_analysis_prompt()
        parser = PydanticOutputParser(pydantic_object=CommitAnalysis)
        
        # Extract and format data for prompt
        logger.debug("Extracting commit data and project context for analysis")
        prompt_data = _extract_prompt_data(state)
        
        # Log context availability
        has_project_context = bool(state.commit_data.project_structure)
        logger.info(f"📊 Analyzing with {'enhanced' if has_project_context else 'basic'} project context")
        
        # Create and execute the analysis chain
        logger.debug("Executing LLM analysis chain: prompt | llm | parser")
        chain = prompt | llm | parser

        # Show CLI status while running the long LLM call
        display_model = f"{LLMClient().provider}:{LLMClient().model}"
        with status(f"Analyzing commit {state.commit_sha[:8]} with {display_model}..."):
            analysis: CommitAnalysis = chain.invoke(prompt_data)
        
        # Store analysis results in state
        state.commit_analysis = analysis
        
        # Store context assessment in state for other nodes
        state.context_assessment = analysis.context_assessment
        state.context_assessment_details = analysis.context_assessment_details
        state.needs_enhanced_context = analysis.needs_enhanced_context()
        
        # Log analysis results
        logger.info(f"✅ CommitAnalyzer: Analysis complete for {state.commit_sha[:8]}...")
        logger.info(f"📋 Change type: {analysis.change_type}")
        logger.info(f"📊 Context assessment: {analysis.context_assessment}")
        
        if analysis.context_assessment_details:
            logger.debug(f"📝 Context details: {analysis.context_assessment_details}")
        
        if state.needs_enhanced_context:
            logger.info("🔍 Enhanced context recommended for quality improvement")
        
        logger.debug(f"💡 Key changes: {len(analysis.key_changes)} items")
        logger.debug(f"🔧 Technical details: {len(analysis.technical_details)} items")
        logger.debug(f"📦 Affected components: {len(analysis.affected_components)} items")
        
    except (ConfigurationError, LLMError) as e:
        # Handle known LLM-related exceptions
        user_msg = CommitAnalyzerErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.add_error(user_msg)
        
        # Log technical details for debugging
        logger.error(f"CommitAnalyzer LLM error: {e}", exc_info=True)
        logger.debug(f"Error context: repo={state.repo_identifier}, sha={state.commit_sha}")
        
    except ValidationError as e:
        # Handle Pydantic validation errors (malformed LLM output)
        user_msg = CommitAnalyzerErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.add_error(user_msg)
        
        # Log validation details for debugging
        logger.error(f"CommitAnalyzer validation error: {e}", exc_info=True)
        logger.debug(f"LLM output failed validation for {state.commit_sha}")
        
    except Exception as e:
        # Handle unexpected errors
        user_msg = CommitAnalyzerErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.add_error(user_msg)
        
        # Log unexpected error with full context
        logger.error(
            f"Unexpected error in CommitAnalyzer: {e}",
            exc_info=True,
            extra={
                'repo_identifier': state.repo_identifier,
                'commit_sha': state.commit_sha,
                'workflow_id': state.workflow_id,
                'has_commit_data': bool(state.commit_data),
                'has_project_context': bool(state.commit_data.project_structure if state.commit_data else False)
            }
        )
    
    # Mark step complete regardless of success/failure
    state.mark_step_complete("commit_analysis")
    
    return state 