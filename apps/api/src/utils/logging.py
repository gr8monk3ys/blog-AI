"""
Production-grade structured logging for Blog AI.

Provides:
- JSON structured logging for production environments
- Human-readable colored logging for development
- Request context (request_id, user_id) propagation
- Sensitive data filtering
- Performance timing utilities
"""

import json
import logging
import os
import re
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Union

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Patterns for sensitive data that should be redacted
SENSITIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+', re.IGNORECASE),
    re.compile(r'password["\']?\s*[:=]\s*["\']?[^\s,}]+', re.IGNORECASE),
    re.compile(r'secret["\']?\s*[:=]\s*["\']?[\w-]+', re.IGNORECASE),
    re.compile(r'token["\']?\s*[:=]\s*["\']?[\w.-]+', re.IGNORECASE),
    re.compile(r'bearer\s+[\w.-]+', re.IGNORECASE),
    re.compile(r'authorization["\']?\s*[:=]\s*["\']?[^\s,}]+', re.IGNORECASE),
    re.compile(r'sk[-_](?:test|live)[-_][\w]+', re.IGNORECASE),  # Stripe secret keys
    re.compile(r'pk[-_](?:test|live)[-_][\w]+', re.IGNORECASE),  # Stripe public keys
    re.compile(r'whsec_[\w]+', re.IGNORECASE),  # Stripe webhook secrets
    re.compile(r'eyJ[\w-]+\.eyJ[\w-]+\.[\w-]+', re.IGNORECASE),  # JWT tokens
]

REDACTED = "[REDACTED]"

# Fields to exclude from extra data in JSON logs
EXCLUDED_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "created", "filename", "funcName",
    "levelname", "levelno", "lineno", "module", "msecs",
    "pathname", "process", "processName", "relativeCreated",
    "stack_info", "exc_info", "exc_text", "thread", "threadName",
    "request_id", "user_id", "correlation_id", "message", "taskName",
})


def redact_sensitive_data(message: str) -> str:
    """
    Redact sensitive data from log messages.

    Args:
        message: The log message to sanitize

    Returns:
        Message with sensitive data replaced with [REDACTED]
    """
    if not message:
        return message

    result = message
    for pattern in SENSITIVE_PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


class RequestContextFilter(logging.Filter):
    """Add request context to all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context attributes to the log record."""
        record.request_id = request_id_var.get() or "-"
        record.user_id = user_id_var.get() or "-"
        record.correlation_id = correlation_id_var.get() or "-"
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter sensitive data from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from the log record."""
        if record.msg:
            record.msg = redact_sensitive_data(str(record.msg))
        if record.args:
            record.args = tuple(
                redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.

    Outputs logs as single-line JSON objects with consistent structure:
    {
        "timestamp": "2024-01-15T10:30:00.123456Z",
        "level": "INFO",
        "logger": "app.routes.blog",
        "message": "Request completed",
        "service": "blog-ai-api",
        "request_id": "abc-123",
        "user_id": "user-456",
        "correlation_id": "corr-789",
        "extra": {...}
    }
    """

    def __init__(self, service_name: str = "blog-ai-api"):
        """
        Initialize JSON formatter.

        Args:
            service_name: Name of the service for log identification
        """
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "request_id": getattr(record, "request_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }

        # Add source location for errors and above
        if record.levelno >= logging.ERROR:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields (custom fields passed via extra={})
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in EXCLUDED_RECORD_ATTRS and not k.startswith("_")
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, default=str, ensure_ascii=False)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter with colors for development.

    Format: [timestamp] LEVEL    [req_id] [user_id] logger - message
    Colors are applied based on log level.
    """

    # ANSI color codes
    COLORS: Dict[str, str] = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and context."""
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET if color else ""

        request_id = getattr(record, "request_id", "-")
        user_id = getattr(record, "user_id", "-")

        # Truncate IDs for readability
        req_display = request_id[:8] if request_id != "-" else "-"
        user_display = user_id[:8] if user_id != "-" else "-"

        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Build formatted message
        formatted = (
            f"{self.DIM}[{timestamp}]{self.RESET} "
            f"{color}{self.BOLD}{record.levelname:8}{reset} "
            f"{self.DIM}[{req_display:>8}] [{user_display:>8}]{self.RESET} "
            f"{record.name} - {record.getMessage()}"
        )

        # Add extra fields if present
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in EXCLUDED_RECORD_ATTRS and not k.startswith("_")
        }
        if extra_fields:
            formatted += f" {self.DIM}{extra_fields}{self.RESET}"

        # Add exception info
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def get_log_level() -> int:
    """
    Get log level from environment variable.

    Returns:
        Logging level integer (e.g., logging.INFO)
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if level is None:
        # Invalid level specified, default to INFO
        return logging.INFO
    return level


def is_production() -> bool:
    """
    Check if running in production environment.

    Returns:
        True if in production, False otherwise
    """
    env = os.environ.get(
        "ENVIRONMENT",
        os.environ.get("SENTRY_ENVIRONMENT", "development")
    )
    return env.lower() in ("production", "prod")


def should_use_json_format() -> bool:
    """
    Determine if JSON format should be used for logging.

    Returns:
        True if JSON format should be used
    """
    # Check explicit override
    force_json = os.environ.get("LOG_FORMAT_JSON", "").lower() in ("true", "1", "yes")
    if force_json:
        return True

    # Use JSON in production by default
    return is_production()


def setup_logging(
    service_name: str = "blog-ai-api",
    log_level: Optional[int] = None,
    force_json: bool = False,
) -> logging.Logger:
    """
    Configure structured logging for the application.

    This should be called once at application startup, before other modules
    that use logging are imported.

    Args:
        service_name: Name of the service for log identification
        log_level: Override log level (defaults to LOG_LEVEL env var)
        force_json: Force JSON output even in development

    Returns:
        Configured root logger
    """
    level = log_level if log_level is not None else get_log_level()
    use_json = force_json or should_use_json_format()

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Add filters for context and sensitive data
    handler.addFilter(RequestContextFilter())
    handler.addFilter(SensitiveDataFilter())

    # Set formatter based on environment
    if use_json:
        handler.setFormatter(JSONFormatter(service_name))
    else:
        handler.setFormatter(DevelopmentFormatter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Log startup information
    root_logger.info(
        f"Logging configured",
        extra={
            "log_level": logging.getLevelName(level),
            "format": "json" if use_json else "development",
            "service": service_name,
        },
    )

    return root_logger


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Set request context for the current async context.

    This context will be included in all log messages made within
    the current async context.

    Args:
        request_id: Unique identifier for the request
        user_id: Authenticated user identifier
        correlation_id: Correlation ID for distributed tracing
    """
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if correlation_id is not None:
        correlation_id_var.set(correlation_id)


def clear_request_context() -> None:
    """Clear request context after request completion."""
    request_id_var.set(None)
    user_id_var.set(None)
    correlation_id_var.set(None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


def get_user_id() -> Optional[str]:
    """Get current user ID from context."""
    return user_id_var.get()


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return correlation_id_var.get()


class Timer:
    """
    Context manager for timing operations.

    Usage:
        with Timer("database_query") as timer:
            result = db.query(...)
        print(f"Query took {timer.elapsed_ms}ms")

    Or with automatic logging:
        with Timer("database_query", logger):
            result = db.query(...)
    """

    def __init__(
        self,
        name: str,
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.DEBUG,
    ):
        """
        Initialize timer.

        Args:
            name: Name of the operation being timed
            logger: Logger to use for automatic logging (optional)
            log_level: Level to log at when complete
        """
        self.name = name
        self.logger = logger
        self.log_level = log_level
        self.start_time: Optional[float] = None
        self.elapsed_ms: float = 0

    def __enter__(self) -> "Timer":
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and optionally log result."""
        if self.start_time is not None:
            self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000

        if self.logger:
            self.logger.log(
                self.log_level,
                f"{self.name} completed in {self.elapsed_ms:.2f}ms",
                extra={
                    "operation": self.name,
                    "duration_ms": round(self.elapsed_ms, 2),
                    "success": exc_type is None,
                },
            )


def timed(
    name: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.DEBUG,
) -> Callable:
    """
    Decorator for timing function execution.

    Usage:
        @timed("user_lookup")
        async def get_user(user_id: str):
            ...

        @timed()  # Uses function name
        def process_data(data):
            ...

    Args:
        name: Operation name (defaults to function name)
        logger: Logger to use (defaults to function's module logger)
        log_level: Level to log at

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or func.__name__
        func_logger = logger or logging.getLogger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with Timer(operation_name, func_logger, log_level):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with Timer(operation_name, func_logger, log_level):
                return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra: Any,
) -> None:
    """
    Log a message with additional context.

    This is a convenience function that ensures extra fields are properly
    passed to the logger.

    Args:
        logger: Logger instance to use
        level: Log level (e.g., logging.INFO)
        message: Log message
        **extra: Additional fields to include in the log
    """
    logger.log(level, message, extra=extra)
