"""
Pydantic Models for Structured LLM Outputs
"""
from typing import List, Literal, Union, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, model_validator

class ParagraphBlock(BaseModel):
    type: Literal["paragraph"] = Field(description="Indicates a paragraph block.")
    content: str = Field(description="The text content of the paragraph.")

class HeadingBlock(BaseModel):
    type: Literal["heading"] = Field(description="Indicates a heading block.")
    level: int = Field(description="The heading level (e.g., 1 for <h1>).")
    content: str = Field(description="The text content of the heading.")

class ListBlock(BaseModel):
    type: Literal["list"] = Field(description="Indicates a list block.")
    items: List[str] = Field(description="A list of items in the list.")

class CodeBlock(BaseModel):
    type: Literal["code"] = Field(description="Indicates a code block.")
    language: str = Field(description="The programming language of the code.")
    content: str = Field(description="The code snippet.")

ContentBlock = Union[ParagraphBlock, HeadingBlock, ListBlock, CodeBlock]

class BlogPostOutput(BaseModel):
    """
    Defines the structured output for a generated blog post from the LLM.
    """
    title: str = Field(
        description="The engaging, SEO-friendly title of the blog post."
    )
    author: str = Field(
        description="The name of the author of the blog post."
    )
    date: str = Field(
        description="The publication date of the blog post in YYYY-MM-DD format."
    )
    tags: List[str] = Field(
        description="A list of relevant tags for the blog post."
    )
    summary: str = Field(
        description="A concise, one-paragraph summary of the blog post, suitable for social media sharing or a meta description."
    )
    body: List[ContentBlock] = Field(
        description="The main body of the blog post, composed of a list of structured content blocks (e.g., paragraphs, headings, code blocks)."
    )

    @model_validator(mode='before')
    @classmethod
    def case_insensitive_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {k.lower(): v for k, v in data.items()}
        return data
