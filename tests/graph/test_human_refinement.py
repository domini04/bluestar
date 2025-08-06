import pytest
from unittest.mock import patch

from bluestar.agents.state import AgentState
from bluestar.agents.nodes.human_refinement import human_refinement_node
from bluestar.formats.llm_outputs import BlogPostOutput, HeadingBlock, ParagraphBlock, CodeBlock, ListBlock

@pytest.fixture
def blog_post_fixture() -> BlogPostOutput:
    """Provides a realistic BlogPostOutput object for testing."""
    return BlogPostOutput(
        title="Solving LLM Content Generation: A Deep Dive into BlueStar's Content Synthesizer",
        author="Shin Y. Lee",
        date="2025-08-04",
        tags=["LLM", "LangGraph", "Pydantic", "Prompt Engineering", "Architecture", "BlueStar"],
        summary="Generating high-quality technical content with LLMs presents two key challenges: unreliable output structure and a generic, non-technical tone. This post details the implementation of BlueStar's ContentSynthesizer node, which solves these problems through a dual approach. We introduced a Pydantic-enforced, block-based output format for structural reliability and platform extensibility, and developed highly-engineered prompts to ensure a precise, engineer-to-engineer tone suitable for our developer audience.",
        body=[
            ParagraphBlock(type="paragraph", content="The core promise of BlueStar is turning Git commits into developer-focused blog posts. While LLMs are a natural fit for this task, raw generation often falls short. The output can be structurally unpredictable and stylistically generic. To deliver on our core value proposition, we needed to solve two primary problems: 1) ensuring reliable, structured output from the LLM, and 2) controlling the tone to be authentically technical and direct. The new `ContentSynthesizer` node addresses both of these challenges head-on."),
            HeadingBlock(type="heading", level=2, content="Problem 1: The Challenge of Unstructured LLM Output"),
            ParagraphBlock(type="paragraph", content="Relying on an LLM to generate raw Markdown is brittle. Minor variations in formatting can break downstream processing, and it tightly couples the content generation logic to a single output format. This makes it difficult to adapt the system to publish on different platforms (e.g., a company blog, Medium, Notion) which may have different formatting requirements or APIs."),
            HeadingBlock(type="heading", level=2, content="Solution: A Platform-Agnostic, Block-Based Model"),
            ParagraphBlock(type="paragraph", content='To solve this, we implemented a significant architectural shift. As noted in our internal development documents, we decided to "decouple content generation from publishing to enhance extensibility." We achieved this by defining a strict, block-based Pydantic model for the blog post content. Instead of a single string of Markdown, the LLM is now required to generate a JSON object that conforms to our `BlogPostOutput` schema.'),
            CodeBlock(type="code", language="python", content='from pydantic import BaseModel\nfrom typing import List, Literal, Union\n\nclass ParagraphBlock(BaseModel):\n    type: Literal["paragraph"] = "paragraph"\n    content: str\n\nclass CodeBlock(BaseModel):\n    type: Literal["code"] = "code"\n    language: str\n    content: str\n\nclass HeadingBlock(BaseModel):\n    type: Literal["heading"] = "heading"\n    level: int\n    content: str\n\nContentBlock = Union[ParagraphBlock, CodeBlock, HeadingBlock]\n\nclass BlogPostOutput(BaseModel):\n    title: str\n    author: str\n    summary: str\n    body: List[ContentBlock]'),
            ParagraphBlock(type="paragraph", content="This structure is enforced using LangChain's `PydanticOutputParser`. The parser automatically appends formatting instructions to the prompt and validates the LLM's output, ensuring we always receive a well-formed `BlogPostOutput` object. This makes the generation process far more reliable and allows us to easily write different \"renderers\" that can transform this structured data into any required final format (HTML, Markdown, etc.) without touching the core generation logic."),
            HeadingBlock(type="heading", level=2, content="Problem 2: The Fight Against Generic, 'Marketing-like' Content"),
            ParagraphBlock(type="paragraph", content="The second major challenge is tone. By default, LLMs can produce content that feels vague, overly enthusiastic, or simply lacks the direct, objective style that developers expect. To create content that resonates with our target audience, we needed precise control over the LLM's voice."),
            HeadingBlock(type="heading", level=2, content="Solution: Surgical Prompt Engineering"),
            ParagraphBlock(type="paragraph", content="We addressed this by engineering two distinct, highly-specific prompts: one for initial generation and another for refinement. The system selects the appropriate prompt based on whether it is creating the first draft or iterating based on user feedback."),
            HeadingBlock(type="heading", level=3, content="The Initial Generation Prompt"),
            ParagraphBlock(type="paragraph", content="For the first draft, we use a prompt with a higher temperature (0.7) to encourage creativity while providing firm guardrails on style. The instructions are explicit about the target audience and desired format."),
            CodeBlock(type="code", language="text", content="ADOPT AN ENGINEER-TO-ENGINEER TONE: Write in a direct, objective, and neutral style. The goal is to clearly explain the work, its context, and its importance. AVOID overly persuasive, exaggerated, or \"marketing-like\" language.\n\nSHOW, DON'T JUST TELL: When explaining technical concepts, implementations, or key changes, try to include small, illustrative code snippets or pseudocode where appropriate."),
            HeadingBlock(type="heading", level=3, content="The Refinement Prompt"),
            ParagraphBlock(type="paragraph", content="When a user provides feedback for edits, we switch to a refinement prompt with a low temperature (0.2) to ensure precision. This prompt instructs the LLM to behave not as a creator, but as an editor making targeted changes."),
            CodeBlock(type="code", language="text", content="You are a surgical editor. Your task is to refine the existing draft of a technical blog post based on specific user feedback. You must follow the user's instructions precisely while preserving the rest of the original draft. Only change what is necessary to fulfill the request."),
            HeadingBlock(type="heading", level=2, content="Integration and Impact"),
            ParagraphBlock(type="paragraph", content="With these components in place, the new `ContentSynthesizer` node was integrated into our main LangGraph workflow, replacing its placeholder. The agent's state was updated to manage the `BlogPostOutput` model and track synthesis iterations. This change completes BlueStar's primary `commit -> analysis -> content` pipeline, delivering a robust and extensible system. By combining a structured output model with targeted prompt engineering, we can now reliably generate high-quality technical content that is immediately useful and easy to extend to new publishing platforms in the future.")
        ]
    )

def test_human_refinement_satisfied_path(blog_post_fixture):
    """Tests the workflow where the user is satisfied with the draft."""
    # Arrange
    initial_state = AgentState(
        repo_identifier="test/repo",
        commit_sha="test_sha",
        blog_post=blog_post_fixture
    )
    
    # Act
    # We patch 'builtins.input' to simulate the user typing 'y' and pressing Enter.
    with patch('builtins.input', return_value='y'):
        final_state = human_refinement_node(initial_state)

    # Assert
    assert final_state.user_satisfied is True
    assert final_state.user_feedback is None
    assert final_state.synthesis_iteration_count == 1

def test_human_refinement_unsatisfied_path(blog_post_fixture):
    """Tests the workflow where the user is not satisfied and provides feedback."""
    # Arrange
    initial_state = AgentState(
        repo_identifier="test/repo",
        commit_sha="test_sha",
        blog_post=blog_post_fixture
    )
    feedback_text = "Make the tone more formal and add a conclusion."
    
    # Act
    # We patch 'builtins.input' to simulate the user first typing 'n',
    # then providing their feedback.
    with patch('builtins.input', side_effect=['n', feedback_text]):
        final_state = human_refinement_node(initial_state)

    # Assert
    assert final_state.user_satisfied is False
    assert final_state.user_feedback == feedback_text
    assert final_state.synthesis_iteration_count == 1
