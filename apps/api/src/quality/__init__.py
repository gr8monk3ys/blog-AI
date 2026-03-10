"""
Quality assurance modules for content generation.

This package provides tools for ensuring content quality including:
- Plagiarism detection
- Content originality scoring
- Quality metrics
"""

from .plagiarism_checker import (
    BasePlagiarismChecker,
    CopyscapeChecker,
    EmbeddingChecker,
    OriginalityChecker,
    PlagiarismCheckerFactory,
    PlagiarismCheckError,
    get_plagiarism_checker,
)

__all__ = [
    "BasePlagiarismChecker",
    "CopyscapeChecker",
    "EmbeddingChecker",
    "OriginalityChecker",
    "PlagiarismCheckerFactory",
    "PlagiarismCheckError",
    "get_plagiarism_checker",
]
