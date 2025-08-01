# CommitAnalyzer Output Evaluation Framework

This document provides a structured framework for evaluating the output quality of the `CommitAnalyzer` node. Use this template to review LangSmith traces for specific commits and provide consistent, actionable feedback.

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
- **Accuracy Score**: (1-3)
  - **1 (Incorrect)**: The type is completely wrong (e.g., labeled 'bugfix' for a new feature).
  - **2 (Partially Correct)**: The type is plausible but not the best fit (e.g., 'refactor' for a performance optimization).
  - **3 (Correct)**: The type accurately represents the primary intent of the commit.
- **Notes**:
  >

---

## 2. Content for Blog Generation

### `technical_summary`

- **Quality Score**: (1-5)
  - **1 (Poor)**: Inaccurate, irrelevant, or just a copy of the commit message.
  - **2 (Needs Improvement)**: Vague, misses key technical details, or is hard to understand.
  - **3 (Average)**: Accurate but lacks depth. A good starting point but needs significant editing.
  - **4 (Good)**: Mostly accurate and detailed. Captures the "what" and "how" effectively.
  - **5 (Excellent)**: Clear, concise, and technically deep. Perfectly explains the change for a developer audience.
- **Notes**:
  >

### `business_impact`

- **Quality Score**: (1-5)
  - **1 (Poor)**: Missing, irrelevant, or fails to explain user/business value.
  - **2 (Needs Improvement)**: Vague connection to business value; generic statements.
  - **3 (Average)**: Explains the impact, but could be more compelling or specific.
  - **4 (Good)**: Clearly articulates the "why" for non-technical stakeholders.
  - **5 (Excellent)**: Provides a compelling, clear, and specific explanation of the business value and user benefits.
- **Notes**:
  >

---

## 3. Structured Insights

### `key_changes`

- **Accuracy & Completeness Score**: (1-5)
  - **1 (Poor)**: Completely misses the key changes or lists incorrect items.
  - **2 (Needs Improvement)**: Lists some changes but misses major ones or includes minor, irrelevant details.
  - **3 (Average)**: Captures most of the high-level changes but may lack precision.
  - **4 (Good)**: Accurately lists all significant changes.
  - **5 (Excellent)**: Lists all significant changes with concise and precise descriptions.
- **Notes**:
  >

### `technical_details`

- **Usefulness Score**: (1-5)
  - **1 (Poor)**: Irrelevant, incorrect, or generic details.
  - **2 (Needs Improvement)**: Too high-level or repeats information from other fields.
  - **3 (Average)**: Provides some useful technical keywords or concepts.
  - **4 (Good)**: Lists specific technologies, patterns, or implementation choices that a developer would find valuable.
  - **5 (Excellent)**: Highlights non-obvious technical decisions and provides deep insight into the implementation.
- **Notes**:
  >

### `affected_components`

- **Accuracy Score**: (1-3)
  - **1 (Incorrect)**: Lists wrong components or misses all key affected areas.
  - **2 (Partially Correct)**: Identifies some, but not all, affected components.
  - **3 (Correct)**: Accurately and comprehensively lists all affected modules/areas.
- **Notes**:
  >

---

## 4. Blog Narrative Structure

### `narrative_angle`

- **Quality Score**: (1-3)
  - **1 (Poor)**: Generic, uninspired, or doesn't fit the commit content.
  - **2 (Average)**: A plausible but standard narrative (e.g., "Problem-Solution").
  - **3 (Excellent)**: A creative, compelling, and highly relevant angle that would make for an interesting blog post.
- **Notes**:
  >

---

## 5. Context Self-Assessment

### `context_assessment` & `context_assessment_details`

- **Accuracy Score**: (1-3)
  - **1 (Incorrect)**: The assessment is wrong (e.g., claims 'sufficient' when major context is clearly missing).
  - **2 (Partially Correct)**: The assessment is reasonable, but the details are vague or not actionable.
  - **3 (Correct)**: The assessment is accurate, and the details (if any) are specific and actionable.
- **Notes**:
  >

---

## Overall Summary & Action Items

- **Overall Quality Score**: (1-5)
- **Key Strengths**:
  >
- **Areas for Improvement**:
  >
- **Action Items**: (e.g., "Tune prompt to improve `business_impact`", "Add file content of related modules to context")
  >
