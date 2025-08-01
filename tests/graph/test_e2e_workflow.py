"""
End-to-End (E2E) Workflow Tests for BlueStar

Tests the sequential execution of multiple nodes in the LangGraph workflow
using real, external APIs (GitHub, LLMs) to verify the pipeline's integrity.
"""

import pytest
from src.bluestar.agents.state import AgentState
from src.bluestar.agents.nodes import (
    input_validator_node,
    commit_fetcher_node,
    commit_analyzer_node
)
from src.bluestar.core.tracing import setup_langsmith_tracing, get_tracing_info

class TestE2EWorkflow:
    """End-to-end tests for the core analysis pipeline."""

    @pytest.fixture(autouse=True)
    def setup_tracing(self):
        """Set up LangSmith tracing for E2E tests."""
        success = setup_langsmith_tracing("bluestar-e2e-tests")
        tracing_info = get_tracing_info()
        if not tracing_info["enabled"]:
            pytest.skip("LangSmith tracing not enabled for E2E tests.")
        yield success

    def test_e2e_validation_to_analysis_real_commit(self):
        """
        Tests the workflow from InputValidator -> CommitFetcher -> CommitAnalyzer.
        
        This test uses a real GitHub commit and a real LLM call to verify the
        entire initial analysis pipeline.
        """
        # --- Test Data ---
        repo_identifier = "domini04/bluestar"
        commit_sha = "bcb5db9d771acd0f222a76714a96b6992ba86a16"
        
        # 1. --- Initialization ---
        initial_state = AgentState(
            repo_identifier=repo_identifier,
            commit_sha=commit_sha,
            user_instructions="Analyze this documentation and tooling update for a blog post."
        )
        print(f"🚀 Starting E2E test for {repo_identifier}/commit/{commit_sha[:7]}")

        # 2. --- Input Validation ---
        print("\n[Step 1/3] 🕵️  Running InputValidator...")
        validated_state = input_validator_node(initial_state)
        
        assert not validated_state.has_errors(), f"InputValidator failed: {validated_state.errors}"
        assert validated_state.repo_identifier == repo_identifier
        assert validated_state.commit_sha == commit_sha.lower()
        print("   ✅ Input validation successful.")

        # 3. --- Commit Fetching ---
        print("\n[Step 2/3] ☁️  Running CommitFetcher (real GitHub API call)...")
        fetched_state = commit_fetcher_node(validated_state)
        
        assert not fetched_state.has_errors(), f"CommitFetcher failed: {fetched_state.errors}"
        assert fetched_state.commit_data is not None, "CommitData should be populated."
        assert fetched_state.commit_data.sha == commit_sha
        assert len(fetched_state.commit_data.files_changed) > 0
        print(f"   ✅ Commit data fetched successfully for {len(fetched_state.commit_data.files_changed)} files.")

        # 4. --- Commit Analysis ---
        print("\n[Step 3/3] 🧠  Running CommitAnalyzer (real LLM API call)...")
        analyzed_state = commit_analyzer_node(fetched_state)

        assert not analyzed_state.has_errors(), f"CommitAnalyzer failed: {analyzed_state.errors}"
        assert analyzed_state.commit_analysis is not None, "CommitAnalysis should be generated."
        
        analysis = analyzed_state.commit_analysis
        print(f"   ✅ Commit analysis generated successfully.")
        print(f"      - Change Type: {analysis.change_type}")
        print(f"      - Narrative Angle: {analysis.narrative_angle}")
        print(f"      - Context Assessment: {analysis.context_assessment}")

        # --- Final Verification ---
        assert analysis.change_type
        assert len(analysis.technical_summary) > 20
        assert len(analysis.business_impact) > 20
        assert len(analysis.key_changes) > 0
        
        print("\n🎉 E2E test completed successfully!")
        print("📈 Check LangSmith dashboard under 'bluestar-e2e-tests' project for detailed traces.")

