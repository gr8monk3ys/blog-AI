"""Base repository interface for I/O operations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """
    Abstract repository for storage operations.

    Provides a clean abstraction over file system, database,
    or cloud storage operations.
    """

    @abstractmethod
    def save(self, content: T, filename: str, **kwargs) -> Path:
        """
        Save content to storage.

        Args:
            content: Content to save
            filename: Target filename
            **kwargs: Additional save options

        Returns:
            Path to saved file

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def load(self, filename: str, **kwargs) -> T:
        """
        Load content from storage.

        Args:
            filename: Source filename
            **kwargs: Additional load options

        Returns:
            Loaded content

        Raises:
            RepositoryError: If load operation fails
        """
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """
        Check if content exists in storage.

        Args:
            filename: Filename to check

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """
        Delete content from storage.

        Args:
            filename: Filename to delete

        Returns:
            True if deleted, False if didn't exist

        Raises:
            RepositoryError: If delete operation fails
        """
        pass
