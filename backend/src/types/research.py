"""
Type definitions for research functionality.
"""

import json
from typing import Any, Dict, List, Literal, Optional


def _truncate(value: Optional[str], max_len: int) -> Optional[str]:
    if value is None:
        return None
    value = str(value)
    if len(value) <= max_len:
        return value
    return value[: max(0, max_len - 3)] + "..."


class SearchResult:
    """A search result from a web search."""

    title: str
    url: str
    snippet: str

    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": _truncate(self.title, 200) or "",
            "url": _truncate(self.url, 500) or "",
            "snippet": _truncate(self.snippet, 400) or "",
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class PeopleAlsoAsk:
    """A 'People Also Ask' question from a search engine."""

    question: str
    answer: Optional[str]

    def __init__(self, question: str, answer: Optional[str] = None):
        self.question = question
        self.answer = answer

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": _truncate(self.question, 200) or "",
            "answer": _truncate(self.answer, 400),
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class RelatedSearch:
    """A related search query from a search engine."""

    query: str

    def __init__(self, query: str):
        self.query = query

    def to_dict(self) -> Dict[str, Any]:
        return {"query": _truncate(self.query, 200) or ""}

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class GoogleSerpResult:
    """Results from a Google SERP (Search Engine Results Page) search."""

    organic: List[SearchResult]
    people_also_ask: List[PeopleAlsoAsk]
    related_searches: List[RelatedSearch]

    def __init__(
        self,
        organic: List[SearchResult],
        people_also_ask: Optional[List[PeopleAlsoAsk]] = None,
        related_searches: Optional[List[RelatedSearch]] = None,
    ):
        self.organic = organic
        self.people_also_ask = people_also_ask or []
        self.related_searches = related_searches or []

    def to_dict(self, max_results: int = 8) -> Dict[str, Any]:
        return {
            "organic": [r.to_dict() for r in (self.organic or [])[:max_results]],
            "people_also_ask": [q.to_dict() for q in (self.people_also_ask or [])[:max_results]],
            "related_searches": [q.to_dict() for q in (self.related_searches or [])[:max_results]],
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class TavilyResult:
    """A result from Tavily AI search."""

    title: str
    url: str
    content: str

    def __init__(self, title: str, url: str, content: str):
        self.title = title
        self.url = url
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": _truncate(self.title, 200) or "",
            "url": _truncate(self.url, 500) or "",
            "content": _truncate(self.content, 600) or "",
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class TavilySearchResult:
    """Results from a Tavily AI search."""

    results: List[TavilyResult]
    answer: str
    follow_up_questions: List[str]

    def __init__(
        self,
        results: List[TavilyResult],
        answer: str,
        follow_up_questions: Optional[List[str]] = None,
    ):
        self.results = results
        self.answer = answer
        self.follow_up_questions = follow_up_questions or []

    def to_dict(self, max_results: int = 8) -> Dict[str, Any]:
        return {
            "answer": _truncate(self.answer, 1200) or "",
            "results": [r.to_dict() for r in (self.results or [])[:max_results]],
            "follow_up_questions": [(_truncate(q, 200) or "") for q in (self.follow_up_questions or [])[:max_results]],
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class MetaphorResult:
    """A result from Metaphor AI search."""

    title: str
    url: str
    text: str

    def __init__(self, title: str, url: str, text: str):
        self.title = title
        self.url = url
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": _truncate(self.title, 200) or "",
            "url": _truncate(self.url, 500) or "",
            "text": _truncate(self.text, 600) or "",
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class TrendPoint:
    """A point in a Google Trends timeline."""

    date: str
    value: float

    def __init__(self, date: str, value: float):
        self.date = date
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {"date": _truncate(self.date, 50) or "", "value": self.value}

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


class GoogleTrendsResult:
    """Results from a Google Trends analysis."""

    keyword: str
    timeline: List[TrendPoint]
    related_topics: List[str]
    related_queries: List[str]

    def __init__(
        self,
        keyword: str,
        timeline: List[TrendPoint],
        related_topics: Optional[List[str]] = None,
        related_queries: Optional[List[str]] = None,
    ):
        self.keyword = keyword
        self.timeline = timeline
        self.related_topics = related_topics or []
        self.related_queries = related_queries or []

    def to_dict(self, max_points: int = 16, max_items: int = 16) -> Dict[str, Any]:
        return {
            "keyword": _truncate(self.keyword, 200) or "",
            "timeline": [p.to_dict() for p in (self.timeline or [])[:max_points]],
            "related_topics": [(_truncate(t, 200) or "") for t in (self.related_topics or [])[:max_items]],
            "related_queries": [(_truncate(q, 200) or "") for q in (self.related_queries or [])[:max_items]],
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)


SearchType = Literal["google", "tavily", "metaphor", "trends"]


class SearchOptions:
    """Options for web search."""

    location: str
    language: str
    num_results: int
    time_range: str
    include_domains: Optional[List[str]]
    similar_url: Optional[str]

    def __init__(
        self,
        location: str = "us",
        language: str = "en",
        num_results: int = 10,
        time_range: str = "anytime",
        include_domains: Optional[List[str]] = None,
        similar_url: Optional[str] = None,
    ):
        self.location = location
        self.language = language
        self.num_results = num_results
        self.time_range = time_range
        self.include_domains = include_domains
        self.similar_url = similar_url


class ResearchResults:
    """Combined results from multiple research sources."""

    google: Optional[GoogleSerpResult]
    tavily: Optional[TavilySearchResult]
    metaphor: Optional[List[MetaphorResult]]
    trends: Optional[GoogleTrendsResult]

    def __init__(
        self,
        google: Optional[GoogleSerpResult] = None,
        tavily: Optional[TavilySearchResult] = None,
        metaphor: Optional[List[MetaphorResult]] = None,
        trends: Optional[GoogleTrendsResult] = None,
    ):
        self.google = google
        self.tavily = tavily
        self.metaphor = metaphor
        self.trends = trends

    def to_dict(self, max_results: int = 8) -> Dict[str, Any]:
        return {
            "google": self.google.to_dict(max_results=max_results) if self.google else None,
            "tavily": self.tavily.to_dict(max_results=max_results) if self.tavily else None,
            "metaphor": [r.to_dict() for r in (self.metaphor or [])[:max_results]] if self.metaphor else None,
            "trends": self.trends.to_dict(max_points=max_results * 2, max_items=max_results * 2) if self.trends else None,
        }

    def __str__(self) -> str:
        # Use JSON so prompts get structured context instead of a memory address.
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)
