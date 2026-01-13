"""Tests for the Python parser."""

import pytest

from codemap.parsers.python_parser import PythonParser


class TestPythonParser:
    """Tests for PythonParser class."""

    @pytest.fixture
    def parser(self):
        return PythonParser()

    def test_parse_simple_function(self, parser):
        source = '''
def hello(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}"
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "hello"
        assert symbols[0].type == "function"
        assert symbols[0].lines == (2, 4)
        assert "name: str" in symbols[0].signature
        assert "-> str" in symbols[0].signature
        assert symbols[0].docstring == "Greet someone."

    def test_parse_async_function(self, parser):
        source = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    pass
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].name == "fetch_data"
        assert symbols[0].type == "async_function"

    def test_parse_class_with_methods(self, parser):
        source = '''
class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        calc = symbols[0]
        assert calc.name == "Calculator"
        assert calc.type == "class"
        assert calc.docstring == "A simple calculator."
        assert len(calc.children) == 2
        assert calc.children[0].name == "add"
        assert calc.children[0].type == "method"
        assert calc.children[1].name == "subtract"

    def test_parse_class_with_async_method(self, parser):
        source = '''
class Service:
    async def process(self, data: str) -> bool:
        pass
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].children[0].name == "process"
        assert symbols[0].children[0].type == "async_method"

    def test_parse_nested_class(self, parser):
        source = '''
class Outer:
    class Inner:
        def method(self):
            pass
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        outer = symbols[0]
        assert outer.name == "Outer"
        assert len(outer.children) == 1
        inner = outer.children[0]
        assert inner.name == "Inner"
        assert inner.type == "class"
        assert len(inner.children) == 1

    def test_parse_decorated_function(self, parser):
        source = '''
@decorator
@another_decorator
def decorated_func():
    pass
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        # Decorator should be included in line range
        assert symbols[0].lines[0] == 2  # First decorator line
        assert symbols[0].lines[1] == 5  # End of function

    def test_parse_decorated_class(self, parser):
        source = '''
@dataclass
class MyClass:
    field: str
'''
        symbols = parser.parse(source)

        assert len(symbols) == 1
        assert symbols[0].lines[0] == 2  # Decorator line

    def test_parse_function_with_default_args(self, parser):
        source = '''
def func(a: int, b: str = "default", c: bool = True):
    pass
'''
        symbols = parser.parse(source)

        assert "a: int" in symbols[0].signature
        assert "b: str" in symbols[0].signature
        assert "c: bool" in symbols[0].signature

    def test_parse_function_with_args_kwargs(self, parser):
        source = '''
def func(*args, **kwargs):
    pass
'''
        symbols = parser.parse(source)

        assert "*args" in symbols[0].signature
        assert "**kwargs" in symbols[0].signature

    def test_parse_empty_file(self, parser):
        source = ""
        symbols = parser.parse(source)
        assert symbols == []

    def test_parse_file_with_only_comments(self, parser):
        source = '''
# This is a comment
# Another comment
"""Module docstring."""
'''
        symbols = parser.parse(source)
        assert symbols == []

    def test_parse_syntax_error(self, parser):
        source = '''
def broken(
    missing closing paren
'''
        with pytest.raises(SyntaxError):
            parser.parse(source)

    def test_symbol_to_dict(self, parser):
        source = '''
def example(x: int) -> str:
    """Example function."""
    pass
'''
        symbols = parser.parse(source)
        result = symbols[0].to_dict()

        assert result["name"] == "example"
        assert result["type"] == "function"
        assert result["lines"] == [2, 4]
        assert "signature" in result
        assert "docstring" in result

    def test_docstring_truncation(self, parser):
        source = '''
def long_doc():
    """This is a very long docstring that should be truncated because it exceeds the maximum length allowed by the system which is one hundred and fifty characters in total."""
    pass
'''
        symbols = parser.parse(source)
        result = symbols[0].to_dict()

        assert len(result["docstring"]) <= 150

    def test_can_parse_python_files(self, parser):
        assert parser.can_parse("test.py")
        assert parser.can_parse("path/to/module.py")
        assert parser.can_parse("types.pyi")
        assert not parser.can_parse("script.js")
        assert not parser.can_parse("module.ts")

    def test_parse_multiple_top_level_symbols(self, parser):
        source = '''
def func1():
    pass

class Class1:
    pass

def func2():
    pass

class Class2:
    pass
'''
        symbols = parser.parse(source)

        assert len(symbols) == 4
        assert symbols[0].name == "func1"
        assert symbols[1].name == "Class1"
        assert symbols[2].name == "func2"
        assert symbols[3].name == "Class2"
