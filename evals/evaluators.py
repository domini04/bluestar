"""
BlueStar Custom Evaluators for LangSmith

This module defines the evaluators (judges) used to score BlueStar's blog generation performance.
It includes both deterministic (code-based) evaluators and LLM-based evaluators.
"""

import re
from typing import Optional, Dict, Any
from langsmith.schemas import Run, Example
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

# --- LLM CONFIGURATION ---
def get_evaluator_llm():
    """Returns the configured Gemini 2.5 Pro LLM for evaluation."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro", # Using Flash for speed/cost in evals, or Pro for quality
        temperature=0,                 # Deterministic output for consistent grading
        max_retries=2
    )

# --- 1. DETERMINISTIC EVALUATORS (Python Logic) ---

def structure_evaluator(run: Run, example: Optional[Example] = None) -> Dict[str, Any]:
    """
    Checks structural requirements:
    1. Word count (Target: 800-1500, but flexible for short commits)
    2. Code-to-text ratio (Target: < 40%)
    3. Formatting (Markdown headers)
    """
    # Extract output
    if not run.outputs or "blog_content" not in run.outputs:
        return {"key": "structure_quality", "score": 0, "comment": "No blog output generated"}
    
    content = run.outputs["blog_content"]
    
    # 1. Word Count Check
    words = content.split()
    word_count = len(words)
    
    # 2. Code Ratio Check
    # Regex to find code blocks ```...```
    code_blocks = re.findall(r'```[\s\S]*?```', content)
    code_char_count = sum(len(block) for block in code_blocks)
    total_char_count = len(content)
    
    code_ratio = 0
    if total_char_count > 0:
        code_ratio = code_char_count / total_char_count
        
    # 3. Header Check
    has_h1 = bool(re.search(r'^#\s+', content, re.MULTILINE))
    has_h2 = bool(re.search(r'^##\s+', content, re.MULTILINE))
    
    # Scoring Logic
    score = 1
    issues = []
    
    if code_ratio > 0.45: # Slightly loose buffer
        score = 0
        issues.append(f"Too much code ({code_ratio:.1%}, limit 40%)")
        
    if not (has_h1 or has_h2):
        score = 0
        issues.append("Missing standard markdown headers (# or ##)")
        
    # We are lenient on word count for now as simple commits might be short
    # but we log it for visibility
    comment = f"Words: {word_count}, Code Ratio: {code_ratio:.1%}. " + "; ".join(issues)
    
    return {
        "key": "structure_quality",
        "score": score,
        "comment": comment
    }


# --- 2. LLM-AS-A-JUDGE EVALUATORS ---

class BinaryGrade(BaseModel):
    score: int = Field(description="1 for Pass, 0 for Fail")
    reasoning: str = Field(description="Explanation of the verdict")

def faithfulness_evaluator(run: Run, example: Optional[Example] = None) -> Dict[str, Any]:
    """
    Checks for Hallucinations / Invented Code.
    Did the LLM generate code or claims not supported by the input diff?
    """
    if not run.outputs or "blog_content" not in run.outputs:
        return {"key": "faithfulness", "score": 0, "comment": "No output"}
    
    # Extract Input (Commit Data) from the Run Outputs (Option B strategy)
    # The 'target_app' now returns 'commit_context' explicitly fetched from the CommitFetcher node.
    if "commit_context" in run.outputs:
        commit_inputs = run.outputs["commit_context"]
    else:
        # Fallback to dataset inputs if run failed to capture context (unlikely with new wrapper)
        commit_inputs = str(example.inputs) if example else "No input available"
        
    blog_post = run.outputs["blog_content"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a strict Code Auditor for a technical blog generation agent.
Your goal is to detect HALLUCINATIONS, specifically "Invented Code" or "Unsupported Claims".

Review the Blog Post generated for the given Commit Context.

FAIL CRITERIA (Score 0):
1. The blog post contains code snippets that appear to be completely invented/hallucinated and not derived from standard boilerplate or the likely commit context.
2. The blog post claims technical details (e.g., "Added AWS Lambda") that contradict or are completely absent from the commit context provided.
3. The blog post is a generic tutorial that ignores the specific context of the commit.

PASS CRITERIA (Score 1):
1. Code snippets are illustrative, syntactically correct, and relevant to the technologies mentioned.
2. All technical claims are plausible given the commit context.
3. It describes the specific changes (e.g. "Updated README") accurately.

Constraint: Illustrative pseudo-code (e.g. showing how a library works) IS allowed if it explains a concept mentioned in the docs/commit. It is NOT a hallucination unless it claims to be the actual diff when it isn't.
"""),
        ("human", """
COMMIT CONTEXT:
{commit_context}

GENERATED BLOG POST:
{blog_post}

Grade this post for Faithfulness.
""")
    ])
    
    llm = get_evaluator_llm().with_structured_output(BinaryGrade)
    chain = prompt | llm
    
    try:
        result = chain.invoke({
            "commit_context": commit_inputs,
            "blog_post": blog_post
        })
        return {
            "key": "faithfulness",
            "score": result.score,
            "comment": result.reasoning
        }
    except Exception as e:
        return {"key": "faithfulness", "score": 0, "comment": f"Evaluator Error: {str(e)}"}


def core_accuracy_evaluator(run: Run, example: Optional[Example] = None) -> Dict[str, Any]:
    """
    Checks if the blog post captures the 'Main Event' (Intent) of the commit.
    """
    if not run.outputs or "blog_content" not in run.outputs:
        return {"key": "core_accuracy", "score": 0, "comment": "No output"}

    # Extract Input (Commit Data) from the Run Outputs (Option B strategy)
    if "commit_context" in run.outputs:
        commit_inputs = run.outputs["commit_context"]
    else:
        commit_inputs = str(example.inputs) if example else "No input available"

    blog_post = run.outputs["blog_content"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Technical Editor.
Your goal is to verify CORE ACCURACY. Does the blog post talk about the right thing?

FAIL CRITERIA (Score 0):
- The post misses the main point (e.g., Commit is about "Refactoring", Post talks about "New Features").
- The post focuses on minor details (e.g., "Updated .gitignore") and misses the big picture.

PASS CRITERIA (Score 1):
- The post correctly identifies the primary change (e.g., "Documentation Update", "Architecture Refactor").
- The technical summary aligns with the commit intent.
"""),
        ("human", """
COMMIT CONTEXT:
{commit_context}

GENERATED BLOG POST:
{blog_post}

Grade this post for Core Accuracy.
""")
    ])
    
    llm = get_evaluator_llm().with_structured_output(BinaryGrade)
    chain = prompt | llm
    
    try:
        result = chain.invoke({
            "commit_context": commit_inputs,
            "blog_post": blog_post
        })
        return {
            "key": "core_accuracy",
            "score": result.score,
            "comment": result.reasoning
        }
    except Exception as e:
        return {"key": "core_accuracy", "score": 0, "comment": f"Evaluator Error: {str(e)}"}

