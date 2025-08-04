"""
BlueStar LangGraph Agent State

Comprehensive state management for the blog generation workflow.
Tracks all data and control flow through the blog generation process,
from input collection to final publishing decision.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..formats.commit_data import CommitAnalysis, CommitData
from ..formats.blog_formats import GhostBlogPost
from ..formats.llm_outputs import BlogPostOutput


# TODO: Import when implemented
# from ..models.commit_analysis import CommitAnalysis
# from ..models.user_instructions import UserInstructions

# Forward references for planned models - safe for runtime
# These are design-time type hints that won't cause runtime errors


@dataclass
class AgentState:
    """
    Comprehensive state management for BlueStar LangGraph workflow.
    
    Tracks all data and control flow through the blog generation process,
    from input collection to final publishing decision.
    
    Design Principles:
    - Clean separation of input, processing, control, publishing, and metadata
    - Leverages LangGraph checkpointing for conversation history
    - Reuses existing BlueStar exception system for error handling
    - Minimal state size with separate metrics system
    - Natural language feedback with boolean satisfaction tracking
    """
    
    # ==================== INPUT DATA ====================
    # Structured input data - populated directly by interfaces
    repo_identifier: str                              # Repository identifier (owner/repo)
    commit_sha: str                                   # Commit SHA (40 characters)
    user_instructions: Optional[str] = None           # Optional user instructions as string
    
    # ==================== PROCESSING DATA ====================
    # Core workflow data transformation chain
    commit_data: Optional[CommitData] = None          # Structured commit info from GitHub API
    commit_analysis: Optional[CommitAnalysis] = None          # LLM analysis with categorization/insights
    blog_post: Optional[BlogPostOutput] = None         # Generated blog post in a structured, platform-agnostic format
    
    
    # ==================== HUMAN-IN-THE-LOOP CONTROL ====================
    # User interaction and satisfaction management
    max_iterations: int = 3                           # Maximum allowed improvement iterations
    synthesis_iteration_count: int = 0                # Number of iterations of the ContentSynthesizer
    user_satisfied: Optional[bool] = None             # Boolean satisfaction (feedback presence = dissatisfied)
    user_feedback: Optional[str] = None               # User feedback on the generated blog post  
    
    # ==================== CONTEXT & Context ENHANCEMENT CONTROL ====================
    # Context assessment and enhancement routing
    context_assessment: Optional[str] = None          # "sufficient", "needs_enhancement", "insufficient"
    context_assessment_details: Optional[str] = None  # Detailed explanation of context gaps
    needs_enhanced_context: bool = False              # Boolean flag for routing to ContextEnhancer
    
    # ==================== WORKFLOW CONTROL ====================
    # Workflow state and execution tracking
    current_step: str = "input_validation"            # Current workflow step identifier
    processing_complete: bool = False                 # Workflow completion flag
    errors: List[str] = field(default_factory=list)  # User-facing error messages
    
    # ==================== PUBLISHING CONTROL ====================
    # Blog publishing decision and results
    publish_to_blog: Optional[bool] = None            # User choice for publishing vs draft-only
    publication_result: Optional[Dict[str, Any]] = None  # Publishing operation results/metadata
    
    # ==================== METADATA ====================
    # Workflow tracking and performance monitoring
    workflow_id: str = field(default_factory=lambda: f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    start_time: datetime = field(default_factory=datetime.now)
    step_timestamps: Dict[str, datetime] = field(default_factory=dict)  # Step completion times
    
    def add_error(self, error_message: str) -> None:
        """
        Add user-facing error message to workflow state.
        
        Args:
            error_message: Clear, actionable error message for user
        """
        self.errors.append(error_message)
    
    def mark_step_complete(self, step_name: str) -> None:
        """
        Mark workflow step as complete with timestamp.
        
        Args:
            step_name: Name of the completed step
        """
        self.step_timestamps[step_name] = datetime.now()
        self.current_step = step_name
    

    
    def get_workflow_duration(self) -> float:
        """
        Calculate total workflow duration in seconds.
        
        Returns:
            Duration in seconds from start_time to now
        """
        return (datetime.now() - self.start_time).total_seconds()
    
    def is_processing_complete(self) -> bool:
        """
        Check if workflow processing is complete.
        
        Returns:
            True if processing is complete, False otherwise
        """
        return self.processing_complete
    
    def has_errors(self) -> bool:
        """
        Check if workflow has encountered errors.
        
        Returns:
            True if errors exist, False otherwise
        """
        return len(self.errors) > 0
    
    def get_current_iteration_count(self) -> int:
        """
        Get current iteration count by examining step timestamps.
        
        Returns:
            Number of content synthesis iterations completed
        """
        synthesis_count = sum(1 for step in self.step_timestamps.keys() 
                            if step.startswith("content_synthesis"))
        return synthesis_count
    
    def can_iterate(self) -> bool:
        """
        Check if workflow can perform another iteration.
        
        Returns:
            True if under max_iterations limit, False otherwise
        """
        return self.get_current_iteration_count() < self.max_iterations
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"AgentState(workflow_id={self.workflow_id}, "
                f"current_step={self.current_step}, "
                f"processing_complete={self.processing_complete}, "
                f"errors={len(self.errors)}, "
                f"user_satisfied={self.user_satisfied})") 