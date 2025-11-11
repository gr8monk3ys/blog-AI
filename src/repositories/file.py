"""File-based repository implementation."""

import logging
from pathlib import Path

from ..exceptions import RepositoryError
from .base import Repository

logger = logging.getLogger(__name__)


class FileRepository(Repository[str | bytes]):
    """
    File system repository for text and binary content.

    Handles file I/O operations with proper error handling
    and directory management.
    """

    def __init__(self, base_dir: str | Path):
        """
        Initialize file repository.

        Args:
            base_dir: Base directory for file operations
        """
        self.base_dir = Path(base_dir)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create base directory if it doesn't exist."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Repository directory: {self.base_dir}")
        except Exception as e:
            raise RepositoryError(
                f"Failed to create repository directory: {e}",
                details={"directory": str(self.base_dir)},
            ) from e

    def save(
        self,
        content: str | bytes,
        filename: str,
        **kwargs,
    ) -> Path:
        """
        Save content to file.

        Args:
            content: Content to save (text or bytes)
            filename: Target filename (relative to base_dir)
            **kwargs: Additional options (encoding, etc.)

        Returns:
            Full path to saved file

        Raises:
            RepositoryError: If save fails
        """
        try:
            # Construct full path
            filepath = self.base_dir / filename

            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Save content
            if isinstance(content, bytes):
                filepath.write_bytes(content)
                logger.info(f"Saved binary file: {filepath} ({len(content)} bytes)")
            else:
                encoding = kwargs.get("encoding", "utf-8")
                filepath.write_text(content, encoding=encoding)
                logger.info(f"Saved text file: {filepath} ({len(content)} chars)")

            return filepath

        except Exception as e:
            raise RepositoryError(
                f"Failed to save file: {e}",
                details={
                    "filename": filename,
                    "directory": str(self.base_dir),
                },
            ) from e

    def load(self, filename: str, **kwargs) -> str | bytes:
        """
        Load content from file.

        Args:
            filename: Source filename (relative to base_dir)
            **kwargs: Additional options (encoding, mode, etc.)

        Returns:
            File content (text or bytes)

        Raises:
            RepositoryError: If load fails
        """
        try:
            filepath = self.base_dir / filename

            if not filepath.exists():
                raise RepositoryError(
                    f"File not found: {filename}",
                    details={"filepath": str(filepath)},
                )

            # Determine if binary mode
            mode = kwargs.get("mode", "text")

            content: str | bytes
            if mode == "binary":
                content = filepath.read_bytes()
                logger.debug(f"Loaded binary file: {filepath} ({len(content)} bytes)")
            else:
                encoding = kwargs.get("encoding", "utf-8")
                content = filepath.read_text(encoding=encoding)
                logger.debug(f"Loaded text file: {filepath} ({len(content)} chars)")

            return content

        except RepositoryError:
            raise
        except Exception as e:
            raise RepositoryError(
                f"Failed to load file: {e}",
                details={
                    "filename": filename,
                    "directory": str(self.base_dir),
                },
            ) from e

    def exists(self, filename: str) -> bool:
        """
        Check if file exists.

        Args:
            filename: Filename to check

        Returns:
            True if file exists
        """
        filepath = self.base_dir / filename
        return filepath.exists() and filepath.is_file()

    def delete(self, filename: str) -> bool:
        """
        Delete file.

        Args:
            filename: Filename to delete

        Returns:
            True if file was deleted, False if didn't exist

        Raises:
            RepositoryError: If delete fails
        """
        try:
            filepath = self.base_dir / filename

            if not filepath.exists():
                logger.debug(f"File not found for deletion: {filepath}")
                return False

            filepath.unlink()
            logger.info(f"Deleted file: {filepath}")
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to delete file: {e}",
                details={
                    "filename": filename,
                    "directory": str(self.base_dir),
                },
            ) from e

    def list_files(self, pattern: str = "*") -> list[Path]:
        """
        List files matching pattern.

        Args:
            pattern: Glob pattern (default: all files)

        Returns:
            List of file paths

        Raises:
            RepositoryError: If listing fails
        """
        try:
            files = list(self.base_dir.glob(pattern))
            files = [f for f in files if f.is_file()]
            logger.debug(f"Found {len(files)} files matching '{pattern}'")
            return files
        except Exception as e:
            raise RepositoryError(
                f"Failed to list files: {e}",
                details={
                    "pattern": pattern,
                    "directory": str(self.base_dir),
                },
            ) from e
