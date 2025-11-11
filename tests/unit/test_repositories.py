"""Unit tests for repositories."""

from pathlib import Path

import pytest

from src.exceptions import RepositoryError
from src.repositories import FileRepository


class TestFileRepository:
    """Tests for FileRepository."""

    def test_init_creates_directory(self, tmp_path):
        """Test repository creates base directory on init."""
        repo_dir = tmp_path / "test_repo"
        assert not repo_dir.exists()

        repo = FileRepository(repo_dir)

        assert repo_dir.exists()
        assert repo_dir.is_dir()
        assert repo.base_dir == repo_dir

    def test_save_text_file(self, tmp_path):
        """Test saving text content."""
        repo = FileRepository(tmp_path)

        content = "Hello, World!"
        filepath = repo.save(content, "test.txt")

        assert filepath.exists()
        assert filepath.read_text() == "Hello, World!"

    def test_save_binary_file(self, tmp_path):
        """Test saving binary content."""
        repo = FileRepository(tmp_path)

        content = b"Binary content"
        filepath = repo.save(content, "test.bin")

        assert filepath.exists()
        assert filepath.read_bytes() == b"Binary content"

    def test_save_creates_subdirectories(self, tmp_path):
        """Test save creates subdirectories if needed."""
        repo = FileRepository(tmp_path)

        filepath = repo.save("content", "sub/dir/file.txt")

        assert filepath.exists()
        assert (tmp_path / "sub" / "dir").exists()
        assert filepath.read_text() == "content"

    def test_save_with_encoding(self, tmp_path):
        """Test saving with custom encoding."""
        repo = FileRepository(tmp_path)

        content = "Héllo, Wörld!"
        filepath = repo.save(content, "test.txt", encoding="utf-8")

        assert filepath.exists()
        assert filepath.read_text(encoding="utf-8") == "Héllo, Wörld!"

    def test_load_text_file(self, tmp_path):
        """Test loading text content."""
        repo = FileRepository(tmp_path)

        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        # Load it
        content = repo.load("test.txt")

        assert content == "Test content"

    def test_load_binary_file(self, tmp_path):
        """Test loading binary content."""
        repo = FileRepository(tmp_path)

        # Create a binary file
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"Binary data")

        # Load it
        content = repo.load("test.bin", mode="binary")

        assert content == b"Binary data"

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading nonexistent file raises error."""
        repo = FileRepository(tmp_path)

        with pytest.raises(RepositoryError) as exc_info:
            repo.load("nonexistent.txt")

        assert "File not found" in str(exc_info.value)

    def test_exists(self, tmp_path):
        """Test checking file existence."""
        repo = FileRepository(tmp_path)

        # File doesn't exist
        assert not repo.exists("test.txt")

        # Create file
        repo.save("content", "test.txt")

        # Now it exists
        assert repo.exists("test.txt")

    def test_delete_existing_file(self, tmp_path):
        """Test deleting existing file."""
        repo = FileRepository(tmp_path)

        # Create file
        repo.save("content", "test.txt")
        assert repo.exists("test.txt")

        # Delete it
        result = repo.delete("test.txt")

        assert result is True
        assert not repo.exists("test.txt")

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting nonexistent file returns False."""
        repo = FileRepository(tmp_path)

        result = repo.delete("nonexistent.txt")

        assert result is False

    def test_list_files(self, tmp_path):
        """Test listing files."""
        repo = FileRepository(tmp_path)

        # Create multiple files
        repo.save("content1", "file1.txt")
        repo.save("content2", "file2.txt")
        repo.save("content3", "file3.md")

        # List all files
        files = repo.list_files()
        assert len(files) == 3

        # List with pattern
        txt_files = repo.list_files("*.txt")
        assert len(txt_files) == 2

        md_files = repo.list_files("*.md")
        assert len(md_files) == 1

    def test_list_files_excludes_directories(self, tmp_path):
        """Test list_files only returns files, not directories."""
        repo = FileRepository(tmp_path)

        # Create file and directory
        repo.save("content", "file.txt")
        (tmp_path / "subdir").mkdir()

        files = repo.list_files()

        assert len(files) == 1
        assert files[0].name == "file.txt"

    def test_repository_path_handling(self, tmp_path):
        """Test repository handles path objects and strings."""
        # String path
        repo1 = FileRepository(str(tmp_path / "repo1"))
        assert repo1.base_dir.exists()

        # Path object
        repo2 = FileRepository(tmp_path / "repo2")
        assert repo2.base_dir.exists()

    def test_save_overwrite_existing(self, tmp_path):
        """Test saving over existing file."""
        repo = FileRepository(tmp_path)

        # Create initial file
        repo.save("original content", "test.txt")
        assert (tmp_path / "test.txt").read_text() == "original content"

        # Overwrite
        repo.save("new content", "test.txt")
        assert (tmp_path / "test.txt").read_text() == "new content"

    def test_repository_error_details(self, tmp_path):
        """Test repository errors include details."""
        repo = FileRepository(tmp_path)

        try:
            repo.load("nonexistent.txt")
        except RepositoryError as e:
            assert e.details is not None
            assert "filepath" in e.details
            assert "nonexistent.txt" in str(e.details)

    def test_save_logs_info(self, tmp_path, caplog):
        """Test save operations are logged."""
        import logging

        caplog.set_level(logging.INFO)

        repo = FileRepository(tmp_path)
        repo.save("content", "test.txt")

        assert "Saved text file" in caplog.text
        assert "test.txt" in caplog.text
