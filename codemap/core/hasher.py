"""File hashing utilities for change detection."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_file(filepath: str | Path) -> str:
    """Generate a short SHA256 hash of file contents.

    Args:
        filepath: Path to the file to hash.

    Returns:
        First 12 characters of the SHA256 hex digest.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        PermissionError: If the file can't be read.
    """
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def hash_content(content: bytes) -> str:
    """Generate a short SHA256 hash of raw content.

    Args:
        content: Raw bytes to hash.

    Returns:
        First 12 characters of the SHA256 hex digest.
    """
    return hashlib.sha256(content).hexdigest()[:12]
