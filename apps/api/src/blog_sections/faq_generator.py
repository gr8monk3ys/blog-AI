"""
FAQ generation functionality.
"""

import re
from typing import List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.blog_sections import FAQ, FAQSection


class FAQGenerationError(Exception):
    """Exception raised for errors in the FAQ generation process."""

    pass


def generate_faqs(
    content: str,
    count: int = 5,
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> FAQSection:
    """
    Generate FAQs for a blog post.

    Args:
        content: The content of the blog post.
        count: The number of FAQs to generate.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated FAQs.

    Raises:
        FAQGenerationError: If an error occurs during FAQ generation.
    """
    try:
        # PROMPT DESIGN: FAQs are a high-value SEO asset (featured snippets, People Also
        # Ask). We optimize for search-intent questions that real people actually type,
        # and answers that are direct enough to win snippet placement.
        prompt = f"""Generate {count} FAQ entries based on this blog content.

BLOG CONTENT:
{content[:2000]}
"""

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""
REQUIREMENTS:
- Generate exactly {count} question-and-answer pairs.
- Questions must sound like what a real person would type into Google -- natural
  language, not formal or stilted. Use "how", "what", "why", "can I", "should I"
  question formats.
- Each answer should be 2-4 sentences: start with a direct answer in the first
  sentence, then add context or a practical tip.
- Cover different aspects of the content -- do NOT cluster all questions around
  the same subtopic.
- Answers should be specific and actionable, not vague reassurances.
- Do NOT start answers with "Great question!" or "Absolutely!" -- just answer directly.
- Do NOT use words like: delve, landscape, leverage, robust, seamless, utilize

FORMAT (follow exactly):

Q1: [Question]
A1: [Answer]

Q2: [Question]
A2: [Answer]

Continue through Q{count}/A{count}. Return ONLY the Q/A pairs, nothing else."""

        # Generate FAQs
        faqs_text = generate_text(prompt, provider, options)

        # Parse the FAQs
        faqs = parse_faqs(faqs_text)

        # Ensure we have the requested number of FAQs
        while len(faqs) < count:
            # Generate more FAQs
            more_count = count - len(faqs)
            # PROMPT DESIGN: Additional FAQs -- we pass existing questions to avoid
            # duplication and push for coverage of untouched subtopics.
            more_prompt = f"""Generate {more_count} additional FAQ entries based on this blog content.

BLOG CONTENT:
{content[:2000]}
"""

            if brand_voice:
                more_prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

            more_prompt += f"""
ALREADY COVERED (do NOT repeat or rephrase these):
{', '.join([f'"{faq.question}"' for faq in faqs])}

REQUIREMENTS:
- Generate exactly {more_count} NEW question-and-answer pairs.
- Questions must cover aspects of the content NOT addressed by existing questions.
- Questions should sound like real search queries -- natural language, not formal.
- Answers: 2-4 sentences. Lead with the direct answer, then add context.
- Do NOT start answers with "Great question!" or "Absolutely!"
- Do NOT use words like: delve, landscape, leverage, robust, seamless, utilize

FORMAT (follow exactly):

Q1: [Question]
A1: [Answer]

Q2: [Question]
A2: [Answer]

Return ONLY the Q/A pairs, nothing else."""

            more_faqs_text = generate_text(more_prompt, provider, options)
            more_faqs = parse_faqs(more_faqs_text)

            faqs.extend(more_faqs)

        # Limit to the requested number of FAQs
        faqs = faqs[:count]

        return FAQSection(title="Frequently Asked Questions", faqs=faqs)
    except Exception as e:
        raise FAQGenerationError(f"Error generating FAQs: {str(e)}")


def parse_faqs(text: str) -> List[FAQ]:
    """
    Parse FAQs from text.

    Args:
        text: The text containing FAQs.

    Returns:
        The parsed FAQs.

    Raises:
        FAQGenerationError: If an error occurs during FAQ parsing.
    """
    try:
        lines = text.strip().split("\n")

        # If the model returns numbered Q/A pairs (Q1/A1, Q2/A2, ...), pair them by index.
        # This avoids incorrectly pairing mismatched lines like Q1 with A2.
        has_numbered_pairs = any(
            re.match(r"^[QA]\s*\d+\s*:", line.strip(), re.IGNORECASE)
            for line in lines
            if line.strip()
        )

        if has_numbered_pairs:
            questions: dict[int, str] = {}
            answers: dict[int, str] = {}

            q_re = re.compile(r"^Q\s*(\d+)\s*:\s*(.+)$", re.IGNORECASE)
            a_re = re.compile(r"^A\s*(\d+)\s*:\s*(.+)$", re.IGNORECASE)

            for raw_line in lines:
                line = raw_line.strip()
                if not line:
                    continue

                q_match = q_re.match(line)
                if q_match:
                    questions[int(q_match.group(1))] = q_match.group(2).strip()
                    continue

                a_match = a_re.match(line)
                if a_match:
                    answers[int(a_match.group(1))] = a_match.group(2).strip()
                    continue

            faqs: List[FAQ] = []
            for num in sorted(set(questions.keys()) & set(answers.keys())):
                faqs.append(FAQ(question=questions[num], answer=answers[num]))
            return faqs

        # Fallback: parse sequentially (unnumbered Q:/A: format).
        faqs: List[FAQ] = []
        question: Optional[str] = None
        answer: Optional[str] = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.lower().startswith("q") and ":" in line:
                if question and answer:
                    faqs.append(FAQ(question=question, answer=answer))
                    answer = None
                question = line.split(":", 1)[1].strip()
                continue

            if line.lower().startswith("a") and ":" in line:
                answer = line.split(":", 1)[1].strip()
                if question and answer:
                    faqs.append(FAQ(question=question, answer=answer))
                    question = None
                    answer = None

        if question and answer:
            faqs.append(FAQ(question=question, answer=answer))

        return faqs
    except Exception as e:
        raise FAQGenerationError(f"Error parsing FAQs: {str(e)}")


def generate_faq_from_questions(
    questions: List[str],
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> FAQSection:
    """
    Generate FAQs from a list of questions.

    Args:
        questions: The questions to answer.
        content: The content to use for answering the questions.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated FAQs.

    Raises:
        FAQGenerationError: If an error occurs during FAQ generation.
    """
    try:
        faqs = []

        for question in questions:
            # PROMPT DESIGN: Direct answer generation for user-supplied questions.
            # We optimize for conciseness and featured-snippet friendliness.
            prompt = f"""Answer this question using ONLY information from the content below.

Question: {question}

Content:
{content[:2000]}

RULES:
- Start with a direct, specific answer in the first sentence.
- Add 1-2 sentences of supporting context or a practical tip.
- Total length: 2-4 sentences. No more.
- Use natural, conversational language with contractions.
- Do NOT restate the question in your answer.
- Do NOT use filler phrases like "it's important to note" or "it's worth mentioning."
- Stick strictly to facts from the content -- do not invent information.

Return ONLY the answer text, nothing else."""

            # Generate answer
            answer = generate_text(prompt, provider, options)

            # Clean up the answer
            answer = answer.strip()

            faqs.append(FAQ(question=question, answer=answer))

        return FAQSection(title="Frequently Asked Questions", faqs=faqs)
    except Exception as e:
        raise FAQGenerationError(f"Error generating FAQs from questions: {str(e)}")
