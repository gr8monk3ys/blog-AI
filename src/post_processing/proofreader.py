"""
Proofreading functionality.
"""
from typing import List, Dict, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.post_processing import ProofreadingOptions, ProofreadingIssue, ProofreadingResult


class ProofreadingError(Exception):
    """Exception raised for errors in the proofreading process."""
    pass


def proofread_content(
    content: str,
    options: Optional[ProofreadingOptions] = None,
    provider: Optional[LLMProvider] = None,
    generation_options: Optional[GenerationOptions] = None
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
        
        # Create prompt for proofreading
        prompt = f"""
        Proofread the following content and identify any issues:
        
        {content}
        
        Requirements:
        """
        
        if options.check_grammar:
            prompt += """
            - Identify any grammar issues, including subject-verb agreement, verb tense, pronoun usage, etc.
            """
        
        if options.check_spelling:
            prompt += """
            - Identify any spelling errors or typos.
            """
        
        if options.check_style:
            prompt += """
            - Identify any style issues, including passive voice, wordiness, jargon, etc.
            """
        
        if options.check_plagiarism:
            prompt += """
            - Identify any potential plagiarism issues, including direct copying, paraphrasing without attribution, etc.
            """
        
        prompt += """
        For each issue, provide:
        1. The type of issue (grammar, spelling, style, plagiarism)
        2. The problematic text
        3. The line and character position
        4. A suggested correction
        
        Return your analysis in the following format:
        
        Issue 1:
        Type: [type]
        Text: [problematic text]
        Position: Line [line number], Character [character position]
        Suggestion: [suggested correction]
        
        Issue 2:
        Type: [type]
        Text: [problematic text]
        Position: Line [line number], Character [character position]
        Suggestion: [suggested correction]
        
        And so on.
        
        If there are no issues, return "No issues found."
        """
        
        # Generate proofreading results
        proofreading_text = generate_text(prompt, provider, generation_options)
        
        # Parse the proofreading results
        issues = parse_proofreading_results(proofreading_text, content)
        
        # Generate corrected text if there are issues
        corrected_text = None
        if issues:
            corrected_text = generate_corrected_text(content, issues, provider, generation_options)
        
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
                        line_number_text = position_text[line_start + 4:line_end].strip()
                        try:
                            issue_position["line"] = int(line_number_text)
                        except ValueError:
                            pass
                    
                    # Extract character position
                    char_start = position_text.find("Character")
                    if char_start != -1:
                        char_number_text = position_text[char_start + 9:].strip()
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
                        suggestion=issue_suggestion
                    )
                )
        
        return issues
    except Exception as e:
        raise ProofreadingError(f"Error parsing proofreading results: {str(e)}")


def generate_corrected_text(
    content: str,
    issues: List[ProofreadingIssue],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for correction
        prompt = f"""
        Correct the following content based on the identified issues:
        
        Content:
        {content}
        
        Issues:
        """
        
        for i, issue in enumerate(issues):
            prompt += f"""
            Issue {i+1}:
            Type: {issue.type}
            Text: {issue.text}
            Position: Line {issue.position["line"]}, Character {issue.position["character"]}
            Suggestion: {issue.suggestion or "No suggestion provided"}
            """
        
        prompt += """
        Return only the corrected content, nothing else.
        """
        
        # Generate corrected text
        corrected_text = generate_text(prompt, provider, options)
        
        return corrected_text.strip()
    except Exception as e:
        raise ProofreadingError(f"Error generating corrected text: {str(e)}")


def check_grammar(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
            check_plagiarism=False
        )
        
        result = proofread_content(content, proofreading_options, provider, options)
        
        return [issue for issue in result.issues if issue.type.lower() == "grammar"]
    except Exception as e:
        raise ProofreadingError(f"Error checking grammar: {str(e)}")


def check_spelling(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
            check_plagiarism=False
        )
        
        result = proofread_content(content, proofreading_options, provider, options)
        
        return [issue for issue in result.issues if issue.type.lower() == "spelling"]
    except Exception as e:
        raise ProofreadingError(f"Error checking spelling: {str(e)}")


def check_style(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
            check_plagiarism=False
        )
        
        result = proofread_content(content, proofreading_options, provider, options)
        
        return [issue for issue in result.issues if issue.type.lower() == "style"]
    except Exception as e:
        raise ProofreadingError(f"Error checking style: {str(e)}")


def check_plagiarism(
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
            check_plagiarism=True
        )
        
        result = proofread_content(content, proofreading_options, provider, options)
        
        return [issue for issue in result.issues if issue.type.lower() == "plagiarism"]
    except Exception as e:
        raise ProofreadingError(f"Error checking plagiarism: {str(e)}")
