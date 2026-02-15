"""
Web research functionality.
"""

import os
import json
from typing import Any, Dict, List, Optional, Tuple

from ..types.research import (
    GoogleSerpResult,
    GoogleTrendsResult,
    MetaphorResult,
    PeopleAlsoAsk,
    RelatedSearch,
    ResearchResults,
    SearchOptions,
    SearchResult,
    TavilyResult,
    TavilySearchResult,
    TrendPoint,
)
from .cache import get_research_cache


class ResearchError(Exception):
    """Exception raised for errors in the research process."""

    pass


def extract_research_sources(
    research_results: ResearchResults,
    max_sources: int = 8,
) -> List[Dict[str, Any]]:
    """
    Flatten multi-provider research results into a de-duplicated list of sources.

    Returned items are safe to serialize and can be used both for:
    - Prompt context ("cite sources like [1]")
    - API responses (show users which sources informed the output)
    """
    sources: List[Tuple[str, Dict[str, Any]]] = []

    def _add(provider: str, title: str, url: str, snippet: str = "") -> None:
        url = (url or "").strip()
        title = (title or "").strip()
        if not url or not title:
            return
        key = f"{provider}:{url}"
        sources.append(
            (
                key,
                {
                    "provider": provider,
                    "title": title[:200],
                    "url": url[:500],
                    "snippet": (snippet or "")[:400],
                },
            )
        )

    # Google organic results
    if research_results.google and getattr(research_results.google, "organic", None):
        for r in (research_results.google.organic or [])[: max_sources * 2]:
            _add("google", getattr(r, "title", ""), getattr(r, "url", ""), getattr(r, "snippet", ""))

    # Tavily results
    if research_results.tavily and getattr(research_results.tavily, "results", None):
        for r in (research_results.tavily.results or [])[: max_sources * 2]:
            _add("tavily", getattr(r, "title", ""), getattr(r, "url", ""), getattr(r, "content", ""))

    # Metaphor results
    if research_results.metaphor:
        for r in (research_results.metaphor or [])[: max_sources * 2]:
            _add("metaphor", getattr(r, "title", ""), getattr(r, "url", ""), getattr(r, "text", ""))

    # De-duplicate by (provider,url) keeping first.
    seen: set = set()
    deduped: List[Dict[str, Any]] = []
    for key, item in sources:
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= max_sources:
            break

    # Assign stable numeric IDs (1..N) for citations.
    for i, item in enumerate(deduped, start=1):
        item["id"] = i

    return deduped


def format_research_results_for_prompt(
    research_results: ResearchResults,
    max_sources: int = 8,
    max_chars: int = 2200,
) -> str:
    """
    Produce a compact, LLM-friendly research context with numbered sources.

    The generation prompts can instruct the model to cite sources using [n].
    """
    sources = extract_research_sources(research_results, max_sources=max_sources)

    lines: List[str] = []
    lines.append("SOURCES (cite using [n]; do not invent citations):")
    for s in sources:
        snippet = (s.get("snippet") or "").strip().replace("\n", " ")
        snippet = snippet[:280] + ("..." if len(snippet) > 280 else "")
        lines.append(f"[{s['id']}] {s.get('title','').strip()} ({s.get('provider')})")
        lines.append(f"URL: {s.get('url','').strip()}")
        if snippet:
            lines.append(f"Notes: {snippet}")

    # Add provider "answers"/PAA when present (these are secondary, not primary citations).
    if research_results.tavily and getattr(research_results.tavily, "answer", None):
        answer = str(research_results.tavily.answer or "").strip().replace("\n", " ")
        if answer:
            lines.append("")
            lines.append("TAVILY SUMMARY (use as guidance; still cite sources above):")
            lines.append(answer[:800] + ("..." if len(answer) > 800 else ""))

    if research_results.google and getattr(research_results.google, "people_also_ask", None):
        paa = research_results.google.people_also_ask or []
        if paa:
            lines.append("")
            lines.append("PEOPLE ALSO ASK:")
            for q in paa[:6]:
                q_text = str(getattr(q, "question", "") or "").strip()
                a_text = str(getattr(q, "answer", "") or "").strip()
                if not q_text:
                    continue
                lines.append(f"- {q_text}" + (f" | {a_text[:180]}{'...' if len(a_text) > 180 else ''}" if a_text else ""))

    out = "\n".join(lines).strip()
    if len(out) <= max_chars:
        return out
    return out[: max(0, max_chars - 3)] + "..."


def conduct_web_research(
    keywords: List[str], options: Optional[SearchOptions] = None
) -> ResearchResults:
    """
    Conduct web research using multiple sources.

    Args:
        keywords: The keywords to research.
        options: Options for the search.

    Returns:
        The research results.

    Raises:
        ResearchError: If an error occurs during research.
    """
    options = options or SearchOptions()
    cache = get_research_cache()
    cache_enabled = os.environ.get("DEV_MODE", "false").lower() != "true"

    try:
        # Convert keywords list to a string for searching
        search_query = " ".join(keywords)

        cache_key = _build_cache_key(search_query, options)
        if cache_enabled:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        # Conduct research using different sources
        google_results = google_serp_search(search_query, options)
        tavily_results = tavily_ai_search(search_query, options)
        metaphor_results = metaphor_ai_search(search_query, options)
        trends_results = google_trends_analysis(keywords, options)

        # Combine results
        results = ResearchResults(
            google=google_results,
            tavily=tavily_results,
            metaphor=metaphor_results,
            trends=trends_results,
        )
        if cache_enabled:
            cache.set(cache_key, results)
        return results
    except ResearchError:
        # Re-raise ResearchError as-is
        raise
    except Exception as e:
        # Catch-all for unexpected errors, log full traceback
        import traceback
        traceback.print_exc()
        raise ResearchError(f"Unexpected error conducting web research: {str(e)}") from e


def _build_cache_key(query: str, options: SearchOptions) -> str:
    """Build a stable cache key for research requests."""
    payload = {
        "query": query,
        "location": options.location,
        "language": options.language,
        "num_results": options.num_results,
        "time_range": options.time_range,
        "include_domains": sorted(options.include_domains or []),
        "similar_url": options.similar_url,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def google_serp_search(
    query: str, options: SearchOptions
) -> Optional[GoogleSerpResult]:
    """
    Search using Google SERP API.

    Args:
        query: The search query.
        options: Options for the search.

    Returns:
        The search results.

    Raises:
        ResearchError: If an error occurs during search.
    """
    try:
        import requests

        api_key = os.environ.get("SERP_API_KEY")
        if not api_key:
            raise ResearchError("SERP_API_KEY environment variable not set")

        url = "https://serpapi.com/search"

        params = {
            "api_key": api_key,
            "q": query,
            "location": options.location,
            "hl": options.language,
            "num": options.num_results,
            "tbm": "search",
            "tbs": (
                f"qdr:{options.time_range}" if options.time_range != "anytime" else ""
            ),
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        # Extract organic results
        organic_results = []
        for result in data.get("organic_results", []):
            organic_results.append(
                SearchResult(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    snippet=result.get("snippet", ""),
                )
            )

        # Extract "People Also Ask" questions
        paa_results = []
        for paa in data.get("related_questions", []):
            paa_results.append(
                PeopleAlsoAsk(
                    question=paa.get("question", ""), answer=paa.get("answer", "")
                )
            )

        # Extract related searches
        related_searches = []
        for related in data.get("related_searches", []):
            related_searches.append(RelatedSearch(query=related.get("query", "")))

        return GoogleSerpResult(
            organic=organic_results,
            people_also_ask=paa_results,
            related_searches=related_searches,
        )
    except ImportError:
        raise ResearchError(
            "Requests package not installed. Install it with 'pip install requests'."
        )
    except requests.Timeout as e:
        raise ResearchError(f"Google SERP request timed out: {str(e)}") from e
    except requests.ConnectionError as e:
        raise ResearchError(f"Network error connecting to Google SERP: {str(e)}") from e
    except requests.HTTPError as e:
        raise ResearchError(f"Google SERP HTTP error: {str(e)}") from e
    except requests.RequestException as e:
        raise ResearchError(f"Google SERP request failed: {str(e)}") from e
    except KeyError as e:
        raise ResearchError(f"Unexpected response format from Google SERP, missing key: {str(e)}") from e
    except (TypeError, ValueError) as e:
        raise ResearchError(f"Error parsing Google SERP response: {str(e)}") from e


def tavily_ai_search(
    query: str, options: SearchOptions
) -> Optional[TavilySearchResult]:
    """
    Search using Tavily AI.

    Args:
        query: The search query.
        options: Options for the search.

    Returns:
        The search results.

    Raises:
        ResearchError: If an error occurs during search.
    """
    try:
        import requests

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ResearchError("TAVILY_API_KEY environment variable not set")

        url = "https://api.tavily.com/search"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "query": query,
            "search_depth": "advanced",
            "max_results": options.num_results,
            "include_answer": True,
            "include_domains": options.include_domains,
            "include_raw_content": False,
            "include_images": False,
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        # Extract results
        tavily_results = []
        for item in result.get("results", []):
            tavily_results.append(
                TavilyResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                )
            )

        return TavilySearchResult(
            results=tavily_results,
            answer=result.get("answer", ""),
            follow_up_questions=result.get("follow_up_questions", []),
        )
    except ImportError:
        raise ResearchError(
            "Requests package not installed. Install it with 'pip install requests'."
        )
    except requests.Timeout as e:
        raise ResearchError(f"Tavily AI request timed out: {str(e)}") from e
    except requests.ConnectionError as e:
        raise ResearchError(f"Network error connecting to Tavily AI: {str(e)}") from e
    except requests.HTTPError as e:
        raise ResearchError(f"Tavily AI HTTP error: {str(e)}") from e
    except requests.RequestException as e:
        raise ResearchError(f"Tavily AI request failed: {str(e)}") from e
    except KeyError as e:
        raise ResearchError(f"Unexpected response format from Tavily AI, missing key: {str(e)}") from e
    except (TypeError, ValueError) as e:
        raise ResearchError(f"Error parsing Tavily AI response: {str(e)}") from e


def metaphor_ai_search(
    query: str, options: SearchOptions
) -> Optional[List[MetaphorResult]]:
    """
    Search using Metaphor AI.

    Args:
        query: The search query.
        options: Options for the search.

    Returns:
        The search results.

    Raises:
        ResearchError: If an error occurs during search.
    """
    try:
        import requests

        api_key = os.environ.get("METAPHOR_API_KEY")
        if not api_key:
            raise ResearchError("METAPHOR_API_KEY environment variable not set")

        url = "https://api.metaphor.systems/search"

        headers = {"Content-Type": "application/json", "x-api-key": api_key}

        data = {
            "query": query,
            "numResults": options.num_results,
            "useAutoprompt": True,
        }

        if options.similar_url:
            data["type"] = "neural"
            data["url"] = options.similar_url

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        # Extract results
        metaphor_results = []
        for item in result.get("results", []):
            # Get content for each result
            content_url = f"https://api.metaphor.systems/contents"
            content_data = {"ids": [item.get("id")]}

            content_response = requests.post(
                content_url, headers=headers, json=content_data
            )
            content_response.raise_for_status()

            content_result = content_response.json()
            content = content_result.get("contents", [{}])[0].get("extract", "")

            metaphor_results.append(
                MetaphorResult(
                    title=item.get("title", ""), url=item.get("url", ""), text=content
                )
            )

        return metaphor_results
    except ImportError:
        raise ResearchError(
            "Requests package not installed. Install it with 'pip install requests'."
        )
    except requests.Timeout as e:
        raise ResearchError(f"Metaphor AI request timed out: {str(e)}") from e
    except requests.ConnectionError as e:
        raise ResearchError(f"Network error connecting to Metaphor AI: {str(e)}") from e
    except requests.HTTPError as e:
        raise ResearchError(f"Metaphor AI HTTP error: {str(e)}") from e
    except requests.RequestException as e:
        raise ResearchError(f"Metaphor AI request failed: {str(e)}") from e
    except KeyError as e:
        raise ResearchError(f"Unexpected response format from Metaphor AI, missing key: {str(e)}") from e
    except (TypeError, ValueError) as e:
        raise ResearchError(f"Error parsing Metaphor AI response: {str(e)}") from e


def google_trends_analysis(
    keywords: List[str], options: SearchOptions
) -> Optional[GoogleTrendsResult]:
    """
    Analyze trends using Google Trends.

    Args:
        keywords: The keywords to analyze.
        options: Options for the analysis.

    Returns:
        The analysis results.

    Raises:
        ResearchError: If an error occurs during analysis.
    """
    try:
        from pytrends.request import TrendReq

        # Use the first keyword for trends analysis
        keyword = keywords[0] if keywords else ""

        if not keyword:
            return None

        # Initialize pytrends
        pytrends = TrendReq(hl=options.language, geo=options.location.upper())

        # Build payload
        pytrends.build_payload([keyword], timeframe="today 12-m")

        # Get interest over time
        interest_over_time = pytrends.interest_over_time()

        # Get related topics
        related_topics = pytrends.related_topics()

        # Get related queries
        related_queries = pytrends.related_queries()

        # Extract timeline data
        timeline = []
        if not interest_over_time.empty:
            for date, row in interest_over_time.iterrows():
                timeline.append(
                    TrendPoint(
                        date=date.strftime("%Y-%m-%d"), value=float(row[keyword])
                    )
                )

        # Extract related topics
        topics = []
        if keyword in related_topics:
            for _, row in related_topics[keyword]["top"].iterrows():
                topics.append(row["topic_title"])

        # Extract related queries
        queries = []
        if keyword in related_queries:
            for _, row in related_queries[keyword]["top"].iterrows():
                queries.append(row["query"])

        return GoogleTrendsResult(
            keyword=keyword,
            timeline=timeline,
            related_topics=topics,
            related_queries=queries,
        )
    except ImportError:
        raise ResearchError(
            "Pytrends package not installed. Install it with 'pip install pytrends'."
        )
    except requests.Timeout as e:
        raise ResearchError(f"Google Trends request timed out: {str(e)}") from e
    except requests.ConnectionError as e:
        raise ResearchError(f"Network error connecting to Google Trends: {str(e)}") from e
    except requests.RequestException as e:
        raise ResearchError(f"Google Trends request failed: {str(e)}") from e
    except KeyError as e:
        raise ResearchError(f"Unexpected response format from Google Trends, missing key: {str(e)}") from e
    except (TypeError, ValueError, AttributeError) as e:
        raise ResearchError(f"Error parsing Google Trends response: {str(e)}") from e
