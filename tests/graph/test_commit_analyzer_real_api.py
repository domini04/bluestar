"""
Real API Integration Tests for CommitAnalyzer

Tests CommitAnalyzer with actual LLM calls and LangSmith tracing.
Uses real LangChain chains but structured test data.
"""

import pytest
import os
from datetime import datetime
from unittest.mock import patch

from src.bluestar.agents.nodes.commit_analyzer import commit_analyzer_node
from src.bluestar.agents.state import AgentState
from src.bluestar.formats.commit_data import CommitData, CommitAnalysis, DiffData
from src.bluestar.core.tracing import setup_langsmith_tracing, get_tracing_info


class TestRealAPIIntegration:
    """Integration tests using real LLM API calls with LangSmith tracing."""
    
    @pytest.fixture(autouse=True)
    def setup_tracing(self):
        """Set up LangSmith tracing for integration tests."""
        # Enable tracing for this test session
        success = setup_langsmith_tracing("bluestar-integration-tests")
        
        # Verify tracing is working
        tracing_info = get_tracing_info()
        if not tracing_info["enabled"]:
            pytest.skip("LangSmith tracing not enabled - set LANGSMITH_TRACING=true and LANGSMITH_API_KEY")
        
        yield success
    
    def create_test_commit_data(self, commit_type="feature", complexity="simple"):
        """Create structured test commit data for different scenarios."""
        
        if complexity == "simple":
            diff_data = DiffData(
                file_path="src/utils/helper.py",
                change_type="modified",
                additions=15,
                deletions=3,
                diff_content="+ def new_helper_function():\n+     return 'hello world'\n- # TODO: implement this"
            )
            files_changed = ["src/utils/helper.py"]
            message = "feat: add simple helper function"
            
        elif complexity == "complex":
            diff_data = DiffData(
                file_path="src/auth/jwt_middleware.py",
                change_type="added",
                additions=120,
                deletions=0,
                diff_content="""+ import jwt
+ from functools import wraps
+ from flask import request, jsonify, current_app
+ 
+ def token_required(f):
+     @wraps(f)
+     def decorated(*args, **kwargs):
+         token = request.headers.get('Authorization')
+         if not token:
+             return jsonify({'message': 'Token is missing!'}), 401
+         try:
+             data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
+         except:
+             return jsonify({'message': 'Token is invalid!'}), 401
+         return f(*args, **kwargs)
+     return decorated"""
            )
            files_changed = ["src/auth/jwt_middleware.py", "src/auth/__init__.py", "tests/test_auth.py"]
            message = "feat: implement JWT authentication middleware with token validation"
            
        return CommitData(
            sha=f"test_{commit_type}_{complexity}_123abc",
            message=message,
            author="Test Developer",
            author_email="test@example.com",
            date=datetime.now(),
            files_changed=files_changed,
            total_additions=diff_data.additions,
            total_deletions=diff_data.deletions,
            diffs=[diff_data],
            repository_path="/test/repo"
        )
    
    def test_simple_feature_commit_real_llm(self):
        """Test CommitAnalyzer with a simple feature commit using real LLM."""
        
        # Create test data
        test_commit = self.create_test_commit_data("feature", "simple")
        test_state = AgentState(
            repo_identifier="test/integration-repo",
            commit_sha=test_commit.sha,
            commit_data=test_commit
        )
        
        # Execute CommitAnalyzer with real LLM call
        result_state = commit_analyzer_node(test_state)
        
        # Verify analysis was generated
        assert result_state.commit_analysis is not None, "CommitAnalysis should be generated"
        analysis = result_state.commit_analysis
        
        # Verify required fields are present
        assert analysis.change_type in ["feature", "bugfix", "refactor", "performance", "security", "documentation", "other"]
        assert len(analysis.technical_summary) > 10, "Technical summary should be meaningful"
        assert len(analysis.business_impact) > 10, "Business impact should be meaningful"
        assert len(analysis.key_changes) > 0, "Should have at least one key change"
        assert len(analysis.technical_details) > 0, "Should have technical details"
        assert len(analysis.affected_components) > 0, "Should identify affected components"
        assert analysis.context_assessment in ["sufficient", "needs_enhancement", "insufficient"]
        
        # Verify specific content makes sense for a helper function
        assert "helper" in analysis.technical_summary.lower() or "function" in analysis.technical_summary.lower()
        
        print(f"✅ Real LLM Analysis Generated:")
        print(f"   Change Type: {analysis.change_type}")
        print(f"   Technical Summary: {analysis.technical_summary[:100]}...")
        print(f"   Business Impact: {analysis.business_impact[:100]}...")
        print(f"   Context Assessment: {analysis.context_assessment}")
        print(f"📈 LangSmith traces: Check dashboard for 'bluestar-integration-tests' project")
    
    def test_complex_auth_commit_real_llm(self):
        """Test CommitAnalyzer with a complex authentication commit using real LLM."""
        
        # Create complex test data
        test_commit = self.create_test_commit_data("feature", "complex")
        test_state = AgentState(
            repo_identifier="test/auth-repo",
            commit_sha=test_commit.sha,
            commit_data=test_commit,
            user_instructions="Focus on security implications and implementation details"
        )
        
        # Execute CommitAnalyzer with real LLM call
        result_state = commit_analyzer_node(test_state)
        
        # Verify analysis was generated
        assert result_state.commit_analysis is not None
        analysis = result_state.commit_analysis
        
        # Verify quality of analysis for complex commit
        assert len(analysis.technical_summary) > 50, "Complex commit should have detailed technical summary"
        assert len(analysis.key_changes) >= 2, "Complex commit should have multiple key changes"
        assert len(analysis.technical_details) >= 2, "Should have multiple technical details"
        
        # Verify auth-specific content
        auth_keywords = ["auth", "token", "jwt", "security", "middleware"]
        technical_text = analysis.technical_summary.lower()
        assert any(keyword in technical_text for keyword in auth_keywords), "Should mention authentication concepts"
        
        # Verify user instructions were considered
        if test_state.user_instructions:
            # Check if the analysis reflects the user's focus on security
            security_keywords = ["security", "secure", "protection", "validation"]
            business_text = analysis.business_impact.lower()
            assert any(keyword in business_text for keyword in security_keywords), "Should address security focus"
        
        print(f"✅ Complex Auth Analysis Generated:")
        print(f"   Change Type: {analysis.change_type}")
        print(f"   Key Changes: {len(analysis.key_changes)} items")
        print(f"   Technical Details: {len(analysis.technical_details)} items")
        print(f"   Affected Components: {analysis.affected_components}")
    
    def test_state_updates_with_real_analysis(self):
        """Test that AgentState is properly updated with real LLM analysis."""
        
        test_commit = self.create_test_commit_data("feature", "simple")
        test_state = AgentState(
            repo_identifier="test/state-repo",
            commit_sha=test_commit.sha,
            commit_data=test_commit
        )
        
        # Track initial state
        initial_step_count = len(test_state.step_timestamps)
        
        # Execute node
        result_state = commit_analyzer_node(test_state)
        
        # Verify state updates
        assert result_state.commit_analysis is not None
        assert len(result_state.step_timestamps) > initial_step_count, "Should add step timestamp"
        assert "commit_analysis" in result_state.step_timestamps, "Should record commit_analysis step"
        
        # Verify original data preserved
        assert result_state.repo_identifier == test_state.repo_identifier
        assert result_state.commit_sha == test_state.commit_sha
        assert result_state.commit_data == test_state.commit_data
    

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No LLM API key configured"
    )
    def test_api_error_handling_real_failures(self):
        """Test error handling with potential real API failures."""
        
        # Create test data
        test_commit = self.create_test_commit_data("feature", "simple")
        test_state = AgentState(
            repo_identifier="test/error-repo",
            commit_sha=test_commit.sha,
            commit_data=test_commit
        )
        
        # This test should handle real API errors gracefully
        try:
            result_state = commit_analyzer_node(test_state)
            
            # If successful, verify analysis
            if result_state.commit_analysis is not None:
                print("✅ API call successful, analysis generated")
                assert isinstance(result_state.commit_analysis, CommitAnalysis)
            else:
                # If failed, should have error handling
                print("⚠️  API call failed, checking error handling")
                assert result_state.errors is not None, "Should capture errors"
                assert len(result_state.errors) > 0, "Should have error details"
                
        except Exception as e:
            # Should not raise unhandled exceptions
            pytest.fail(f"CommitAnalyzer should handle API errors gracefully: {e}")


 