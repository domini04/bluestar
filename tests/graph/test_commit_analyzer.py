"""
Unit Tests for CommitAnalyzer Node

Comprehensive high-priority tests focusing on core logic, data processing, and error handling.
All LLM interactions are mocked to ensure fast, reliable, isolated testing.

Test Coverage:
- Core node functionality with various success/error scenarios
- Different project types (Python, JavaScript, Java)
- Different analysis types (feature, bugfix, security, refactor)
- Prompt data integration and validation
- Edge cases (empty commits, missing data)
- Error handling for all exception types
- State management and context assessment
"""

import os
import sys
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from bluestar.agents.state import AgentState
from bluestar.agents.nodes.commit_analyzer import (
    commit_analyzer_node, 
    _extract_prompt_data,
    CommitAnalyzerErrorHandler
)
from bluestar.formats.commit_data import CommitData, DiffData, CommitAnalysis
from bluestar.core.exceptions import ConfigurationError, LLMError


class TestCommitAnalyzerNode:
    """Test the main commit_analyzer_node function."""
    
    def create_test_commit_data(self, with_project_context=True, project_type="python"):
        """Helper to create test commit data for different project types."""
        # Create different file paths and content based on project type
        project_configs = {
            "python": {
                "file_path": "src/auth/login.py",
                "diff_content": "+ def authenticate_user(username, password):\n-     return True",
                "files_changed": ["src/auth/login.py", "tests/test_auth.py"],
                "config_file": "pyproject.toml",
                "language": "Python",
                "topics": ["authentication", "web-app"]
            },
            "javascript": {
                "file_path": "src/components/Auth.jsx",
                "diff_content": "+ const authenticateUser = (username, password) => {\n-   return true;",
                "files_changed": ["src/components/Auth.jsx", "src/utils/auth.js"],
                "config_file": "package.json",
                "language": "JavaScript",
                "topics": ["react", "frontend", "authentication"]
            },
            "java": {
                "file_path": "src/main/java/com/example/AuthService.java",
                "diff_content": "+ public boolean authenticateUser(String username, String password) {\n-     return true;",
                "files_changed": ["src/main/java/com/example/AuthService.java", "src/test/java/AuthTest.java"],
                "config_file": "pom.xml",
                "language": "Java",
                "topics": ["spring", "backend", "security"]
            }
        }
        
        config = project_configs.get(project_type, project_configs["python"])
        
        diff_data = DiffData(
            file_path=config["file_path"],
            change_type="modified",
            additions=10,
            deletions=3,
            diff_content=config["diff_content"]
        )
        
        project_structure = {
            "repository_metadata": {
                "description": f"A test {project_type} repository",
                "language": config["language"],
                "topics": config["topics"]
            },
            "readme_summary": f"This is a test {project_type} authentication system",
            "primary_config": {
                "file_name": config["config_file"],
                "project_type": project_type
            },
            "project_type": project_type
        } if with_project_context else None
        
        return CommitData(
            sha="a1b2c3d4e5f6789012345678901234567890abcd",
            message="Add user authentication with JWT tokens",
            author="John Doe",
            author_email="john@example.com",
            date=datetime(2025, 1, 20, 10, 30, 0),
            branch="feature/auth",
            files_changed=config["files_changed"],
            total_additions=15,
            total_deletions=5,
            diffs=[diff_data],
            repository_path="/path/to/repo",
            tags=["v1.2.0"],
            project_structure=project_structure
        )
    
    def create_test_analysis(self, change_type="feature", context_assessment="sufficient"):
        """Helper to create test analysis result for different change types."""
        analysis_configs = {
            "feature": {
                "technical_summary": "Added JWT-based authentication system with secure token generation",
                "business_impact": "Users can now securely log in and access protected features",
                "key_changes": ["Added JWT authentication middleware", "Created login/logout endpoints"],
                "technical_details": ["Used PyJWT library", "Implemented bcrypt for password hashing"],
                "affected_components": ["authentication module", "user routes"],
                "narrative_angle": "Problem-solution approach focusing on security improvements"
            },
            "bugfix": {
                "technical_summary": "Fixed memory leak in authentication token cleanup process",
                "business_impact": "Improved application stability and reduced server resource usage",
                "key_changes": ["Fixed token cleanup memory leak", "Added proper session disposal"],
                "technical_details": ["Added explicit garbage collection", "Implemented proper dispose pattern"],
                "affected_components": ["session management", "memory allocator"],
                "narrative_angle": "Technical problem diagnosis and resolution"
            },
            "security": {
                "technical_summary": "Patched SQL injection vulnerability in user authentication queries",
                "business_impact": "Eliminated critical security risk protecting user data from attacks",
                "key_changes": ["Implemented parameterized queries", "Added input sanitization"],
                "technical_details": ["Used prepared statements", "Added SQL injection tests"],
                "affected_components": ["database layer", "authentication queries"],
                "narrative_angle": "Security vulnerability mitigation and best practices"
            },
            "refactor": {
                "technical_summary": "Restructured authentication module for better maintainability",
                "business_impact": "Improved code quality enabling faster future development",
                "key_changes": ["Extracted auth service class", "Simplified login flow"],
                "technical_details": ["Applied SOLID principles", "Reduced cyclomatic complexity"],
                "affected_components": ["authentication module", "service layer"],
                "narrative_angle": "Code quality improvement and technical debt reduction"
            }
        }
        
        config = analysis_configs.get(change_type, analysis_configs["feature"])
        
        return CommitAnalysis(
            change_type=change_type,
            technical_summary=config["technical_summary"],
            business_impact=config["business_impact"],
            key_changes=config["key_changes"],
            technical_details=config["technical_details"],
            affected_components=config["affected_components"],
            narrative_angle=config["narrative_angle"],
            context_assessment=context_assessment,
            context_assessment_details=None if context_assessment == "sufficient" else "Missing additional context for comprehensive analysis"
        )
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_success(self, mock_prompt, mock_llm_client):
        """Test successful commit analysis with complete data."""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        # Mock the chain execution
        mock_analysis = self.create_test_analysis()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        # Setup chain creation (prompt | llm | parser)
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Create a simple approach: mock the entire chain creation process  
            # by intercepting the actual chain execution
            def mock_chain_creation(*args, **kwargs):
                return mock_chain
            
            # Patch the prompt to return something that creates our mock chain
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            # Create test state
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                user_instructions="Focus on security features"
            )
            state.commit_data = self.create_test_commit_data()
            
            # Execute
            result_state = commit_analyzer_node(state)
            
            # Verify LLM client was configured correctly
            mock_llm_client.get_client.assert_called_once_with(
                temperature=0.3,
                max_tokens=200000,
                timeout=60
            )
            
            # Verify prompt was created
            mock_prompt.assert_called_once()
            
            # Verify chain was invoked
            mock_chain.invoke.assert_called_once()
            
            # Verify results stored in state
            assert result_state.commit_analysis == mock_analysis
            assert result_state.context_assessment == "sufficient"
            assert result_state.context_assessment_details is None
            assert result_state.needs_enhanced_context is False
            assert "commit_analysis" in result_state.step_timestamps
            assert len(result_state.errors) == 0
    
    def test_commit_analyzer_node_missing_commit_data(self):
        """Test error handling when commit_data is missing."""
        state = AgentState(
            repo_identifier="test/repo",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
        )
        # Don't set commit_data
        
        result_state = commit_analyzer_node(state)
        
        # Verify error handling
        assert len(result_state.errors) == 1
        assert "CommitAnalyzer requires commit data from CommitFetcher" in result_state.errors[0]
        assert result_state.commit_analysis is None
        assert "commit_analysis" in result_state.step_timestamps
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_stores_context_assessment(self, mock_prompt, mock_llm_client):
        """Test that context assessment is properly stored in state."""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        # Create analysis with needs_enhancement context
        mock_analysis = self.create_test_analysis()
        mock_analysis.context_assessment = "needs_enhancement"
        mock_analysis.context_assessment_details = "Missing database schema context"
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo", 
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify context assessment is stored
            assert result_state.context_assessment == "needs_enhancement"
            assert result_state.context_assessment_details == "Missing database schema context"
            assert result_state.needs_enhanced_context is True
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    def test_commit_analyzer_node_configuration_error(self, mock_llm_client):
        """Test handling of LLM configuration errors."""
        # Setup LLM client to raise ConfigurationError
        mock_llm_client.get_client.side_effect = ConfigurationError("Invalid API key")
        
        state = AgentState(
            repo_identifier="test/repo",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
        )
        state.commit_data = self.create_test_commit_data()
        
        result_state = commit_analyzer_node(state)
        
        # Verify error handling
        assert len(result_state.errors) == 1
        assert "LLM configuration error while analyzing commit a1b2c3d4" in result_state.errors[0]
        assert "Please check your LLM API key" in result_state.errors[0]
        assert result_state.commit_analysis is None
        assert "commit_analysis" in result_state.step_timestamps
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_llm_error(self, mock_prompt, mock_llm_client):
        """Test handling of LLM API errors."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        # Setup chain to raise LLMError
        mock_chain = Mock()
        mock_chain.invoke.side_effect = LLMError("Rate limit exceeded")
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify error handling
            assert len(result_state.errors) == 1
            assert "LLM API rate limit reached while analyzing commit a1b2c3d4" in result_state.errors[0]
            assert "Please wait a few minutes" in result_state.errors[0]
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_validation_error(self, mock_prompt, mock_llm_client):
        """Test handling of Pydantic validation errors."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        # Setup chain to raise ValidationError
        mock_chain = Mock()
        mock_chain.invoke.side_effect = ValidationError.from_exception_data(
            "CommitAnalysis", [{"type": "missing", "loc": ("change_type",), "msg": "Field required"}]
        )
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify error handling
            assert len(result_state.errors) == 1
            assert "LLM returned invalid analysis format" in result_state.errors[0]
            assert "temporary LLM issue" in result_state.errors[0]
    
    # ==================== DIFFERENT PROJECT TYPES TESTS ====================
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_javascript_project(self, mock_prompt, mock_llm_client):
        """Test analysis with JavaScript project context."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/react-app",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data(project_type="javascript")
            
            result_state = commit_analyzer_node(state)
            
            # Verify successful analysis with JavaScript context
            assert result_state.commit_analysis == mock_analysis
            assert len(result_state.errors) == 0
            
            # Verify prompt was called with JavaScript project data
            prompt_call_args = mock_chain.invoke.call_args[0][0]
            assert prompt_call_args["project_type"] == "javascript"
            assert "package.json" in prompt_call_args["primary_config"]
            assert "Language: JavaScript" in prompt_call_args["repository_metadata"]
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_java_project(self, mock_prompt, mock_llm_client):
        """Test analysis with Java project context."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/spring-app",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data(project_type="java")
            
            result_state = commit_analyzer_node(state)
            
            # Verify successful analysis with Java context
            assert result_state.commit_analysis == mock_analysis
            assert len(result_state.errors) == 0
            
            # Verify prompt was called with Java project data
            prompt_call_args = mock_chain.invoke.call_args[0][0]
            assert prompt_call_args["project_type"] == "java"
            assert "pom.xml" in prompt_call_args["primary_config"]
            assert "Language: Java" in prompt_call_args["repository_metadata"]
    
    # ==================== DIFFERENT ANALYSIS TYPES TESTS ====================
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_bugfix_analysis(self, mock_prompt, mock_llm_client):
        """Test analysis of bugfix commit type."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis(change_type="bugfix")
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify bugfix analysis
            assert result_state.commit_analysis.change_type == "bugfix"
            assert "memory leak" in result_state.commit_analysis.technical_summary
            assert "stability" in result_state.commit_analysis.business_impact
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_security_analysis(self, mock_prompt, mock_llm_client):
        """Test analysis of security commit type."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis(change_type="security")
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify security analysis
            assert result_state.commit_analysis.change_type == "security"
            assert "SQL injection" in result_state.commit_analysis.technical_summary
            assert "security risk" in result_state.commit_analysis.business_impact
    
    # ==================== PROMPT INTEGRATION TESTS ====================
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_prompt_data_injection(self, mock_prompt, mock_llm_client):
        """Test that prompt receives properly formatted data from _extract_prompt_data."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="abc123def456789012345678901234567890abcd",
                user_instructions="Focus on performance aspects"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify chain.invoke was called with correct data structure
            assert mock_chain.invoke.called
            prompt_data = mock_chain.invoke.call_args[0][0]
            
            # Verify all required fields are present
            required_fields = [
                "repo_identifier", "commit_message", "commit_author", "commit_date",
                "files_changed", "diff_content", "repository_metadata", "readme_summary",
                "primary_config", "project_type", "user_instructions"
            ]
            for field in required_fields:
                assert field in prompt_data, f"Missing required field: {field}"
            
            # Verify specific data injection
            assert prompt_data["repo_identifier"] == "test/repo"
            assert prompt_data["user_instructions"] == "Focus on performance aspects"
            assert "pyproject.toml" in prompt_data["primary_config"]
    
    # ==================== EDGE COMMIT TESTS ====================
    
    def create_empty_commit_data(self):
        """Helper to create empty commit data (edge case)."""
        return CommitData(
            sha="empty123456789012345678901234567890abcd",
            message="Empty commit for CI trigger",
            author="CI Bot",
            author_email="ci@example.com",
            date=datetime(2025, 1, 20, 10, 30, 0),
            files_changed=[],  # No files changed
            total_additions=0,
            total_deletions=0,
            diffs=[],  # No diffs
            repository_path="/path/to/repo",
            project_structure=None  # No project context
        )
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_node_empty_commit(self, mock_prompt, mock_llm_client):
        """Test analysis of empty commit (no files changed)."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis(change_type="other")
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser.return_value = Mock()
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="empty123456789012345678901234567890abcd"
            )
            state.commit_data = self.create_empty_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify successful handling of empty commit
            assert result_state.commit_analysis == mock_analysis
            assert len(result_state.errors) == 0
            
            # Verify prompt data handles empty commit gracefully
            prompt_data = mock_chain.invoke.call_args[0][0]
            assert prompt_data["files_changed"] == "No files listed"
            assert prompt_data["diff_content"] == "No diff available"
    
    # ==================== PARSER VALIDATION TESTS ====================
    
    @patch('bluestar.agents.nodes.commit_analyzer.llm_client')
    @patch('bluestar.agents.nodes.commit_analyzer.create_commit_analysis_prompt')
    def test_commit_analyzer_parser_configuration(self, mock_prompt, mock_llm_client):
        """Test that Pydantic parser is configured correctly with CommitAnalysis model."""
        mock_llm = Mock()
        mock_llm_client.get_client.return_value = mock_llm
        mock_prompt.return_value = Mock()
        
        mock_analysis = self.create_test_analysis()
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_analysis
        
        with patch('bluestar.agents.nodes.commit_analyzer.PydanticOutputParser') as mock_parser:
            mock_parser_instance = Mock()
            mock_parser.return_value = mock_parser_instance
            
            # Mock the chain creation process
            mock_prompt_obj = Mock()
            mock_prompt_obj.__or__ = Mock(return_value=Mock(__or__=Mock(return_value=mock_chain)))
            mock_prompt.return_value = mock_prompt_obj
            
            state = AgentState(
                repo_identifier="test/repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
            )
            state.commit_data = self.create_test_commit_data()
            
            result_state = commit_analyzer_node(state)
            
            # Verify parser was configured with CommitAnalysis model
            mock_parser.assert_called_once_with(pydantic_object=CommitAnalysis)
            
            # Verify successful completion
            assert result_state.commit_analysis == mock_analysis
            assert len(result_state.errors) == 0


class TestExtractPromptData:
    """Test the _extract_prompt_data helper function."""
    
    def create_test_state_with_commit_data(self, with_project_context=True):
        """Helper to create test state with commit data."""
        diff_data = DiffData(
            file_path="src/main.py",
            change_type="modified",
            additions=5,
            deletions=2,
            diff_content="+ print('Hello World')\n- print('Hello')"
        )
        
        project_structure = {
            "repository_metadata": {
                "description": "Test repository",
                "language": "Python",
                "topics": ["web", "api"]
            },
            "readme_summary": "A simple test application",
            "primary_config": {
                "file_name": "setup.py",
                "project_type": "python"
            },
            "project_type": "python"
        } if with_project_context else None
        
        commit_data = CommitData(
            sha="abc123def456",
            message="Update greeting message",
            author="Jane Smith",
            author_email="jane@example.com",
            date=datetime(2025, 1, 15, 14, 30, 0),
            files_changed=["src/main.py", "README.md"],
            total_additions=10,
            total_deletions=5,
            diffs=[diff_data],
            repository_path="/test/repo",
            project_structure=project_structure
        )
        
        state = AgentState(
            repo_identifier="test/example",
            commit_sha="abc123def456",
            user_instructions="Make it more friendly"
        )
        state.commit_data = commit_data
        
        return state
    
    def test_extract_prompt_data_complete(self):
        """Test prompt data extraction with complete data."""
        state = self.create_test_state_with_commit_data(with_project_context=True)
        
        result = _extract_prompt_data(state)
        
        # Verify all fields are present
        assert result["repo_identifier"] == "test/example"
        assert result["commit_message"] == "Update greeting message"
        assert result["commit_author"] == "Jane Smith"
        assert result["commit_date"] == "2025-01-15T14:30:00"
        assert "src/main.py" in result["files_changed"]
        assert "README.md" in result["files_changed"]
        assert "print('Hello World')" in result["diff_content"]
        assert "Description: Test repository" in result["repository_metadata"]
        assert "Language: Python" in result["repository_metadata"]
        assert result["readme_summary"] == "A simple test application"
        assert "File: setup.py" in result["primary_config"]
        assert result["project_type"] == "python"
        assert result["user_instructions"] == "Make it more friendly"
    
    def test_extract_prompt_data_minimal(self):
        """Test prompt data extraction with minimal data."""
        state = self.create_test_state_with_commit_data(with_project_context=False)
        
        result = _extract_prompt_data(state)
        
        # Verify minimal data handling
        assert result["repo_identifier"] == "test/example"
        assert result["commit_message"] == "Update greeting message"
        assert result["repository_metadata"] == "Description: None, Language: Unknown, Topics: []"
        assert result["readme_summary"] == "No README available"
        assert result["primary_config"] == "File: None, Type: unknown"
        assert result["project_type"] == "unknown"
    
    def test_extract_prompt_data_truncates_large_diffs(self):
        """Test that large diffs are truncated appropriately."""
        state = self.create_test_state_with_commit_data()
        
        # Create a large diff
        large_diff = "+" + "x" * 25000  # Larger than 20k limit
        state.commit_data.diffs[0].diff_content = large_diff
        
        result = _extract_prompt_data(state)
        
        # Verify truncation
        assert len(result["diff_content"]) <= 20050  # 20k + truncation message
        assert "[diff truncated for brevity]" in result["diff_content"]
    
    def test_extract_prompt_data_missing_project_context(self):
        """Test handling when project_structure is None."""
        state = self.create_test_state_with_commit_data()
        state.commit_data.project_structure = None
        
        result = _extract_prompt_data(state)
        
        # Verify defaults for missing context
        assert "Description: None" in result["repository_metadata"]
        assert result["readme_summary"] == "No README available"
        assert "File: None" in result["primary_config"]
        assert result["project_type"] == "unknown"
    
    def test_extract_prompt_data_no_files_changed(self):
        """Test handling when no files are listed."""
        state = self.create_test_state_with_commit_data()
        state.commit_data.files_changed = []
        
        result = _extract_prompt_data(state)
        
        assert result["files_changed"] == "No files listed"
    
    def test_extract_prompt_data_no_diffs(self):
        """Test handling when no diffs are available."""
        state = self.create_test_state_with_commit_data()
        state.commit_data.diffs = []
        
        result = _extract_prompt_data(state)
        
        assert result["diff_content"] == "No diff available"
    
    def test_extract_prompt_data_no_user_instructions(self):
        """Test handling when user instructions are None."""
        state = self.create_test_state_with_commit_data()
        state.user_instructions = None
        
        result = _extract_prompt_data(state)
        
        assert result["user_instructions"] == "No specific instructions provided"


class TestCommitAnalyzerErrorHandler:
    """Test the CommitAnalyzerErrorHandler utility class."""
    
    def test_error_handler_configuration_error(self):
        """Test handling of configuration errors."""
        error = ConfigurationError("Invalid API key")
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "a1b2c3d4e5f6789012345678901234567890abcd"
        )
        
        assert "LLM configuration error while analyzing commit a1b2c3d4" in message
        assert "Please check your LLM API key and configuration" in message
    
    def test_error_handler_llm_rate_limit(self):
        """Test handling of LLM rate limit errors."""
        error = LLMError("Rate limit exceeded for API")
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "abc123def456"
        )
        
        assert "LLM API rate limit reached while analyzing commit abc123de" in message
        assert "Please wait a few minutes and try again" in message
    
    def test_error_handler_llm_timeout(self):
        """Test handling of LLM timeout errors."""
        error = LLMError("Request timeout after 60 seconds")
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "xyz789abc123"
        )
        
        assert "LLM API request timed out while analyzing commit xyz789ab" in message
        assert "Please try again" in message
        assert "service may be experiencing issues" in message
    
    def test_error_handler_llm_generic_error(self):
        """Test handling of generic LLM errors."""
        error = LLMError("Service unavailable")
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "def456ghi789"
        )
        
        assert "LLM API error while analyzing commit def456gh" in message
        assert "temporary issue" in message
        assert "Please try again in a few moments" in message
    
    def test_error_handler_validation_error(self):
        """Test handling of Pydantic validation errors."""
        error = ValidationError.from_exception_data(
            "CommitAnalysis", [{"type": "missing", "loc": ("change_type",), "msg": "Field required"}]
        )
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "ghi789jkl012"
        )
        
        assert "LLM returned invalid analysis format for commit ghi789jk" in message
        assert "temporary LLM issue" in message
        assert "Please try again" in message
    
    def test_error_handler_generic_error(self):
        """Test handling of unexpected errors."""
        error = Exception("Unexpected system error")
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "jkl012mno345"
        )
        
        assert "Unexpected error while analyzing commit jkl012mn" in message
        assert "Please try again or contact support" in message
    
    def test_error_handler_short_commit_sha(self):
        """Test handling when commit SHA is shorter than 8 characters."""
        error = ConfigurationError("Test error")
        
        message = CommitAnalyzerErrorHandler.get_user_message(
            error, "test/repo", "abc123"
        )
        
        assert "commit abc123" in message  # Should use full short SHA


if __name__ == "__main__":
    pytest.main([__file__]) 