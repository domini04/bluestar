"""
BlueStar Exception Classes

Custom exception hierarchy for BlueStar application errors.
These complement LangChain's existing exceptions rather than duplicate them.
"""


class BlueStarError(Exception):
    """Base exception for all BlueStar-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# Configuration Errors
class ConfigurationError(BlueStarError):
    """Configuration-related errors (missing API keys, invalid providers, etc.)."""
    pass


class InvalidProviderError(ConfigurationError):
    """Unsupported or misconfigured LLM provider."""
    
    def __init__(self, provider: str, available_providers: list = None):
        available = f" Available providers: {available_providers}" if available_providers else ""
        super().__init__(
            f"Unsupported LLM provider: '{provider}'.{available}",
            {"provider": provider, "available_providers": available_providers}
        )


# Workflow Errors
class WorkflowError(BlueStarError):
    """LangGraph workflow execution errors."""
    pass


class ContentGenerationError(WorkflowError):
    """Failed to generate blog content."""
    pass


class CommitAnalysisError(WorkflowError):
    """Failed to analyze commit data."""
    pass


# LLM Integration Errors
class LLMError(BlueStarError):
    """BlueStar-specific LLM errors (wraps LangChain exceptions)."""
    
    def __init__(self, message: str, original_error: Exception = None, details: dict = None):
        super().__init__(message, details)
        self.original_error = original_error
    
    @classmethod
    def from_langchain_error(cls, langchain_error: Exception, context: str = ""):
        """Create BlueStar LLM error from LangChain exception."""
        message = f"LLM error{f' during {context}' if context else ''}: {str(langchain_error)}"
        return cls(message, original_error=langchain_error)


class ContextLengthError(LLMError):
    """Content too long for model context window."""
    
    def __init__(self, content_length: int, max_length: int):
        super().__init__(
            f"Content length ({content_length}) exceeds model limit ({max_length})",
            details={"content_length": content_length, "max_length": max_length}
        )


class QualityThresholdError(LLMError):
    """Generated content didn't meet quality standards."""
    
    def __init__(self, quality_score: float, threshold: float):
        super().__init__(
            f"Content quality score ({quality_score}) below threshold ({threshold})",
            details={"quality_score": quality_score, "threshold": threshold}
        )


# Data Errors
class DataError(BlueStarError):
    """Data processing and validation errors."""
    pass


class InvalidCommitError(DataError):
    """Invalid commit SHA or inaccessible commit."""
    
    def __init__(self, commit_sha: str, repo_path: str = None):
        message = f"Invalid or inaccessible commit: {commit_sha}"
        if repo_path:
            message += f" in repository: {repo_path}"
        super().__init__(message, {"commit_sha": commit_sha, "repo_path": repo_path})


class RepositoryError(DataError):
    """Repository access or validation errors."""
    
    def __init__(self, repo_path: str, reason: str = ""):
        message = f"Repository error: {repo_path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"repo_path": repo_path, "reason": reason}) 