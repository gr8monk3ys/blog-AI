"""Repository layer for I/O operations."""

from .base import Repository
from .file import FileRepository

__all__ = [
    "Repository",
    "FileRepository",
]
