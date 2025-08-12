"""
Prompt templates for the ContentSynthesizer node: Refinement Generation.
"""
from langchain_core.prompts import ChatPromptTemplate

# -------------------- REFINEMENT GENERATION PROMPT --------------------

# This prompt is designed for the second and subsequent passes of content
# generation. Its primary goal is surgical editing, not creative writing.
# It instructs the LLM to act as a precise editor, applying user feedback
# to an existing draft while preserving all other content. It will be paired
# with a low temperature to ensure deterministic, feedback-driven changes.

refinement_generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """# ================== ROLE DEFINITION ==================
You are a precise and helpful editor. Your job is to improve a draft of a technical blog post by perfectly implementing specific user feedback.

# ================== CORE PRINCIPLES (MUST FOLLOW) ==================
1.  **BE A SURGICAL EDITOR**: Your only goal is to implement the changes requested in the `User Feedback`.
2.  **PRESERVE THE ORIGINAL DRAFT**: This is your most important instruction. **DO NOT** change any part of the `Previous Draft` that the feedback does not address. Your job is to revise, not to rewrite from scratch.
3.  **MAINTAIN THE FULL STRUCTURE**: You MUST return a complete JSON object with all original fields (`title`, `author`, `date`, `tags`, `summary`, `body`). Do not omit any fields, even if they were not changed.
4.  **USE ORIGINAL ANALYSIS FOR REFERENCE ONLY**: The `Original Commit Analysis` is provided only as a reference document. You should only consult it if you need to clarify a technical detail to fulfill the user's request. Your primary inputs are the `Previous Draft` and the `User Feedback`.

# ================== YOUR TASK ==================
Revise the `Previous Draft` below according to the `User Feedback`. After applying the changes, return the **complete and updated** blog post as a raw JSON object that conforms to the following schema.

{format_instructions}
""",
        ),
        (
            "human",
            """# ================== DOCUMENTS FOR REVISION ==================

### 1. The Previous Draft to Revise:
- **Title**: {previous_title}
- **Author**: {commit_author}
- **Date**: {commit_date}
- **Tags**: {tags}
- **Content**:
{previous_content}

### 2. User Feedback to Implement:
"{user_feedback}"

### 3. Original Commit Analysis (for reference only):
- **Change Type**: {change_type}
- **Technical Summary**: {technical_summary}
- **Business Impact**: {business_impact}
- **Key Changes**:
{key_changes}
- **Affected Components**: {affected_components}
- **Technical Details**:
{technical_details}
- **Narrative Angle**: {narrative_angle}
- **Project Context**: {project_context_summary}
- **Original User Instructions**: {user_instructions}
- **Original Commit Message**:
{commit_message}
""",
        ),
    ]
)
