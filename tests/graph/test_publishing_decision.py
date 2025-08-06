import pytest
from unittest.mock import patch

from bluestar.agents.state import AgentState
from bluestar.agents.nodes.publishing_decision import publishing_decision_node

@pytest.fixture
def satisfied_state_fixture() -> AgentState:
    """Provides an AgentState where the user is satisfied, ready for publishing decision."""
    return AgentState(
        repo_identifier="test/repo",
        commit_sha="test_sha",
        user_satisfied=True
    )

def test_publishing_decision_publish_to_ghost(satisfied_state_fixture):
    """Tests the user choosing to publish to Ghost."""
    # Arrange
    initial_state = satisfied_state_fixture
    
    # Act
    # Patch 'builtins.input' to simulate the user entering '1'.
    with patch('builtins.input', return_value='1'):
        final_state = publishing_decision_node(initial_state)
        
    # Assert
    assert final_state.publishing_decision == "ghost"

def test_publishing_decision_save_locally(satisfied_state_fixture):
    """Tests the user choosing to save the draft locally."""
    # Arrange
    initial_state = satisfied_state_fixture
    
    # Act
    with patch('builtins.input', return_value='2'):
        final_state = publishing_decision_node(initial_state)
        
    # Assert
    assert final_state.publishing_decision == "local"

def test_publishing_decision_discard(satisfied_state_fixture):
    """Tests the user choosing to discard the draft."""
    # Arrange
    initial_state = satisfied_state_fixture
    
    # Act
    with patch('builtins.input', return_value='3'):
        final_state = publishing_decision_node(initial_state)
        
    # Assert
    assert final_state.publishing_decision == "discard"

def test_publishing_decision_invalid_input_then_valid(satisfied_state_fixture):
    """Tests the node's ability to handle invalid input before a valid one."""
    # Arrange
    initial_state = satisfied_state_fixture
    
    # Act
    # Simulate the user entering 'invalid', then '2'.
    with patch('builtins.input', side_effect=['invalid', '2']):
        final_state = publishing_decision_node(initial_state)
        
    # Assert
    assert final_state.publishing_decision == "local"
