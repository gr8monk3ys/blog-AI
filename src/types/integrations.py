"""
Type definitions for integrations functionality.
"""
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


class WordPressCredentials:
    """Credentials for WordPress integration."""
    site_url: str
    username: str
    password: str
    
    def __init__(self, site_url: str, username: str, password: str):
        self.site_url = site_url
        self.username = username
        self.password = password


class WordPressCategory:
    """A WordPress category."""
    id: int
    name: str
    slug: str
    
    def __init__(self, id: int, name: str, slug: str):
        self.id = id
        self.name = name
        self.slug = slug


class WordPressTag:
    """A WordPress tag."""
    id: int
    name: str
    slug: str
    
    def __init__(self, id: int, name: str, slug: str):
        self.id = id
        self.name = name
        self.slug = slug


class WordPressImage:
    """A WordPress image."""
    id: int
    url: str
    alt: str
    
    def __init__(self, id: int, url: str, alt: str):
        self.id = id
        self.url = url
        self.alt = alt


class WordPressPostOptions:
    """Options for a WordPress post."""
    title: str
    content: str
    excerpt: Optional[str]
    slug: Optional[str]
    status: str
    categories: List[int]
    tags: List[int]
    featured_media: Optional[int]
    
    def __init__(
        self,
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        slug: Optional[str] = None,
        status: str = "draft",
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        featured_media: Optional[int] = None
    ):
        self.title = title
        self.content = content
        self.excerpt = excerpt
        self.slug = slug
        self.status = status
        self.categories = categories or []
        self.tags = tags or []
        self.featured_media = featured_media


class GitHubCredentials:
    """Credentials for GitHub integration."""
    token: str
    
    def __init__(self, token: str):
        self.token = token


class GitHubRepository:
    """A GitHub repository."""
    owner: str
    name: str
    
    def __init__(self, owner: str, name: str):
        self.owner = owner
        self.name = name


class GitHubFileOptions:
    """Options for a GitHub file."""
    path: str
    content: str
    message: str
    branch: str
    
    def __init__(
        self,
        path: str,
        content: str,
        message: str = "Add content via blog-AI",
        branch: str = "main"
    ):
        self.path = path
        self.content = content
        self.message = message
        self.branch = branch


class MediumCredentials:
    """Credentials for Medium integration."""
    token: str
    
    def __init__(self, token: str):
        self.token = token


class MediumPostOptions:
    """Options for a Medium post."""
    title: str
    content: str
    content_format: str
    tags: List[str]
    canonical_url: Optional[str]
    publish_status: str
    
    def __init__(
        self,
        title: str,
        content: str,
        content_format: str = "markdown",
        tags: Optional[List[str]] = None,
        canonical_url: Optional[str] = None,
        publish_status: str = "draft"
    ):
        self.title = title
        self.content = content
        self.content_format = content_format
        self.tags = tags or []
        self.canonical_url = canonical_url
        self.publish_status = publish_status


IntegrationType = Literal["wordpress", "github", "medium"]


class IntegrationOptions:
    """Options for integration."""
    type: IntegrationType
    credentials: Dict[str, Any]
    options: Dict[str, Any]
    
    def __init__(
        self,
        type: IntegrationType,
        credentials: Dict[str, Any],
        options: Dict[str, Any]
    ):
        self.type = type
        self.credentials = credentials
        self.options = options


class IntegrationResult:
    """Results from integration."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]]
    
    def __init__(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.data = data
