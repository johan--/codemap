"""Python parser using stdlib ast module."""

from __future__ import annotations

import ast
from typing import Union

from .base import Parser, Symbol


class PythonParser(Parser):
    """Parser for Python files using stdlib ast module."""

    extensions = [".py", ".pyi"]
    language = "python"

    def parse(self, source: str, filepath: str = "") -> list[Symbol]:
        """Parse Python source code and extract symbols.

        Args:
            source: Python source code.
            filepath: Optional file path for error messages.

        Returns:
            List of top-level Symbol objects.

        Raises:
            SyntaxError: If the source code has syntax errors.
        """
        tree = ast.parse(source, filename=filepath or "<string>")
        return self._extract_symbols(tree.body)

    def _extract_symbols(self, nodes: list[ast.stmt]) -> list[Symbol]:
        """Extract symbols from AST nodes.

        Args:
            nodes: List of AST statement nodes.

        Returns:
            List of Symbol objects.
        """
        symbols = []
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                symbols.append(self._parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbol_type = (
                    "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
                )
                symbols.append(self._parse_function(node, symbol_type))
        return symbols

    def _parse_class(self, node: ast.ClassDef) -> Symbol:
        """Parse a class definition.

        Args:
            node: AST ClassDef node.

        Returns:
            Symbol representing the class.
        """
        children = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_type = (
                    "async_method" if isinstance(item, ast.AsyncFunctionDef) else "method"
                )
                children.append(self._parse_function(item, method_type))
            elif isinstance(item, ast.ClassDef):
                # Handle nested classes
                children.append(self._parse_class(item))

        # Include decorators in line range
        start_line = node.lineno
        if node.decorator_list:
            start_line = min(d.lineno for d in node.decorator_list)

        return Symbol(
            name=node.name,
            type="class",
            lines=(start_line, node.end_lineno or node.lineno),
            docstring=ast.get_docstring(node),
            children=children,
        )

    def _parse_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], symbol_type: str
    ) -> Symbol:
        """Parse a function or method definition.

        Args:
            node: AST FunctionDef or AsyncFunctionDef node.
            symbol_type: Type of symbol (function, method, async_function, async_method).

        Returns:
            Symbol representing the function/method.
        """
        # Include decorators in line range
        start_line = node.lineno
        if node.decorator_list:
            start_line = min(d.lineno for d in node.decorator_list)

        return Symbol(
            name=node.name,
            type=symbol_type,
            lines=(start_line, node.end_lineno or node.lineno),
            signature=self._get_signature(node),
            docstring=ast.get_docstring(node),
        )

    def _get_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Extract function signature.

        Args:
            node: AST function node.

        Returns:
            String representation of the function signature.
        """
        args = []

        # Handle positional-only args (Python 3.8+)
        for arg in node.args.posonlyargs:
            args.append(self._format_arg(arg))
        if node.args.posonlyargs:
            args.append("/")

        # Regular positional args
        num_defaults = len(node.args.defaults)
        num_args = len(node.args.args)
        for i, arg in enumerate(node.args.args):
            arg_str = self._format_arg(arg)
            # Check if this arg has a default value
            default_idx = i - (num_args - num_defaults)
            if default_idx >= 0:
                default = node.args.defaults[default_idx]
                arg_str += f"={self._format_default(default)}"
            args.append(arg_str)

        # *args
        if node.args.vararg:
            args.append(f"*{self._format_arg(node.args.vararg)}")
        elif node.args.kwonlyargs:
            args.append("*")

        # Keyword-only args
        for i, arg in enumerate(node.args.kwonlyargs):
            arg_str = self._format_arg(arg)
            if i < len(node.args.kw_defaults) and node.args.kw_defaults[i] is not None:
                arg_str += f"={self._format_default(node.args.kw_defaults[i])}"
            args.append(arg_str)

        # **kwargs
        if node.args.kwarg:
            args.append(f"**{self._format_arg(node.args.kwarg)}")

        sig = f"({', '.join(args)})"

        # Return type
        if node.returns:
            try:
                sig += f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass

        return sig

    def _format_arg(self, arg: ast.arg) -> str:
        """Format a function argument.

        Args:
            arg: AST arg node.

        Returns:
            String representation of the argument.
        """
        if arg.annotation:
            try:
                return f"{arg.arg}: {ast.unparse(arg.annotation)}"
            except Exception:
                return arg.arg
        return arg.arg

    def _format_default(self, node: ast.expr) -> str:
        """Format a default value.

        Args:
            node: AST expression node.

        Returns:
            String representation of the default value.
        """
        try:
            result = ast.unparse(node)
            # Truncate very long defaults
            if len(result) > 20:
                return "..."
            return result
        except Exception:
            return "..."
