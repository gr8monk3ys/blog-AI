"""
Type definitions for content generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


@dataclass
class SourceCitation:
    """A source reference used for research/citations."""

    id: int
    title: str
    url: str
    snippet: str = ""
    provider: str = ""


@dataclass
class SubTopic:
    """A subtopic within a section."""

    title: str
    content: Optional[str] = None


@dataclass
class Section:
    """A section within a blog post or book."""

    title: str
    subtopics: List[SubTopic] = field(default_factory=list)


@dataclass
class BlogPost:
    """A blog post."""

    title: str
    description: str
    sections: List[Section]
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    image: str = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='630' "
        "viewBox='0 0 1200 630'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'"
        "%3E%3Cstop offset='0%25' stop-color='%23f59e0b'/%3E%3Cstop offset='100%25' stop-color="
        "'%23d97706'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1200' height='630' fill="
        "'url(%23g)'/%3E%3Ctext x='600' y='300' text-anchor='middle' dominant-baseline='central' "
        "font-family='system-ui,sans-serif' font-size='64' font-weight='700' fill='white'"
        "%3EBlog AI%3C/text%3E%3Ctext x='600' y='370' text-anchor='middle' font-family="
        "'system-ui,sans-serif' font-size='24' fill='rgba(255,255,255,0.8)'%3EAI-Powered Content"
        "%3C/text%3E%3C/svg%3E"
    )
    tags: List[str] = field(default_factory=lambda: ["AI", "technology"])
    sources: List[SourceCitation] = field(default_factory=list)


@dataclass
class Topic:
    """A topic within a book chapter."""

    title: str
    content: Optional[str] = None


@dataclass
class Chapter:
    """A chapter within a book."""

    number: int
    title: str
    topics: List[Topic] = field(default_factory=list)


@dataclass
class Book:
    """A book."""

    title: str
    chapters: List[Chapter]
    output_file: str = "book.docx"
    tags: List[str] = field(default_factory=list)
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    image: Optional[str] = None
    sources: List[SourceCitation] = field(default_factory=list)


@dataclass
class FAQ:
    """A frequently asked question."""

    question: str
    answer: str


ContentType = Literal["blog", "book", "faq"]


@dataclass
class ContentRequest:
    """A request for content generation."""

    topic: str
    type: ContentType
    options: Dict[str, Any] = field(default_factory=dict)
