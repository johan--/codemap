"""Tests for the hasher module."""

import pytest
from pathlib import Path

from codemap.core.hasher import hash_file, hash_content


class TestHashContent:
    """Tests for hash_content function."""

    def test_hash_content_returns_12_chars(self):
        content = b"hello world"
        result = hash_content(content)
        assert len(result) == 12

    def test_hash_content_is_deterministic(self):
        content = b"test content"
        result1 = hash_content(content)
        result2 = hash_content(content)
        assert result1 == result2

    def test_hash_content_different_for_different_content(self):
        content1 = b"hello"
        content2 = b"world"
        assert hash_content(content1) != hash_content(content2)

    def test_hash_content_empty_bytes(self):
        result = hash_content(b"")
        assert len(result) == 12

    def test_hash_content_unicode(self):
        content = "Hello, 世界!".encode("utf-8")
        result = hash_content(content)
        assert len(result) == 12


class TestHashFile:
    """Tests for hash_file function."""

    def test_hash_file_returns_12_chars(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        result = hash_file(test_file)
        assert len(result) == 12

    def test_hash_file_matches_content_hash(self, tmp_path: Path):
        content = "test content"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)

        file_hash = hash_file(test_file)
        content_hash = hash_content(content.encode("utf-8"))
        assert file_hash == content_hash

    def test_hash_file_not_found(self, tmp_path: Path):
        nonexistent = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            hash_file(nonexistent)

    def test_hash_file_binary_content(self, tmp_path: Path):
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(bytes(range(256)))
        result = hash_file(test_file)
        assert len(result) == 12
