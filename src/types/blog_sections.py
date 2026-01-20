"""
Type definitions for blog sections functionality.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .content import FAQ


@dataclass
class Introduction:
    """An introduction section for a blog post."""

    content: str
    hook: str = ""
    thesis: str = ""


@dataclass
class Conclusion:
    """A conclusion section for a blog post."""

    content: str
    summary: str = ""
    call_to_action: Optional[str] = None


@dataclass
class FAQSection:
    """A FAQ section for a blog post."""

    title: str = "Frequently Asked Questions"
    faqs: List[FAQ] = field(default_factory=list)


@dataclass
class CodeExample:
    """A code example for a blog post."""

    language: str
    code: str
    description: Optional[str] = None


@dataclass
class CodeExampleSection:
    """A code example section for a blog post."""

    title: str = "Code Examples"
    examples: List[CodeExample] = field(default_factory=list)


@dataclass
class TableOfContents:
    """A table of contents for a blog post."""

    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Quote:
    """A quote for a blog post."""

    text: str
    author: Optional[str] = None
    source: Optional[str] = None


@dataclass
class QuoteSection:
    """A quote section for a blog post."""

    quotes: List[Quote] = field(default_factory=list)


@dataclass
class CalloutBox:
    """A callout box for a blog post."""

    content: str
    title: Optional[str] = None
    type: str = "info"


@dataclass
class CalloutSection:
    """A callout section for a blog post."""

    callouts: List[CalloutBox] = field(default_factory=list)


SectionType = Literal[
    "introduction",
    "conclusion",
    "faq",
    "code_example",
    "table_of_contents",
    "quote",
    "callout",
]
