"""
Code examples generation functionality.
"""

from typing import Dict, List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.blog_sections import CodeExample, CodeExampleSection


class CodeExamplesGenerationError(Exception):
    """Exception raised for errors in the code examples generation process."""

    pass


def generate_code_example(
    language: str,
    description: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> CodeExample:
    """
    Generate a code example.

    Args:
        language: The programming language for the code example.
        description: The description of what the code example should do.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated code example.

    Raises:
        CodeExamplesGenerationError: If an error occurs during code example generation.
    """
    try:
        # PROMPT DESIGN: Code examples need to be production-quality, not toy snippets.
        # We push for realistic patterns, clear comments, and runnable completeness.
        prompt = f"""Write a {language} code example that demonstrates:

{description}

REQUIREMENTS:
- Write PRODUCTION-QUALITY code, not a minimal toy example.
- Follow current {language} best practices and idiomatic patterns.
- Use modern syntax (latest stable version conventions).
- Include concise, useful comments that explain WHY, not WHAT.
  BAD: "// declare a variable"
  GOOD: "// Cache the result to avoid redundant API calls"
- The code must be complete and runnable as-is (include necessary imports).
- Use realistic variable/function names, not foo/bar/baz.
- Include basic error handling where appropriate.
- Keep it focused: demonstrate the concept without unnecessary boilerplate.

Do NOT include markdown code fences (```). Return ONLY the raw code."""

        # Generate code example
        code = generate_text(prompt, provider, options)

        # Clean up the code
        code = code.strip()

        # Remove any markdown code block markers
        if code.startswith("```"):
            first_line_end = code.find("\n")
            if first_line_end != -1:
                code = code[first_line_end + 1 :]

        if code.endswith("```"):
            code = code[:-3].strip()

        return CodeExample(language=language, code=code, description=description)
    except Exception as e:
        raise CodeExamplesGenerationError(f"Error generating code example: {str(e)}")


def generate_code_examples_section(
    title: str,
    examples_descriptions: List[Dict[str, str]],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> CodeExampleSection:
    """
    Generate a code examples section.

    Args:
        title: The title of the code examples section.
        examples_descriptions: A list of dictionaries with "language" and "description" keys.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated code examples section.

    Raises:
        CodeExamplesGenerationError: If an error occurs during code examples section generation.
    """
    try:
        examples = []

        for example_desc in examples_descriptions:
            language = example_desc["language"]
            description = example_desc["description"]

            example = generate_code_example(
                language=language,
                description=description,
                provider=provider,
                options=options,
            )

            examples.append(example)

        return CodeExampleSection(title=title, examples=examples)
    except Exception as e:
        raise CodeExamplesGenerationError(
            f"Error generating code examples section: {str(e)}"
        )


def generate_code_examples_for_topic(
    topic: str,
    languages: List[str],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> CodeExampleSection:
    """
    Generate code examples for a topic.

    Args:
        topic: The topic to generate code examples for.
        languages: The programming languages to generate code examples in.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated code examples section.

    Raises:
        CodeExamplesGenerationError: If an error occurs during code examples generation.
    """
    try:
        # PROMPT DESIGN: Description generation for topic-based code examples.
        # We push for practical, distinct demonstrations per language rather than
        # the same concept translated N times.
        prompt = f"""For the topic "{topic}", describe one code example per language.

Languages: {', '.join(languages)}

RULES:
- Each example should demonstrate a DIFFERENT practical aspect of "{topic}"
  that plays to that language's strengths. Don't just repeat the same logic
  in each language.
- Descriptions should be specific and actionable (1-2 sentences).
  BAD: "Demonstrate how to use {topic} in Python"
  GOOD: "Build a retry decorator with exponential backoff for API calls"
- Focus on real-world use cases, not textbook exercises.

FORMAT (follow exactly):

Language: [language]
Description: [specific, actionable description]

Language: [language]
Description: [specific, actionable description]

Return ONLY the Language/Description pairs."""

        # Generate code examples descriptions
        descriptions_text = generate_text(prompt, provider, options)

        # Parse the descriptions
        examples_descriptions = []

        current_language = None
        current_description = None

        lines = descriptions_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                if current_language and current_description:
                    examples_descriptions.append(
                        {
                            "language": current_language,
                            "description": current_description,
                        }
                    )
                    current_language = None
                    current_description = None
                continue

            if line.startswith("Language:"):
                if current_language and current_description:
                    examples_descriptions.append(
                        {
                            "language": current_language,
                            "description": current_description,
                        }
                    )

                current_language = line[9:].strip()
                current_description = None
            elif line.startswith("Description:"):
                current_description = line[12:].strip()

        # Add the last example if it exists
        if current_language and current_description:
            examples_descriptions.append(
                {"language": current_language, "description": current_description}
            )

        # Generate code examples section
        return generate_code_examples_section(
            title=f"Code Examples for {topic}",
            examples_descriptions=examples_descriptions,
            provider=provider,
            options=options,
        )
    except Exception as e:
        raise CodeExamplesGenerationError(
            f"Error generating code examples for topic: {str(e)}"
        )


def generate_comparative_code_examples(
    task: str,
    languages: List[str],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> CodeExampleSection:
    """
    Generate comparative code examples for a task in different languages.

    Args:
        task: The task to generate code examples for.
        languages: The programming languages to generate code examples in.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated code examples section.

    Raises:
        CodeExamplesGenerationError: If an error occurs during code examples generation.
    """
    try:
        examples = []

        for language in languages:
            example = generate_code_example(
                language=language,
                description=f"Implement {task} in {language}",
                provider=provider,
                options=options,
            )

            examples.append(example)

        return CodeExampleSection(
            title=f"Implementing {task} in Different Languages", examples=examples
        )
    except Exception as e:
        raise CodeExamplesGenerationError(
            f"Error generating comparative code examples: {str(e)}"
        )
