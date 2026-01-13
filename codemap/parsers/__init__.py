"""Language parsers for symbol extraction."""

from .base import Parser, Symbol
from .python_parser import PythonParser

__all__ = ["Parser", "Symbol", "PythonParser"]

# Optional tree-sitter parsers
try:
    from .typescript_parser import TypeScriptParser
    __all__.append("TypeScriptParser")
except ImportError:
    TypeScriptParser = None

try:
    from .javascript_parser import JavaScriptParser
    __all__.append("JavaScriptParser")
except ImportError:
    JavaScriptParser = None
