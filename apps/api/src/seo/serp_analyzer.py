"""
SERP analysis functionality for competitive content optimization.

This module fetches top Google results for a target keyword using the SERP API,
then uses LLM analysis to extract actionable competitive intelligence:
common topics, heading patterns, questions answered, word count ranges,
and semantically related NLP terms.
"""

import json
import logging
import os
import re
from typing import List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.seo import SERPAnalysis, SERPResult

logger = logging.getLogger(__name__)


class SERPAnalyzerError(Exception):
    """Exception raised for errors in the SERP analysis process."""

    pass


def fetch_serp_results(
    keyword: str,
    num_results: int = 10,
    location: str = "us",
    language: str = "en",
) -> dict:
    """
    Fetch raw SERP results from the SERP API for a given keyword.

    Args:
        keyword: The search keyword to analyze.
        num_results: Number of results to fetch (max 20).
        location: Geographic location for the search.
        language: Language code for the search.

    Returns:
        Raw JSON response from the SERP API.

    Raises:
        SERPAnalyzerError: If the SERP API request fails.
    """
    try:
        import requests
    except ImportError:
        raise SERPAnalyzerError(
            "Requests package not installed. Install it with 'pip install requests'."
        )

    api_key = os.environ.get("SERP_API_KEY")
    if not api_key:
        raise SERPAnalyzerError(
            "SERP_API_KEY environment variable not set. "
            "SERP analysis requires a valid SerpApi key."
        )

    num_results = max(1, min(num_results, 20))

    url = "https://serpapi.com/search"
    params = {
        "api_key": api_key,
        "q": keyword,
        "location": location,
        "hl": language,
        "num": num_results,
        "tbm": "search",
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.Timeout as e:
        raise SERPAnalyzerError(f"SERP API request timed out: {e}") from e
    except requests.ConnectionError as e:
        raise SERPAnalyzerError(f"Network error connecting to SERP API: {e}") from e
    except requests.HTTPError as e:
        raise SERPAnalyzerError(f"SERP API HTTP error: {e}") from e
    except requests.RequestException as e:
        raise SERPAnalyzerError(f"SERP API request failed: {e}") from e
    except (ValueError, KeyError) as e:
        raise SERPAnalyzerError(f"Error parsing SERP API response: {e}") from e


def _extract_serp_results(raw_data: dict) -> List[SERPResult]:
    """
    Extract structured SERP results from the raw API response.

    Args:
        raw_data: Raw JSON response from the SERP API.

    Returns:
        List of SERPResult objects.
    """
    results: List[SERPResult] = []
    for idx, item in enumerate(raw_data.get("organic_results", []), start=1):
        results.append(
            SERPResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=idx,
            )
        )
    return results


def _extract_people_also_ask(raw_data: dict) -> List[str]:
    """Extract People Also Ask questions from the raw SERP response."""
    questions: List[str] = []
    for paa in raw_data.get("related_questions", []):
        question = paa.get("question", "").strip()
        if question:
            questions.append(question)
    return questions


def _extract_related_searches(raw_data: dict) -> List[str]:
    """Extract related search queries from the raw SERP response."""
    searches: List[str] = []
    for item in raw_data.get("related_searches", []):
        query = item.get("query", "").strip()
        if query:
            searches.append(query)
    return searches


def _build_competitor_context(results: List[SERPResult]) -> str:
    """
    Build a compact textual summary of competitor results for LLM analysis.

    Args:
        results: List of SERP results to summarize.

    Returns:
        A formatted string representing the competitor landscape.
    """
    lines: List[str] = []
    for r in results:
        lines.append(f"Position {r.position}: {r.title}")
        if r.snippet:
            lines.append(f"  Snippet: {r.snippet}")
        lines.append(f"  URL: {r.url}")
        lines.append("")
    return "\n".join(lines)


def analyze_serp(
    keyword: str,
    num_results: int = 10,
    location: str = "us",
    language: str = "en",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> SERPAnalysis:
    """
    Analyze SERPs for a target keyword and extract competitive intelligence.

    This function:
    1. Fetches top Google results using the SERP API.
    2. Extracts titles, URLs, snippets, PAA questions, and related searches.
    3. Uses LLM analysis to identify common topics, heading patterns,
       questions answered, recommended word count, and NLP terms.

    Args:
        keyword: The target keyword to analyze.
        num_results: Number of SERP results to analyze (1-20).
        location: Geographic location for the search.
        language: Language code for the search.
        provider: LLM provider for competitive analysis.
        options: Generation options for the LLM call.

    Returns:
        SERPAnalysis containing structured competitive intelligence.

    Raises:
        SERPAnalyzerError: If fetching or analyzing SERPs fails.
    """
    try:
        # Step 1: Fetch raw SERP data
        logger.info("Fetching SERP results for keyword: %s", keyword)
        raw_data = fetch_serp_results(
            keyword=keyword,
            num_results=num_results,
            location=location,
            language=language,
        )

        # Step 2: Extract structured results
        serp_results = _extract_serp_results(raw_data)
        paa_questions = _extract_people_also_ask(raw_data)
        related_searches = _extract_related_searches(raw_data)

        if not serp_results:
            logger.warning("No organic results found for keyword: %s", keyword)
            return SERPAnalysis(
                keyword=keyword,
                results=[],
                people_also_ask=paa_questions,
                related_searches=related_searches,
            )

        # Step 3: Use LLM to extract competitive intelligence
        competitor_context = _build_competitor_context(serp_results)

        paa_context = ""
        if paa_questions:
            paa_context = "\n\nPeople Also Ask questions:\n" + "\n".join(
                f"- {q}" for q in paa_questions
            )

        related_context = ""
        if related_searches:
            related_context = "\n\nRelated searches:\n" + "\n".join(
                f"- {s}" for s in related_searches
            )

        prompt = f"""Analyze the following Google SERP (Search Engine Results Page) data for the keyword "{keyword}".

Your task is to extract competitive intelligence that would help a content creator write an article that outranks these results.

SERP Results:
{competitor_context}
{paa_context}
{related_context}

Based on these results, provide the following analysis as a JSON object (return ONLY the JSON, no markdown fencing or explanation):

{{
  "common_topics": ["list of 8-15 topics/entities that appear frequently across top results"],
  "suggested_headings": ["list of 6-12 H2/H3 headings a comprehensive article should include"],
  "questions_to_answer": ["list of 5-10 questions the content should address, including PAA questions"],
  "recommended_word_count": <integer, estimated ideal word count based on the competitive landscape>,
  "nlp_terms": ["list of 15-25 semantically related terms/phrases that should appear naturally in the content for topical authority"]
}}

Guidelines:
- common_topics should be specific entities, concepts, or themes (not generic words).
- suggested_headings should be actionable, user-intent-aligned heading text.
- questions_to_answer should include both PAA questions and inferred questions from snippets.
- recommended_word_count should be a realistic estimate (typically 1200-3000 for competitive keywords).
- nlp_terms should include LSI keywords, related entities, and semantic variations that signal topical depth to search engines.
"""

        logger.info("Analyzing competitor content with LLM for keyword: %s", keyword)
        analysis_text = generate_text(prompt, provider, options)

        # Step 4: Parse the LLM response
        analysis_data = _parse_llm_json(analysis_text)

        return SERPAnalysis(
            keyword=keyword,
            results=serp_results,
            common_topics=analysis_data.get("common_topics", []),
            suggested_headings=analysis_data.get("suggested_headings", []),
            questions_to_answer=analysis_data.get("questions_to_answer", []),
            recommended_word_count=analysis_data.get("recommended_word_count", 1500),
            nlp_terms=analysis_data.get("nlp_terms", []),
            people_also_ask=paa_questions,
            related_searches=related_searches,
        )

    except SERPAnalyzerError:
        raise
    except Exception as e:
        logger.exception("Failed to analyze SERPs for keyword: %s", keyword)
        raise SERPAnalyzerError(
            f"Error analyzing SERPs for '{keyword}': {str(e)}"
        ) from e


def _parse_llm_json(text: str) -> dict:
    """
    Parse JSON from the LLM response, handling common formatting issues.

    Args:
        text: Raw LLM output that should contain a JSON object.

    Returns:
        Parsed dictionary.

    Raises:
        SERPAnalyzerError: If JSON parsing fails.
    """
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Try to find a JSON object in the text
    start_brace = cleaned.find("{")
    end_brace = cleaned.rfind("}")

    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_str = cleaned[start_brace:end_brace + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Fallback: try parsing the whole cleaned text
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM JSON response: %s", e)
        raise SERPAnalyzerError(
            f"Failed to parse competitor analysis from LLM response: {e}"
        ) from e
