# BlueStar GUI Implementation Plan

This document outlines the plan for developing a simple, interactive Graphical User Interface (GUI) for the BlueStar application.

---

## 1. Framework Selection

The first step was to choose an appropriate Python-based framework for the GUI. The goal is to create a simple, maintainable UI without requiring a major overhaul of the existing application or introducing non-Python technologies like JavaScript.

### Frameworks Considered

Several options were evaluated based on the project's specific needs:

1.  **Django:**
    *   **Analysis:** A powerful, "batteries-included" framework for large, complex web applications.
    *   **Conclusion:** Considered significant overkill for this project. Its complexity (ORM, migrations, etc.) is unnecessary for building a simple UI for a local tool.

2.  **FastAPI:**
    *   **Analysis:** A modern, high-performance framework for building APIs. It is not a UI framework itself and would require a separate frontend application (e.g., React, Vue.js) to build the GUI.
    *   **Conclusion:** While powerful, this approach would dramatically increase complexity by splitting the project into a separate backend and frontend, which is contrary to the goal of a simple GUI.

3.  **Gradio:**
    *   **Analysis:** A framework designed for creating simple UIs for machine learning models. It excels at wrapping a Python function in a web interface.
    *   **Conclusion:** A very strong contender. It is simple, pure Python, and has relevant built-in components.

4.  **Streamlit:**
    *   **Analysis:** A framework for turning Python scripts into interactive web applications. It offers a rich set of UI components, a straightforward state management system (`session_state`), and flexible layout options.
    *   **Conclusion:** A very strong contender, similar to Gradio in its suitability for the project.

### Recommendation: Streamlit

The recommended framework is **Streamlit**.

While both Streamlit and Gradio are excellent fits, Streamlit holds a slight edge for this project for the following reasons:

1.  **Best Fit for the Task:** Streamlit is purpose-built for turning scripts and tools into interactive applications. Its development model aligns perfectly with the goal of creating a simple GUI layer on top of existing logic.
2.  **Component Alignment:** Its built-in components (`st.text_input`, `st.button`, `st.markdown`, `st.spinner`) map directly to every interactive step required by the BlueStar agent.
3.  **Superior State Management:** Streamlit's `st.session_state` is a simple and robust mechanism for managing the state of the LangGraph agent across multiple user interactions. This is critical for the multi-step refinement and publishing loops.
4.  **Flexible Layouts:** It provides easy-to-use layout primitives like sidebars and columns, which will help in creating a clean, organized, and user-friendly interface.

---

## 2. Implementation Blueprint

This blueprint details the architecture and plan for implementing the Streamlit GUI.

### Guiding Principles

*   **Separation of Concerns:** The GUI code will be kept separate from the core agent logic. The Streamlit app will act as a "client" to the BlueStar agent.
*   **Minimize Core Changes:** The existing LangGraph agent and its nodes will not be modified. The GUI will be built as a layer on top.
*   **Leverage Existing Structures:** The `AgentState` and Pydantic models are central to the application and will be used to manage the UI's state.

### Proposed Architecture & Structure

*   **New File: `app.py`**
    *   A new file, `app.py`, will be created at the project root.
    *   This file will contain all Streamlit UI code and will be the entry point for the GUI (`streamlit run app.py`).
    *   It will import the necessary components, such as the agent graph and state objects, from the `src/bluestar/` directory.

### GUI and Agent Interaction Model

The Streamlit app will manage the execution of the LangGraph agent:

1.  **State Management:** The `AgentState` object will be stored in Streamlit's `st.session_state` to persist it across user interactions.
2.  **Controlled Execution:** The app will run the agent step-by-step, listening for when the graph pauses at a human interaction point (as defined by the existing nodes).
3.  **Dynamic UI Updates:** When the agent pauses, the UI will update to show the relevant information and input widgets (e.g., show the draft and a feedback form).
4.  **Resuming Execution:** User input from the UI will be used to update the `AgentState`, and the app will then resume the agent's execution from where it left off.

### New Components Required

1.  **`app.py` (The GUI Entry Point):**
    *   Will define the application layout, including a title, sidebar for inputs, and a main content area.
    *   Will contain the logic for orchestrating the agent's execution based on user interaction.

2.  **UI Layout (within `app.py`):**
    *   **Input Sidebar:** To contain the initial inputs (Repository URL, Commit SHA, Optional Instructions) and the "Generate" button.
    *   **Main Content Area:** A dynamic area to display the current output from the agent, such as the blog post draft, refinement feedback form, or publishing options.
    *   **Status Log:** A dedicated area to display real-time status updates to the user (e.g., "Fetching commit...", "Analyzing changes...").

3.  **New Rendering Utility:**
    *   A new function will be created in `src/bluestar/utils/rendering.py` to convert the `BlogPostOutput` Pydantic model into a Markdown string, suitable for display using `st.markdown`.

### Required Changes to Existing Application

*   **Core Logic:** **No changes** will be made to the core agent logic or LangGraph nodes.
*   **Dependencies:** `streamlit` will be added to `pyproject.toml` as an optional dependency.

### User Interaction Flow (Blueprint Summary)

1.  The user launches the app with `streamlit run app.py`.
2.  The UI appears with input fields in the sidebar.
3.  The user provides the repository and commit, then clicks **"Generate"**.
4.  A spinner appears. The app initializes the `AgentState`, saves it to `st.session_state`, and starts the agent. Progress is shown in the status log.
5.  The agent runs until it reaches the `HumanRefinementNode` and pauses.
6.  The UI updates to show the generated draft and a feedback form.
7.  The user submits feedback (or leaves it blank if satisfied).
8.  The app updates the `AgentState` and resumes the agent. The agent regenerates the content and pauses again, updating the UI with the new draft.
9.  This loop continues until the user is satisfied.
10. The agent proceeds to the `PublishingDecisionNode` and pauses.
11. The UI updates to show the final publishing buttons.
12. The user makes a choice, the agent executes the final step, and the workflow completes.
