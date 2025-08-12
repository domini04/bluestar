from typing import Literal

from ..state import AgentState

def publishing_decision_node(state: AgentState) -> AgentState:
    """
    Asks the user for their final decision on the approved blog post and
    updates the state with their choice.
    """
    if not state.user_satisfied:
        # This node should only be reached after the user has approved the draft.
        # This is a safeguard against incorrect graph routing.
        state.add_error("PublishingDecisionNode: Cannot proceed without user satisfaction.")
        return state

    print("\nThe draft has been approved.")
    
    menu = (
        "\nWhat would you like to do next?\n\n"
        "[1] Publish to Ghost\n"
        "[2] Save draft locally and exit\n"
        "[3] Discard and exit\n"
    )
    
    while True:
        print(menu)
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            state.publishing_decision = "ghost"
            print("✅ Decision recorded: Publish to Ghost.")
            break
        elif choice == '2':
            state.publishing_decision = "local"
            print("✅ Decision recorded: Save locally.")
            break
        elif choice == '3':
            state.publishing_decision = "discard"
            print("✅ Decision recorded: Discard draft.")
            break
        else:
            print("\n❌ Invalid choice. Please enter a number from 1 to 3.")

    state.mark_step_complete("publishing_decision")
    return state
