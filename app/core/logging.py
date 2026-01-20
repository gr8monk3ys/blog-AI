"""
Structured logging configuration with JSON format for production.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Produces logs in JSON format suitable for log aggregation systems
    like ELK, Splunk, or CloudWatch.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_path: bool = True,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_path = include_path
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {}

        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        if self.include_level:
            log_data["level"] = record.levelname
            log_data["level_num"] = record.levelno

        if self.include_logger:
            log_data["logger"] = record.name

        if self.include_path:
            log_data["path"] = f"{record.pathname}:{record.lineno}"
            log_data["function"] = record.funcName

        # Main message
        log_data["message"] = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
            ):
                log_data[key] = value

        # Add static extra fields
        log_data.update(self.extra_fields)

        return json.dumps(log_data, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable log formatter for development.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        formatted = (
            f"{color}{timestamp} [{record.levelname:8}]{self.RESET} "
            f"{record.name}: {record.getMessage()}"
        )

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


def setup_logging(
    level: str = None,
    json_format: bool = None,
    service_name: str = "blog-ai",
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to LOG_LEVEL env var or INFO.
        json_format: Whether to use JSON format.
                     Defaults to LOG_FORMAT env var == "json" or True in production.
        service_name: Service name to include in logs.
    """
    # Determine settings from environment
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()

    if json_format is None:
        log_format = os.environ.get("LOG_FORMAT", "").lower()
        # Use JSON in production (when not in dev mode)
        json_format = log_format == "json" or os.environ.get("DEV_MODE", "false").lower() != "true"

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level, logging.INFO))

    # Remove existing handlers
    root_logger.handlers = []

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level, logging.INFO))

    # Set formatter
    if json_format:
        formatter = JSONFormatter(
            extra_fields={
                "service": service_name,
                "environment": os.environ.get("ENVIRONMENT", "development"),
            }
        )
    else:
        formatter = DevelopmentFormatter()

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class RequestLogger:
    """
    Context manager for logging request details.
    """

    def __init__(
        self,
        logger: logging.Logger,
        request_id: str,
        method: str,
        path: str,
        user_id: Optional[str] = None,
    ):
        self.logger = logger
        self.request_id = request_id
        self.method = method
        self.path = path
        self.user_id = user_id
        self.start_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        self.logger.info(
            "Request started",
            extra={
                "request_id": self.request_id,
                "method": self.method,
                "path": self.path,
                "user_id": self.user_id,
            },
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type:
            self.logger.error(
                "Request failed",
                extra={
                    "request_id": self.request_id,
                    "method": self.method,
                    "path": self.path,
                    "user_id": self.user_id,
                    "duration_ms": duration_ms,
                    "error": str(exc_val),
                },
                exc_info=True,
            )
        else:
            self.logger.info(
                "Request completed",
                extra={
                    "request_id": self.request_id,
                    "method": self.method,
                    "path": self.path,
                    "user_id": self.user_id,
                    "duration_ms": duration_ms,
                },
            )

        return False  # Don't suppress exceptions
