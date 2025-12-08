# CommitAnalyzer Output Evaluation Framework (Binary)

This document provides a structured framework for evaluating the output quality of the `CommitAnalyzer` node using **Binary (Pass/Fail)** criteria. This approach reduces ambiguity and aligns with modern LLM evaluation best practices.

---

## Evaluation Details

- **Commit SHA**: `[PASTE COMMIT SHA HERE]`
- **Repository**: `[PASTE REPOSITORY IDENTIFIER HERE]`
- **LangSmith Trace URL**: `[PASTE LANGSMITH TRACE URL HERE]`
- **Evaluator**: `[YOUR NAME]`
- **Date**: `[DATE OF EVALUATION]`

---

## 1. Core Categorization

### `change_type`

- **Output**: `[PASTE change_type HERE]`
- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: The type accurately represents the primary intent (e.g., 'feat' for new feature, 'fix' for bugfix).
  - **Fail**: The type is factually incorrect (e.g., labeling a feature as a bugfix).
- **Notes**:
  >

---

## 2. Content for Blog Generation

### `technical_summary`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: Accurate, captures the "what" and "how", and is technically sound.
  - **Fail**: Inaccurate, irrelevant, hallucinations, or just a copy-paste of the commit message.
- **Notes**:
  >

### `business_impact`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: Explicitly states **HOW** the change affects the end-user, performance, or business metrics.
  - **Fail**: Only describes code changes (e.g., "refactored X") without mentioning the user/business benefit.
- **Notes**:
  >

---

## 3. Structured Insights

### `key_changes`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: Lists all significant changes accurately.
  - **Fail**: Misses a major change or includes incorrect items.
- **Notes**:
  >

### `technical_details`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: Lists specific technologies, patterns, or implementation choices valuable to a developer.
  - **Fail**: Generic, irrelevant, or repeats information from other fields.
- **Notes**:
  >

### `affected_components`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: Identifies key affected modules/areas.
  - **Fail**: Lists completely wrong components or misses the primary affected area.
- **Notes**:
  >

---

## 4. Blog Narrative Structure

### `narrative_angle`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: A coherent, relevant angle that fits the commit content (e.g., "Problem-Solution").
  - **Fail**: Generic, uninspired, or totally irrelevant to the actual changes.
- **Notes**:
  >

---

## 5. Context Self-Assessment

### `context_assessment` & `context_assessment_details`

- **Result**: [ ] Pass / [ ] Fail
- **Criteria**:
  - **Pass**: The assessment (sufficient/insufficient) logically matches the provided context and analysis quality.
  - **Fail**: Claims 'sufficient' when major context is clearly missing, or vice versa.
- **Notes**:
  >

---

## Overall Verdict

- **Final Status**: [ ] **PASS** / [ ] **FAIL**
- **Key Failure Mode (if Fail)**:
  >
- **Action Items**: (e.g., "Tune prompt for business impact", "Fix hallucination in summary")
  >
