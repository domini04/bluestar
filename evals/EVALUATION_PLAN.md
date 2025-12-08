# BlueStar Evaluation Process Design(started Nov.24 2025)

This document outlines the planned evaluation process for BlueStar, moving from scalar scoring to binary (pass/fail) metrics and establishing a rigorous, data-driven evaluation workflow.

## 1. Core Philosophy Shift: Binary Metrics

We are moving away from subjective 1-5 scalar ratings to **Binary (Pass/Fail) Criteria**. This decision is supported by research highlighting the reliability issues with scalar scoring in LLM-as-a-Judge systems.

> **Reference**: Shankar et al. (2024), *"Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences"* ([arXiv:2404.12272](https://arxiv.org/abs/2404.12272)), argues that aligning binary/categorical criteria with human preference is more effective than complex scoring, reducing criteria drift and misalignment.

**Rationale**:
- **Clarity**: Eliminates ambiguity (e.g., "Is this a 3 or a 4?").
- **Actionability**: A "Fail" clearly indicates a specific criteria was not met, making it easier to fix.
- **Robustness**: Reduces noise in LLM-as-a-Judge evaluations.

### Example Transformation

| Metric | Old (Scalar 1-5) | New (Binary Pass/Fail) |
| :--- | :--- | :--- |
| **Business Impact** | Score 3: "Explains impact but vague." | **Pass**: Explicitly states *how* the change affects users or metrics.<br>**Fail**: Only describes code changes without mentioning user/business benefit. |
| **Technical Accuracy** | Score 4: "Mostly accurate." | **Pass**: Explanation matches the code changes without factual errors.<br>**Fail**: Contains at least one hallucination or technical inaccuracy. |

## 2. The 5-Step Evaluation Workflow

We will implement the following industry-standard process using **LangSmith**.

> **Reference**: This workflow is adapted from the *"Evaluation Process"* methodology discussed by LangChain/LangSmith team members (e.g., [Building Reliable Agents](https://www.youtube.com/watch?v=BsWxPI9UM4c)), emphasizing a cycle of manual review, categorization, and automated assertion.

### Step 1: Initial Data Analysis (Manual Review)
*   **Goal**: Understand actual failure modes from real traces.
*   **Action**:
    *   Review ~100 traces manually.
    *   **Open Coding**: Write specific, detailed notes on the *first* upstream error for each trace (e.g., "CommitFetcher missed README context", not just "bad output").
    *   **Owner**: Domain expert (Benevolent Dictator) owns the "taste" and consistency.
    *   **Saturation**: Continue until no new error types appear.

### Step 2: Categorization (Axial Coding)
*   **Goal**: Synthesize raw notes into actionable failure categories.
*   **Action**:
    *   **LLM Synthesis**: Use an LLM to cluster the open codes into "Axial Codes" (failure modes).
    *   **Refinement**: Manually review and refine categories to be specific (e.g., "Context Missing: File too large" vs "Context Error").
    *   **Quantification**: Count frequency to prioritize the "biggest problems".
    *   **Decision**: Decide which failures need automated evals vs. simple prompt fixes.

### Step 3: Automated Evaluation Implementation
*   **Goal**: Build functions to automatically score outputs (True/False).
*   **Types**:
    1.  **Code-based Assertions**: For objective criteria (JSON valid, max length, specific keywords). Cheap & fast.
    2.  **LLM-as-a-Judge**: For subjective criteria (Tone, Business Impact clarity). Tightly scoped, binary prompt.

### Step 4: Validate the Validators (Alignment)
*   **Goal**: Ensure automated metrics match human judgment.
*   **Action**:
    *   **Measure Agreement**: Compare LLM-Judge outputs vs. Human Ground Truth (from Step 1).
    *   **Confusion Matrix**: Analyze disagreements (False Positives vs. False Negatives).
    *   **Iterate**: Tune the Judge prompt until misalignment is minimized.

### Step 5: Iteration & Operationalization
*   **Goal**: Continuous improvement.
*   **Action**:
    *   **CI Integration**: Run aligned evals as unit tests.
    *   **Online Monitoring**: Track failure rates in production.
    *   **Improvement Flywheel**: Use eval data to drive agent/prompt updates.

## 3. Applicability to BlueStar

This process is **highly applicable** and recommended for BlueStar because:

1.  **Subjectivity of "Quality"**: Blog posts are creative outputs. Binary criteria (e.g., "Did it mention the business value?") anchor quality better than generic "Goodness" scores.
2.  **Complex Workflow**: BlueStar has multiple nodes (Fetcher -> Analyzer -> Synthesizer). Manual review (Step 1) is crucial to identify *where* the chain breaks (e.g., "Garbage in from Fetcher" vs "Hallucination in Analyzer").
3.  **LangGraph/LangSmith Integration**: The project already uses LangGraph and traces to LangSmith, making data collection for Step 1 immediate.
4.  **Cost Efficiency**: Moving to binary pass/fail allows for cheaper, smaller LLMs to act as judges for specific criteria compared to asking a large model to "rate everything out of 5".

## Next Steps
1.  Update `perfomance_metrics.md` to reflect the Binary Metric strategy.
2.  Prepare the **Dataset Creation Script** to fetch runs from LangSmith for Step 1.

