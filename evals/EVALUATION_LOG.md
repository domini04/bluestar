# BlueStar Evaluation System Development Log

This document tracks the development process, design decisions, and considerations for the BlueStar AI Agent evaluation system.

## Goals
1. Implement a robust evaluation system for LLM-generated outputs.
2. Document the methodology ("How we do evaluations").
3. Provide metrics for Content Quality, User Experience, System Performance, and Analysis Quality.

## Development Log

### [Date: Current] - Evaluation Script Design Considerations
- **Challenge 1: Human-in-the-Loop (HIL) Interaction**: 
  - The BlueStar app is designed to be interactive (CLI prompts for feedback).
  - Automated evaluation (bulk runs) cannot handle blocking user input.
  - **Decision**: We must bypass the Human Refinement Loop during evaluation.
    - Strategy: Configure the `AgentState` with `max_iterations=0` or `user_satisfied=True` initially to force the workflow to skip refinement and proceed directly to completion (or a simplified end state).
    - Requirement: The `human_refinement_node` implementation must check these state flags *before* attempting any I/O.

- **Challenge 2: Data Fetching Strategy**:
  - **Question**: Should we pre-fetch commit data into the dataset or fetch it live during evaluation?
  - **Decision**: Fetch **Live** during evaluation.
  - **Reasoning**:
    - Storing full diffs and file contents in LangSmith datasets creates bloat.
    - We want to test the *entire* pipeline (Fetcher -> Analyzer -> Synthesizer) to catch errors in context gathering.
    - The `commit_sha` and `repo_identifier` in the dataset are sufficient triggers for the `CommitFetcher` node.

- **Action Plan for `run_eval.py`**:
  1. Import the production graph (`create_graph`).
  2. Use a custom/mock config or state initialization that sets `max_iterations=0`.
  3. Ensure the `human_refinement` node logic supports non-interactive execution via state flags.
  4. Use `langsmith.evaluate` to orchestrate the run.

### [Date: Previous] - Dataset Creation
- Created `evals/create_dataset.py` to populate LangSmith with real commits.
- Used a hybrid approach: Local `git log` for the current repo and external repo mapping.
- Successfully created "BlueStar Evaluation Dataset" with 20 examples.

### [Date: Previous] - Initialization
- Created `evals/` directory structure.
- Initiated process to design evaluations based on `performance_metrics.md`.
- Focus: Transparency in the evaluation implementation process.
