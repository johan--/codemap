"""Go parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


def _is_async(node) -> bool:
    """Go doesn't have async, but goroutines could be detected."""
    return False


GO_CONFIG = LanguageConfig(
    name="go",
    extensions=[".go"],
    grammar_module="go",
    node_mappings={
        "function_declaration": NodeMapping(
            symbol_type="function",
            name_child="identifier",
            signature_child="parameter_list",
        ),
        "method_declaration": NodeMapping(
            symbol_type="method",
            name_child="field_identifier",
            signature_child="parameter_list",
        ),
        "type_declaration": NodeMapping(
            symbol_type="type",
            name_child="type_spec",
        ),
        "type_spec": NodeMapping(
            symbol_type="type",
            name_child="type_identifier",
            body_child="struct_type",  # For struct fields
        ),
        "struct_type": NodeMapping(
            symbol_type="struct",
            name_child="type_identifier",
            body_child="field_declaration_list",
        ),
        "interface_type": NodeMapping(
            symbol_type="interface",
            name_child="type_identifier",
            body_child="method_spec_list",
        ),
    },
    comment_types=["comment"],
)


class GoParser(TreeSitterParser):
    """Parser for Go files using tree-sitter."""

    config = GO_CONFIG
