"""Custom exceptions for blog-AI."""


class BlogAIException(Exception):
    """
    Base exception for all blog-AI errors.

    All custom exceptions should inherit from this class.
    """

    def __init__(self, message: str, details: dict | None = None):
        """
        Initialize exception with message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigurationError(BlogAIException):
    """
    Raised when configuration validation fails.

    Examples:
        - Missing required API keys
        - Invalid configuration values
        - Malformed .env file
    """

    pass


class LLMError(BlogAIException):
    """
    Raised when LLM API calls fail.

    Examples:
        - API key invalid or expired
        - Rate limiting
        - Network connectivity issues
        - Model not available
    """

    pass


class GenerationError(BlogAIException):
    """
    Raised when content generation fails.

    Examples:
        - Failed to generate structure
        - Failed to generate content
        - Invalid response from LLM
    """

    pass


class ValidationError(BlogAIException):
    """
    Raised when data validation fails.

    Examples:
        - Invalid Pydantic model data
        - Failed to parse LLM output
        - Missing required fields
    """

    pass


class FormattingError(BlogAIException):
    """
    Raised when output formatting fails.

    Examples:
        - MDX formatting error
        - DOCX creation error
        - Template rendering error
    """

    pass


class RepositoryError(BlogAIException):
    """
    Raised when repository operations fail.

    Examples:
        - File write permission error
        - Directory creation error
        - File not found
    """

    pass


class RetryExhaustedError(BlogAIException):
    """
    Raised when retry attempts are exhausted.

    This indicates that an operation was attempted multiple times
    but continued to fail.
    """

    def __init__(
        self,
        message: str,
        attempts: int,
        original_error: Exception | None = None,
        details: dict | None = None,
    ):
        """
        Initialize with retry information.

        Args:
            message: Error message
            attempts: Number of attempts made
            original_error: The last exception that occurred
            details: Additional context
        """
        self.attempts = attempts
        self.original_error = original_error

        final_details = details or {}
        final_details["attempts"] = attempts
        if original_error:
            final_details["original_error"] = str(original_error)

        super().__init__(message, final_details)
