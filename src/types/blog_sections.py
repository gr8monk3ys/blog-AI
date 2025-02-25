"""
Type definitions for blog sections functionality.
"""
from typing import List, Dict, Any, Optional, Literal


class Introduction:
    """An introduction section for a blog post."""
    content: str
    hook: str
    thesis: str
    
    def __init__(self, content: str, hook: Optional[str] = None, thesis: Optional[str] = None):
        self.content = content
        self.hook = hook or ""
        self.thesis = thesis or ""


class Conclusion:
    """A conclusion section for a blog post."""
    content: str
    summary: str
    call_to_action: Optional[str]
    
    def __init__(self, content: str, summary: Optional[str] = None, call_to_action: Optional[str] = None):
        self.content = content
        self.summary = summary or ""
        self.call_to_action = call_to_action


class FAQ:
    """A frequently asked question for a blog post."""
    question: str
    answer: str
    
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer


class FAQSection:
    """A FAQ section for a blog post."""
    title: str
    faqs: List[FAQ]
    
    def __init__(self, title: str = "Frequently Asked Questions", faqs: Optional[List[FAQ]] = None):
        self.title = title
        self.faqs = faqs or []


class CodeExample:
    """A code example for a blog post."""
    language: str
    code: str
    description: Optional[str]
    
    def __init__(self, language: str, code: str, description: Optional[str] = None):
        self.language = language
        self.code = code
        self.description = description


class CodeExampleSection:
    """A code example section for a blog post."""
    title: str
    examples: List[CodeExample]
    
    def __init__(self, title: str = "Code Examples", examples: Optional[List[CodeExample]] = None):
        self.title = title
        self.examples = examples or []


class TableOfContents:
    """A table of contents for a blog post."""
    items: List[Dict[str, Any]]
    
    def __init__(self, items: Optional[List[Dict[str, Any]]] = None):
        self.items = items or []


class Quote:
    """A quote for a blog post."""
    text: str
    author: Optional[str]
    source: Optional[str]
    
    def __init__(self, text: str, author: Optional[str] = None, source: Optional[str] = None):
        self.text = text
        self.author = author
        self.source = source


class QuoteSection:
    """A quote section for a blog post."""
    quotes: List[Quote]
    
    def __init__(self, quotes: Optional[List[Quote]] = None):
        self.quotes = quotes or []


class CalloutBox:
    """A callout box for a blog post."""
    title: Optional[str]
    content: str
    type: str
    
    def __init__(self, content: str, title: Optional[str] = None, type: str = "info"):
        self.title = title
        self.content = content
        self.type = type


class CalloutSection:
    """A callout section for a blog post."""
    callouts: List[CalloutBox]
    
    def __init__(self, callouts: Optional[List[CalloutBox]] = None):
        self.callouts = callouts or []


SectionType = Literal[
    "introduction",
    "conclusion",
    "faq",
    "code_example",
    "table_of_contents",
    "quote",
    "callout"
]
