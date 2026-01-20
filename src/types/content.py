"""
Type definitions for content generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


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
    image: str = "/images/blog/default.jpg"
    tags: List[str] = field(default_factory=lambda: ["AI", "technology"])


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
