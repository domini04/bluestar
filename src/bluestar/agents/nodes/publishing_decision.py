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

    # If a publishing decision was preselected (e.g., via CLI flag), respect it and skip the menu.
    if state.publishing_decision in {"ghost", "notion", "local", "discard"}:
        print(f"✅ Decision already set: {state.publishing_decision}.")
        state.mark_step_complete("publishing_decision")
        return state

    print("\nThe draft has been approved.")
    
    menu = (
        "\nWhat would you like to do next?\n\n"
        "[1] Publish to Ghost\n"
        "[2] Publish to Notion\n"
        "[3] Save draft locally and exit\n"
        "[4] Discard and exit\n"
    )
    
    while True:
        print(menu)
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == '1':
            state.publishing_decision = "ghost"
            print("✅ Decision recorded: Publish to Ghost.")
            break
        elif choice == '2':
            state.publishing_decision = "notion"
            print("✅ Decision recorded: Publish to Notion.")
            break
        elif choice == '3':
            state.publishing_decision = "local"
            print("✅ Decision recorded: Save locally.")
            break
        elif choice == '4':
            state.publishing_decision = "discard"
            print("✅ Decision recorded: Discard draft.")
            break
        else:
            print("\n❌ Invalid choice. Please enter a number from 1 to 4.")

    state.mark_step_complete("publishing_decision")
    return state
