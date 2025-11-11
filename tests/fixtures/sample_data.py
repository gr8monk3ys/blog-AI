"""Sample data fixtures for testing."""

from src.models import (
    BlogMetadata,
    BlogPost,
    BlogSection,
    Book,
    Chapter,
    Topic,
)

# Sample Topics with actual model fields
SAMPLE_TOPIC_AI_1 = Topic(
    title="Machine learning fundamentals",
    content="Machine learning algorithms can identify patterns in data...",
)

SAMPLE_TOPIC_AI_2 = Topic(
    title="Deep learning architectures",
    content="Deep learning uses neural networks with multiple layers...",
)

SAMPLE_TOPIC_AI_3 = Topic(
    title="Neural networks explained",
    content="Neural networks are inspired by biological neurons...",
)

SAMPLE_TOPIC_APPS_1 = Topic(
    title="Smart assistants and voice recognition",
    content="Voice assistants like Siri, Alexa, and Google Assistant...",
)

SAMPLE_TOPIC_APPS_2 = Topic(
    title="Personalized recommendations",
    content="Streaming services, e-commerce platforms, and social media...",
)

SAMPLE_TOPIC_APPS_3 = Topic(
    title="Automated decision making",
    content="From credit scoring to medical diagnosis support...",
)

# Sample Blog Post with actual model fields
SAMPLE_BLOG_POST = BlogPost(
    metadata=BlogMetadata(
        title="The Future of Artificial Intelligence in 2024",
        description="Artificial intelligence is rapidly evolving and changing how we live and work.",
        date="2024-01-15",
        image="/images/blog/ai-future.jpg",
        tags=["AI", "technology", "future", "machine learning"],
    ),
    sections=[
        BlogSection(
            title="Understanding Modern AI",
            subtopics=[
                SAMPLE_TOPIC_AI_1,
                SAMPLE_TOPIC_AI_2,
                SAMPLE_TOPIC_AI_3,
            ],
        ),
        BlogSection(
            title="AI Applications in Daily Life",
            subtopics=[
                SAMPLE_TOPIC_APPS_1,
                SAMPLE_TOPIC_APPS_2,
                SAMPLE_TOPIC_APPS_3,
            ],
        ),
        BlogSection(
            title="The Road Ahead",
            subtopics=[
                Topic(
                    title="Emerging AI technologies",
                    content="Quantum computing, neuromorphic chips...",
                ),
                Topic(
                    title="Ethical challenges and governance",
                    content="Important questions about bias, privacy...",
                ),
                Topic(
                    title="Preparing for an AI-driven future",
                    content="Education, workforce adaptation...",
                ),
            ],
        ),
    ],
)

# Sample Book with actual model fields
SAMPLE_BOOK = Book(
    title="Introduction to Python Programming",
    chapters=[
        Chapter(
            number=1,
            title="Getting Started with Python",
            content="""# Chapter 1: Getting Started with Python

Python is a versatile, high-level programming language known for its readability
and ease of use. This chapter introduces the fundamentals of Python programming.

## Installing Python

Visit python.org to download the latest version of Python for your operating system.
The installation process is straightforward and includes the IDLE development environment.

## Your First Python Program

The traditional first program in any language is "Hello, World!". In Python, this is
remarkably simple:

```python
print("Hello, World!")
```

## Python Basics

Python uses indentation to define code blocks, making it visually clean and easy to read.
Variables don't require type declarations, and Python automatically manages memory.

## Summary

In this chapter, we covered Python installation and wrote our first program. The next
chapter explores Python's data types and basic operations.""",
        ),
        Chapter(
            number=2,
            title="Variables and Data Types",
            content="""# Chapter 2: Variables and Data Types

Python supports various data types including integers, floats, strings, booleans,
lists, tuples, dictionaries, and sets.

## Numeric Types

Python has three numeric types: integers (int), floating-point numbers (float), and
complex numbers (complex). You can perform arithmetic operations on these types.

## Strings

Strings in Python are sequences of characters enclosed in quotes. They support various
operations like concatenation, slicing, and formatting.

## Collections

Lists are ordered, mutable collections. Tuples are ordered, immutable collections.
Dictionaries store key-value pairs. Sets contain unique elements.

## Type Conversion

Python provides functions to convert between types: int(), float(), str(), list(),
tuple(), dict(), and set().

## Summary

Understanding Python's data types is fundamental to writing effective programs. The
next chapter covers control flow and decision making.""",
        ),
        Chapter(
            number=3,
            title="Control Flow and Loops",
            content="""# Chapter 3: Control Flow and Loops

Control flow statements allow your program to make decisions and repeat operations.

## Conditional Statements

The if-elif-else structure lets your program choose between different paths based on
conditions. Python uses indentation to define code blocks.

## While Loops

While loops repeat code as long as a condition is true. They're useful when you don't
know in advance how many iterations are needed.

## For Loops

For loops iterate over sequences like lists, tuples, strings, or ranges. They're ideal
when you know how many times to repeat an operation.

## Loop Control

Use 'break' to exit a loop early, 'continue' to skip to the next iteration, and 'else'
clauses to execute code when loops complete normally.

## Summary

Control flow is essential for creating dynamic, responsive programs. The next chapter
explores functions and code organization.""",
        ),
    ],
    output_file="intro_to_python.docx",
)

# Mock LLM Responses (simplified to match actual usage)
MOCK_LLM_TITLE_RESPONSE = "The Future of Artificial Intelligence in 2024"

MOCK_LLM_BLOG_STRUCTURE = {
    "metadata": {
        "title": "The Future of Artificial Intelligence in 2024",
        "description": "Exploring how AI is transforming our world",
        "date": "2024-01-15",
        "image": "/images/blog/ai-future.jpg",
        "tags": ["AI", "technology", "future"],
    },
    "sections": [
        {
            "title": "Understanding Modern AI",
            "subtopics": [
                {"title": "Machine learning fundamentals"},
                {"title": "Deep learning architectures"},
                {"title": "Neural networks explained"},
            ],
        },
        {
            "title": "AI Applications in Daily Life",
            "subtopics": [
                {"title": "Smart assistants"},
                {"title": "Personalized recommendations"},
                {"title": "Automated decision making"},
            ],
        },
    ],
}

MOCK_LLM_TOPIC_CONTENT = """
Machine learning algorithms can identify patterns in data and make predictions based
on those patterns. This technology powers everything from recommendation systems to
autonomous vehicles.
"""

MOCK_LLM_BOOK_OUTLINE = {
    "title": "Introduction to Python Programming",
    "chapters": [
        {"number": 1, "title": "Getting Started with Python"},
        {"number": 2, "title": "Variables and Data Types"},
        {"number": 3, "title": "Control Flow and Loops"},
    ],
    "output_file": "intro_to_python.docx",
}

MOCK_LLM_CHAPTER_CONTENT = """
# Chapter 1: Getting Started with Python

Python is a versatile, high-level programming language known for its readability
and ease of use. This chapter introduces the fundamentals of Python programming.
"""

# Aliases for backward compatibility with tests
MOCK_LLM_BOOK_OUTLINE_RESPONSE = MOCK_LLM_BOOK_OUTLINE
MOCK_LLM_CHAPTER_CONTENT_RESPONSE = MOCK_LLM_CHAPTER_CONTENT


def get_sample_blog_post() -> BlogPost:
    """Return a sample blog post for testing."""
    return SAMPLE_BLOG_POST


def get_sample_book() -> Book:
    """Return a sample book for testing."""
    return SAMPLE_BOOK


def get_mock_llm_responses() -> dict:
    """Return dictionary of mock LLM responses."""
    return {
        "title": MOCK_LLM_TITLE_RESPONSE,
        "blog_structure": MOCK_LLM_BLOG_STRUCTURE,
        "topic_content": MOCK_LLM_TOPIC_CONTENT,
        "book_outline": MOCK_LLM_BOOK_OUTLINE,
        "chapter_content": MOCK_LLM_CHAPTER_CONTENT,
    }
