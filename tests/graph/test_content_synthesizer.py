"""
Integration Tests for ContentSynthesizer Node

Tests the ContentSynthesizer node with real CommitAnalysis data generated
from the preceding nodes in the BlueStar workflow.
"""
import pytest
from src.bluestar.agents.state import AgentState
from src.bluestar.agents.nodes import (
    input_validator_node,
    commit_fetcher_node,
    commit_analyzer_node,
    content_synthesizer_node,
)
from src.bluestar.core.tracing import setup_langsmith_tracing, get_tracing_info

from src.bluestar.formats.llm_outputs import BlogPostOutput, ContentBlock

@pytest.fixture(scope="module")
def analyzed_state_fixture() -> AgentState:
    """
    Pytest fixture that runs the initial part of the workflow to generate
    a real CommitAnalysis object. This provides realistic input for testing
    the ContentSynthesizer.
    """
    # Enable tracing for fixture setup
    setup_langsmith_tracing("bluestar-test-fixtures")

    # --- Test Data ---
    repo_identifier = "domini04/bluestar"
    commit_sha = "3a08718cfd5c22a392cd642843a3b5428fc8363d"
    
    # --- Run upstream nodes ---
    initial_state = AgentState(repo_identifier=repo_identifier, commit_sha=commit_sha)
    
    # 1. Input Validation
    validated_state = input_validator_node(initial_state)
    if validated_state.has_errors():
        pytest.fail(f"InputValidator failed in fixture setup: {validated_state.errors}")

    # 2. Commit Fetching (Real GitHub API call)
    fetched_state = commit_fetcher_node(validated_state)
    if fetched_state.has_errors():
        pytest.fail(f"CommitFetcher failed in fixture setup: {fetched_state.errors}")

    # 3. Commit Analysis (Real LLM call)
    analyzed_state = commit_analyzer_node(fetched_state)
    if analyzed_state.has_errors():
        pytest.fail(f"CommitAnalyzer failed in fixture setup: {analyzed_state.errors}")
        
    assert analyzed_state.commit_analysis is not None
    return analyzed_state


class TestContentSynthesizerIntegration:
    """Integration tests for the ContentSynthesizer node."""

    @pytest.fixture(autouse=True)
    def setup_tracing(self):
        """Set up LangSmith tracing for all tests in this class."""
        success = setup_langsmith_tracing("bluestar-synthesizer-tests")
        tracing_info = get_tracing_info()
        if not tracing_info["enabled"]:
            pytest.skip("LangSmith tracing not enabled for integration tests.")
        yield success

    def test_initial_generation_with_real_analysis(self, analyzed_state_fixture):
        """
        Tests the initial blog post generation using a real CommitAnalysis object.
        """
        # The fixture provides the state after the CommitAnalyzer has run
        state_with_analysis = analyzed_state_fixture
        
        print(f"\\n🧪 Running initial generation for commit {state_with_analysis.commit_sha[:7]}...")

        # Run the ContentSynthesizer node
        synthesized_state = content_synthesizer_node(state_with_analysis)

        # --- Verifications ---
        assert not synthesized_state.has_errors(), f"ContentSynthesizer failed: {synthesized_state.errors}"
        
        # Verify a structured blog post was created
        blog_post = synthesized_state.blog_post
        assert blog_post is not None, "Blog post should be generated."
        assert isinstance(blog_post, BlogPostOutput), "Blog post should be a BlogPostOutput object."

        # Verify the content of the structured blog post
        assert isinstance(blog_post.title, str) and len(blog_post.title) > 10
        assert isinstance(blog_post.summary, str) and len(blog_post.summary) > 20
        assert isinstance(blog_post.body, list) and len(blog_post.body) > 3
        
        # Check that the body contains valid ContentBlock objects
        for block in blog_post.body:
            assert isinstance(block, ContentBlock)

        # Verify state was updated correctly
        assert synthesized_state.synthesis_iteration_count == 1
        assert "content_synthesis_1" in synthesized_state.step_timestamps

        print("   ✅ Structured blog post generated successfully.")
        print(f"      - Title: {blog_post.title}")
        print(f"      - Summary: {blog_post.summary[:100].strip()}...")
        print(f"      - Body contains {len(blog_post.body)} content blocks.")
