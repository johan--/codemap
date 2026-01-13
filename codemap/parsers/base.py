"""Abstract base class for language parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Symbol:
    """Represents a code symbol (class, function, method, etc.)."""

    name: str
    type: str  # class, function, method, async_function, async_method
    lines: tuple[int, int]  # (start_line, end_line), 1-indexed
    signature: Optional[str] = None
    docstring: Optional[str] = None
    children: list["Symbol"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert symbol to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "type": self.type,
            "lines": list(self.lines),
        }
        if self.signature:
            # Truncate long signatures
            sig = self.signature if len(self.signature) <= 100 else self.signature[:97] + "..."
            result["signature"] = sig
        if self.docstring:
            # Truncate long docstrings
            doc = self.docstring.strip()
            result["docstring"] = doc[:150] if len(doc) > 150 else doc
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Symbol":
        """Create a Symbol from a dictionary."""
        children = [cls.from_dict(c) for c in data.get("children", [])]
        return cls(
            name=data["name"],
            type=data["type"],
            lines=tuple(data["lines"]),
            signature=data.get("signature"),
            docstring=data.get("docstring"),
            children=children if children else [],
        )


class Parser(ABC):
    """Abstract base class for language parsers."""

    # File extensions this parser handles
    extensions: list[str] = []

    # Language name
    language: str = ""

    @abstractmethod
    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse source code and extract symbols.

        Args:
            source: The source code to parse.
            filepath: Optional file path for error messages.

        Returns:
            List of top-level Symbol objects.

        Raises:
            SyntaxError: If the source code has syntax errors.
        """
        pass

    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the given file.

        Args:
            filepath: Path to the file.

        Returns:
            True if this parser handles the file's extension.
        """
        return any(filepath.endswith(ext) for ext in self.extensions)
