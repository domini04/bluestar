"""
BlueStar Blog Format Structures - Ghost CMS Integration

Pydantic models optimized for Ghost CMS API compatibility.
These models align with Ghost's Admin API structure for seamless publishing.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationInfo


class GhostAuthor(BaseModel):
    """Ghost author information for blog posts."""
    
    name: str = Field(description="Author display name")
    email: Optional[str] = Field(default=None, description="Author email")
    slug: Optional[str] = Field(default=None, description="Author URL slug")
    bio: Optional[str] = Field(default=None, description="Author biography")
    website: Optional[str] = Field(default=None, description="Author website URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "BlueStar AI",
                "email": "ai@bluestar.dev",
                "slug": "bluestar-ai",
                "bio": "AI-powered developer blog generation agent",
                "website": "https://bluestar.dev"
            }
        }


class GhostTag(BaseModel):
    """Ghost tag structure for content organization."""
    
    name: str = Field(description="Tag display name")
    slug: Optional[str] = Field(default=None, description="Tag URL slug")
    description: Optional[str] = Field(default=None, description="Tag description")
    
    @field_validator('slug', mode='before')
    @classmethod
    def generate_slug(cls, v, info: ValidationInfo):
        """Auto-generate slug from name if not provided."""
        if v is None and info.data and 'name' in info.data:
            return info.data['name'].lower().replace(' ', '-').replace('_', '-')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "JavaScript",
                "slug": "javascript",
                "description": "JavaScript development and tutorials"
            }
        }


class BlogSection(BaseModel):
    """Represents a section within a blog post for structured content generation.
    
    Simplified structure for optional content organization - the LLM can generate
    a complete blog post directly without requiring sections.
    """
    
    title: str = Field(description="Section heading")
    content: str = Field(description="Section content in markdown format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Implementation Details",
                "content": "## Implementation Details\n\nIn this section, we explore the technical implementation..."
            }
        }


class GhostBlogPost(BaseModel):
    """Complete blog post structure optimized for Ghost CMS Admin API."""
    
    # Core content (Ghost required fields)
    title: str = Field(description="Post title")
    html: str = Field(description="Post content in HTML format")
    
    # Publishing control
    status: Literal["draft", "published", "scheduled"] = Field(
        default="draft",
        description="Post publication status"
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication timestamp (for published/scheduled posts)"
    )
    
    # URL and SEO
    slug: str = Field(description="URL slug for the post")
    meta_title: Optional[str] = Field(default=None, description="SEO title override")
    meta_description: Optional[str] = Field(default=None, description="SEO meta description")
    canonical_url: Optional[str] = Field(default=None, description="Canonical URL for SEO")
    
    # Content organization
    tags: List[GhostTag] = Field(default_factory=list, description="Associated tags")
    primary_tag: Optional[GhostTag] = Field(default=None, description="Primary tag for the post")
    featured: bool = Field(default=False, description="Whether this post is featured")
    
    # Author information
    authors: List[GhostAuthor] = Field(default_factory=list, description="Post authors")
    primary_author: Optional[GhostAuthor] = Field(default=None, description="Primary author")
    
    # Visual content
    feature_image: Optional[str] = Field(default=None, description="Featured image URL")
    feature_image_alt: Optional[str] = Field(default=None, description="Featured image alt text")
    feature_image_caption: Optional[str] = Field(default=None, description="Featured image caption")
    
    # Content metadata
    excerpt: Optional[str] = Field(default=None, description="Post excerpt/summary")
    custom_excerpt: Optional[str] = Field(default=None, description="Custom excerpt override")
    
    # Advanced Ghost features
    visibility: Literal["public", "members", "paid"] = Field(
        default="public",
        description="Post visibility level"
    )
    custom_template: Optional[str] = Field(default=None, description="Custom template to use")
    
    # Code injection (for custom CSS/JS)
    codeinjection_head: Optional[str] = Field(default=None, description="Custom head code")
    codeinjection_foot: Optional[str] = Field(default=None, description="Custom footer code")
    
    # Social media metadata
    og_image: Optional[str] = Field(default=None, description="Open Graph image URL")
    og_title: Optional[str] = Field(default=None, description="Open Graph title")
    og_description: Optional[str] = Field(default=None, description="Open Graph description")
    twitter_image: Optional[str] = Field(default=None, description="Twitter Card image URL")
    twitter_title: Optional[str] = Field(default=None, description="Twitter Card title")
    twitter_description: Optional[str] = Field(default=None, description="Twitter Card description")
    
    # Newsletter integration
    email_subject: Optional[str] = Field(default=None, description="Email newsletter subject")
    
    # BlueStar-specific metadata (for tracking and quality)
    commit_references: List[str] = Field(
        default_factory=list,
        description="Git commit SHAs referenced in this post"
    )
    generated_sections: List[BlogSection] = Field(
        default_factory=list,
        description="Optional: Structured sections if content was generated in parts"
    )
    quality_score: Optional[float] = Field(
        default=None,
        description="AI-generated quality score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    generation_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadata about the content generation process"
    )
    
    @field_validator('slug', mode='before')
    @classmethod
    def generate_slug_from_title(cls, v, info: ValidationInfo):
        """Auto-generate slug from title if not provided."""
        if v is None and info.data and 'title' in info.data:
            import re
            # Convert title to URL-friendly slug
            slug = info.data['title'].lower()
            slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
            slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces/dashes with single dash
            return slug.strip('-')
        return v
    
    @field_validator('meta_description', mode='before')
    @classmethod
    def set_meta_description_from_excerpt(cls, v, info: ValidationInfo):
        """Use excerpt as meta description if not provided."""
        if v is None and info.data and 'excerpt' in info.data and info.data['excerpt']:
            return info.data['excerpt'][:160]  # Ghost meta description limit
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Building Secure User Authentication with JWT",
                "html": "<h1>Building Secure User Authentication with JWT</h1><p>Today I implemented...</p>",
                "status": "draft",
                "slug": "building-secure-user-authentication-jwt",
                "meta_description": "Learn how to implement JWT authentication in a web application",
                "tags": [
                    {"name": "JavaScript", "slug": "javascript"},
                    {"name": "Authentication", "slug": "authentication"}
                ],
                "authors": [
                    {"name": "BlueStar AI", "slug": "bluestar-ai"}
                ],
                "featured": False,
                "visibility": "public",
                "excerpt": "A comprehensive guide to implementing JWT authentication...",
                "commit_references": ["a1b2c3d4e5f6"],
                "quality_score": 0.85
            }
        }


class GhostPublishingResult(BaseModel):
    """Result of Ghost CMS publishing operation."""
    
    success: bool = Field(description="Whether publishing was successful")
    
    # Ghost API response data
    post_id: Optional[str] = Field(default=None, description="Ghost post ID")
    post_uuid: Optional[str] = Field(default=None, description="Ghost post UUID")
    url: Optional[str] = Field(default=None, description="Published post URL")
    admin_url: Optional[str] = Field(default=None, description="Ghost admin edit URL")
    
    # Operation metadata
    operation: Literal["create", "update", "publish", "unpublish"] = Field(
        description="Type of operation performed"
    )
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(default=None, description="Type of error encountered")
    retry_count: int = Field(default=0, description="Number of retry attempts", ge=0)
    
    # Timestamps
    published_at: Optional[datetime] = Field(default=None, description="Actual publication timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    # Response metadata
    ghost_version: Optional[str] = Field(default=None, description="Ghost CMS version")
    rate_limit_remaining: Optional[int] = Field(default=None, description="API rate limit remaining")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "post_id": "507f1f77bcf86cd799439011",
                "url": "https://blog.example.com/building-secure-user-authentication-jwt/",
                "operation": "create",
                "published_at": "2025-01-15T10:30:00Z",
                "ghost_version": "5.0.0"
            }
        } 