"""
Type definitions for SEO functionality.
"""
from typing import List, Dict, Any, Optional, Literal


class MetaDescription:
    """A meta description for a blog post or webpage."""
    content: str
    length: int
    
    def __init__(self, content: str):
        self.content = content
        self.length = len(content)


class MetaTag:
    """A meta tag for a blog post or webpage."""
    name: str
    content: str
    
    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


class OpenGraphTag:
    """An Open Graph tag for social media sharing."""
    property: str
    content: str
    
    def __init__(self, property: str, content: str):
        self.property = property
        self.content = content


class TwitterCard:
    """A Twitter card for Twitter sharing."""
    card_type: str
    site: Optional[str]
    title: str
    description: str
    image: Optional[str]
    
    def __init__(
        self,
        card_type: str = "summary_large_image",
        site: Optional[str] = None,
        title: str = "",
        description: str = "",
        image: Optional[str] = None
    ):
        self.card_type = card_type
        self.site = site
        self.title = title
        self.description = description
        self.image = image


class ImageAltText:
    """Alt text for an image."""
    image_path: str
    alt_text: str
    
    def __init__(self, image_path: str, alt_text: str):
        self.image_path = image_path
        self.alt_text = alt_text


class StructuredData:
    """Structured data for rich snippets."""
    type: str
    data: Dict[str, Any]
    
    def __init__(self, type: str, data: Dict[str, Any]):
        self.type = type
        self.data = data


class SEOAnalysisResult:
    """Results from an SEO analysis."""
    score: int
    title_analysis: Dict[str, Any]
    meta_description_analysis: Dict[str, Any]
    content_analysis: Dict[str, Any]
    keyword_analysis: Dict[str, Any]
    recommendations: List[str]
    
    def __init__(
        self,
        score: int,
        title_analysis: Dict[str, Any],
        meta_description_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        keyword_analysis: Dict[str, Any],
        recommendations: List[str]
    ):
        self.score = score
        self.title_analysis = title_analysis
        self.meta_description_analysis = meta_description_analysis
        self.content_analysis = content_analysis
        self.keyword_analysis = keyword_analysis
        self.recommendations = recommendations


class SEOMetadata:
    """SEO metadata for a blog post or webpage."""
    title: str
    meta_description: MetaDescription
    meta_tags: List[MetaTag]
    open_graph_tags: List[OpenGraphTag]
    twitter_card: TwitterCard
    structured_data: Optional[StructuredData]
    
    def __init__(
        self,
        title: str,
        meta_description: MetaDescription,
        meta_tags: Optional[List[MetaTag]] = None,
        open_graph_tags: Optional[List[OpenGraphTag]] = None,
        twitter_card: Optional[TwitterCard] = None,
        structured_data: Optional[StructuredData] = None
    ):
        self.title = title
        self.meta_description = meta_description
        self.meta_tags = meta_tags or []
        self.open_graph_tags = open_graph_tags or []
        self.twitter_card = twitter_card or TwitterCard(title=title, description=meta_description.content)
        self.structured_data = structured_data
