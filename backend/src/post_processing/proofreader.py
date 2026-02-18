"""
Proofreading functionality.
"""

from typing import Dict, List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.post_processing import (
    ProofreadingIssue,
    ProofreadingOptions,
    ProofreadingResult,
)


class ProofreadingError(Exception):
    """Exception raised for errors in the proofreading process."""

    pass


def proofread_content(
    content: str,
    options: Optional[ProofreadingOptions] = None,
    provider: Optional[LLMProvider] = None,
    generation_options: Optional[GenerationOptions] = None,
) -> ProofreadingResult:
    """
    Proofread content for grammar, spelling, style, and plagiarism issues.

    Args:
        content: The content to proofread.
        options: Options for proofreading.
        provider: The LLM provider to use.
        generation_options: Options for text generation.

    Returns:
        The proofreading results.

    Raises:
        ProofreadingError: If an error occurs during proofreading.
    """
    try:
        options = options or ProofreadingOptions()

        # PROMPT DESIGN: Proofreading prompt. We make the model focus on real errors
        # rather than subjective rewrites, and we add AI-specific style checks to
        # catch common AI-generated content patterns.
        prompt = f"""Proofread this content and identify specific issues.

CONTENT:
{content}

CHECK FOR:
"""

        if options.check_grammar:
            prompt += """GRAMMAR:
- Subject-verb agreement errors
- Incorrect verb tenses or tense inconsistencies within a paragraph
- Dangling or misplaced modifiers
- Pronoun-antecedent disagreement
- Run-on sentences or comma splices
- Incorrect use of who/whom, that/which, affect/effect, etc.
"""

        if options.check_spelling:
            prompt += """SPELLING:
- Misspelled words and typos
- Confused homophones (their/there/they're, its/it's, your/you're)
- Inconsistent spelling of the same term
"""

        if options.check_style:
            prompt += """STYLE:
- Overuse of passive voice (flag when active voice would be clearer)
- Wordiness: phrases that can be shortened ("in order to" -> "to", "due to the fact that" -> "because")
- AI-generated filler phrases: "it's important to note that", "it's worth mentioning that",
  "in today's fast-paced world", "in the ever-evolving landscape"
- Overuse of weak intensifiers: "very", "really", "extremely", "incredibly"
- Repetitive sentence structures (e.g., three Subject-Verb-Object sentences in a row)
- Overuse of AI-favored words: "delve", "leverage", "robust", "seamless", "utilize",
  "comprehensive", "multifaceted", "aforementioned"
"""

        if options.check_plagiarism:
            prompt += """PLAGIARISM:
- Phrases that appear to be directly copied from common sources without attribution
- Suspiciously formal or encyclopedic passages that contrast with the surrounding tone
"""

        prompt += """
FOR EACH ISSUE, report exactly:

Issue 1:
Type: [grammar|spelling|style|plagiarism]
Text: [exact problematic text from the content]
Position: Line [line number], Character [character position]
Suggestion: [specific correction or improvement]

Issue 2:
Type: ...
Text: ...
Position: ...
Suggestion: ...

RULES:
- Only flag REAL issues, not subjective preferences.
- Be precise: quote the exact problematic text.
- Provide a specific fix, not a vague suggestion like "consider rewording."
- If there are no issues, return exactly: "No issues found."

Return ONLY the issue list in the format above."""

        # Generate proofreading results
        proofreading_text = generate_text(prompt, provider, generation_options)

        # Parse the proofreading results
        issues = parse_proofreading_results(proofreading_text, content)

        # Generate corrected text if there are issues
        corrected_text = None
        if issues:
            corrected_text = generate_corrected_text(
                content, issues, provider, generation_options
            )

        return ProofreadingResult(issues=issues, corrected_text=corrected_text)
    except Exception as e:
        raise ProofreadingError(f"Error proofreading content: {str(e)}")


def parse_proofreading_results(results: str, content: str) -> List[ProofreadingIssue]:
    """
    Parse proofreading results.

    Args:
        results: The proofreading results text.
        content: The original content.

    Returns:
        A list of proofreading issues.

    Raises:
        ProofreadingError: If an error occurs during parsing.
    """
    try:
        issues = []

        # Check if no issues were found
        if "no issues found" in results.lower():
            return issues

        # Split the results into issues
        issue_texts = results.split("Issue ")

        for issue_text in issue_texts:
            issue_text = issue_text.strip()
            if not issue_text or issue_text.isdigit() or issue_text.startswith(":"):
                continue

            # Remove issue number if present
            if issue_text[0].isdigit() and issue_text[1] == ":":
                issue_text = issue_text[2:].strip()

            # Parse the issue
            issue_type = None
            issue_text_value = None
            issue_position = {"line": 0, "character": 0}
            issue_suggestion = None

            lines = issue_text.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("Type:"):
                    issue_type = line[5:].strip()
                elif line.startswith("Text:"):
                    issue_text_value = line[5:].strip()
                elif line.startswith("Position:"):
                    position_text = line[9:].strip()

                    # Extract line number
                    line_start = position_text.find("Line")
                    line_end = position_text.find(",", line_start)
                    if line_start != -1 and line_end != -1:
                        line_number_text = position_text[
                            line_start + 4 : line_end
                        ].strip()
                        try:
                            issue_position["line"] = int(line_number_text)
                        except ValueError:
                            pass

                    # Extract character position
                    char_start = position_text.find("Character")
                    if char_start != -1:
                        char_number_text = position_text[char_start + 9 :].strip()
                        try:
                            issue_position["character"] = int(char_number_text)
                        except ValueError:
                            pass
                elif line.startswith("Suggestion:"):
                    issue_suggestion = line[11:].strip()

            # Add the issue if all required fields are present
            if issue_type and issue_text_value:
                issues.append(
                    ProofreadingIssue(
                        type=issue_type,
                        text=issue_text_value,
                        position=issue_position,
                        suggestion=issue_suggestion,
                    )
                )

        return issues
    except Exception as e:
        raise ProofreadingError(f"Error parsing proofreading results: {str(e)}")


def generate_corrected_text(
    content: str,
    issues: List[ProofreadingIssue],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> str:
    """
    Generate corrected text based on proofreading issues.

    Args:
        content: The original content.
        issues: The proofreading issues.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The corrected text.

    Raises:
        ProofreadingError: If an error occurs during correction.
    """
    try:
        # PROMPT DESIGN: Corrected text generation. We emphasize surgical fixes --
        # apply the corrections without rewriting surrounding content.
        prompt = f"""Apply these corrections to the content below. Fix ONLY the identified issues.

ORIGINAL CONTENT:
{content}

ISSUES TO FIX:
"""

        for i, issue in enumerate(issues):
            prompt += f"""Issue {i+1}:
Type: {issue.type}
Text: "{issue.text}"
Position: Line {issue.position["line"]}, Character {issue.position["character"]}
Fix: {issue.suggestion or "Apply appropriate correction"}
"""

        prompt += """
RULES:
- Apply each fix precisely. Change ONLY the problematic text identified above.
- Do NOT rephrase, reorganize, or "improve" anything beyond the listed issues.
- Do NOT add new content or remove existing content.
- Do NOT change the tone, voice, or style beyond what the fixes require.
- Preserve all formatting, paragraph breaks, and structure.

Return ONLY the corrected content. No commentary or labels."""

        # Generate corrected text
        corrected_text = generate_text(prompt, provider, options)

        return corrected_text.strip()
    except Exception as e:
        raise ProofreadingError(f"Error generating corrected text: {str(e)}")


def check_grammar(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> List[ProofreadingIssue]:
    """
    Check content for grammar issues.

    Args:
        content: The content to check.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A list of grammar issues.

    Raises:
        ProofreadingError: If an error occurs during checking.
    """
    try:
        proofreading_options = ProofreadingOptions(
            check_grammar=True,
            check_spelling=False,
            check_style=False,
            check_plagiarism=False,
        )

        result = proofread_content(content, proofreading_options, provider, options)

        return [issue for issue in result.issues if issue.type.lower() == "grammar"]
    except Exception as e:
        raise ProofreadingError(f"Error checking grammar: {str(e)}")


def check_spelling(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> List[ProofreadingIssue]:
    """
    Check content for spelling issues.

    Args:
        content: The content to check.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A list of spelling issues.

    Raises:
        ProofreadingError: If an error occurs during checking.
    """
    try:
        proofreading_options = ProofreadingOptions(
            check_grammar=False,
            check_spelling=True,
            check_style=False,
            check_plagiarism=False,
        )

        result = proofread_content(content, proofreading_options, provider, options)

        return [issue for issue in result.issues if issue.type.lower() == "spelling"]
    except Exception as e:
        raise ProofreadingError(f"Error checking spelling: {str(e)}")


def check_style(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> List[ProofreadingIssue]:
    """
    Check content for style issues.

    Args:
        content: The content to check.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A list of style issues.

    Raises:
        ProofreadingError: If an error occurs during checking.
    """
    try:
        proofreading_options = ProofreadingOptions(
            check_grammar=False,
            check_spelling=False,
            check_style=True,
            check_plagiarism=False,
        )

        result = proofread_content(content, proofreading_options, provider, options)

        return [issue for issue in result.issues if issue.type.lower() == "style"]
    except Exception as e:
        raise ProofreadingError(f"Error checking style: {str(e)}")


def check_plagiarism(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> List[ProofreadingIssue]:
    """
    Check content for plagiarism issues.

    Args:
        content: The content to check.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A list of plagiarism issues.

    Raises:
        ProofreadingError: If an error occurs during checking.
    """
    try:
        proofreading_options = ProofreadingOptions(
            check_grammar=False,
            check_spelling=False,
            check_style=False,
            check_plagiarism=True,
        )

        result = proofread_content(content, proofreading_options, provider, options)

        return [issue for issue in result.issues if issue.type.lower() == "plagiarism"]
    except Exception as e:
        raise ProofreadingError(f"Error checking plagiarism: {str(e)}")
