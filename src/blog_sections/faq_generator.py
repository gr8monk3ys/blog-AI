"""
FAQ generation functionality.
"""
from typing import List, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.blog_sections import FAQ, FAQSection


class FAQGenerationError(Exception):
    """Exception raised for errors in the FAQ generation process."""
    pass


def generate_faqs(
    content: str,
    count: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for FAQ generation
        prompt = f"""
        Generate {count} frequently asked questions (FAQs) with answers based on the following blog content:
        
        {content[:2000]}...
        
        Requirements:
        - Generate exactly {count} questions and answers.
        - Questions should be clear, concise, and directly related to the content.
        - Answers should be comprehensive but concise (2-3 sentences).
        - Cover the most important aspects of the content.
        - Format the output as a numbered list with questions and answers.
        - Use a conversational tone for both questions and answers.
        
        Format each FAQ as:
        
        Q1: [Question 1]
        A1: [Answer 1]
        
        Q2: [Question 2]
        A2: [Answer 2]
        
        And so on.
        """
        
        # Generate FAQs
        faqs_text = generate_text(prompt, provider, options)
        
        # Parse the FAQs
        faqs = parse_faqs(faqs_text)
        
        # Ensure we have the requested number of FAQs
        while len(faqs) < count:
            # Generate more FAQs
            more_count = count - len(faqs)
            more_prompt = f"""
            Generate {more_count} additional frequently asked questions (FAQs) with answers based on the following blog content:
            
            {content[:2000]}...
            
            Requirements:
            - Generate exactly {more_count} questions and answers.
            - Questions should be different from the following existing questions:
            {', '.join([f'"{faq.question}"' for faq in faqs])}
            - Questions should be clear, concise, and directly related to the content.
            - Answers should be comprehensive but concise (2-3 sentences).
            - Cover aspects of the content not already covered by the existing questions.
            - Format the output as a numbered list with questions and answers.
            - Use a conversational tone for both questions and answers.
            
            Format each FAQ as:
            
            Q1: [Question 1]
            A1: [Answer 1]
            
            Q2: [Question 2]
            A2: [Answer 2]
            
            And so on.
            """
            
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
        faqs = []
        lines = text.strip().split("\n")
        
        question = None
        answer = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with Q or A followed by a number and colon
            if line.startswith("Q") and ":" in line:
                # If we already have a question and answer, add them to the list
                if question and answer:
                    faqs.append(FAQ(question=question, answer=answer))
                    question = None
                    answer = None
                
                # Extract the question
                question = line.split(":", 1)[1].strip()
            elif line.startswith("A") and ":" in line:
                # Extract the answer
                answer = line.split(":", 1)[1].strip()
                
                # If we have both question and answer, add them to the list
                if question and answer:
                    faqs.append(FAQ(question=question, answer=answer))
                    question = None
                    answer = None
        
        # Add the last FAQ if it exists
        if question and answer:
            faqs.append(FAQ(question=question, answer=answer))
        
        return faqs
    except Exception as e:
        raise FAQGenerationError(f"Error parsing FAQs: {str(e)}")


def generate_faq_from_questions(
    questions: List[str],
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
            # Create prompt for answer generation
            prompt = f"""
            Answer the following question based on the content provided:
            
            Question: {question}
            
            Content:
            {content[:2000]}...
            
            Requirements:
            - Answer should be comprehensive but concise (2-3 sentences).
            - Use a conversational tone.
            - Stick to the facts presented in the content.
            - Do not include the question in your response.
            
            Return only the answer, nothing else.
            """
            
            # Generate answer
            answer = generate_text(prompt, provider, options)
            
            # Clean up the answer
            answer = answer.strip()
            
            faqs.append(FAQ(question=question, answer=answer))
        
        return FAQSection(title="Frequently Asked Questions", faqs=faqs)
    except Exception as e:
        raise FAQGenerationError(f"Error generating FAQs from questions: {str(e)}")
