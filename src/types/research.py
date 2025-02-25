"""
Type definitions for research functionality.
"""
from typing import List, Dict, Any, Optional, Literal


class SearchResult:
    """A search result from a web search."""
    title: str
    url: str
    snippet: str
    
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet


class PeopleAlsoAsk:
    """A 'People Also Ask' question from a search engine."""
    question: str
    answer: Optional[str]
    
    def __init__(self, question: str, answer: Optional[str] = None):
        self.question = question
        self.answer = answer


class RelatedSearch:
    """A related search query from a search engine."""
    query: str
    
    def __init__(self, query: str):
        self.query = query


class GoogleSerpResult:
    """Results from a Google SERP (Search Engine Results Page) search."""
    organic: List[SearchResult]
    people_also_ask: List[PeopleAlsoAsk]
    related_searches: List[RelatedSearch]
    
    def __init__(
        self,
        organic: List[SearchResult],
        people_also_ask: Optional[List[PeopleAlsoAsk]] = None,
        related_searches: Optional[List[RelatedSearch]] = None
    ):
        self.organic = organic
        self.people_also_ask = people_also_ask or []
        self.related_searches = related_searches or []


class TavilyResult:
    """A result from Tavily AI search."""
    title: str
    url: str
    content: str
    
    def __init__(self, title: str, url: str, content: str):
        self.title = title
        self.url = url
        self.content = content


class TavilySearchResult:
    """Results from a Tavily AI search."""
    results: List[TavilyResult]
    answer: str
    follow_up_questions: List[str]
    
    def __init__(
        self,
        results: List[TavilyResult],
        answer: str,
        follow_up_questions: Optional[List[str]] = None
    ):
        self.results = results
        self.answer = answer
        self.follow_up_questions = follow_up_questions or []


class MetaphorResult:
    """A result from Metaphor AI search."""
    title: str
    url: str
    text: str
    
    def __init__(self, title: str, url: str, text: str):
        self.title = title
        self.url = url
        self.text = text


class TrendPoint:
    """A point in a Google Trends timeline."""
    date: str
    value: float
    
    def __init__(self, date: str, value: float):
        self.date = date
        self.value = value


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
        related_queries: Optional[List[str]] = None
    ):
        self.keyword = keyword
        self.timeline = timeline
        self.related_topics = related_topics or []
        self.related_queries = related_queries or []


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
        similar_url: Optional[str] = None
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
        trends: Optional[GoogleTrendsResult] = None
    ):
        self.google = google
        self.tavily = tavily
        self.metaphor = metaphor
        self.trends = trends
