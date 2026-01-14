"""Java parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


JAVA_CONFIG = LanguageConfig(
    name="java",
    extensions=[".java"],
    grammar_module="java",
    node_mappings={
        "class_declaration": NodeMapping(
            symbol_type="class",
            name_child="identifier",
            body_child="class_body",
        ),
        "interface_declaration": NodeMapping(
            symbol_type="interface",
            name_child="identifier",
            body_child="interface_body",
        ),
        "enum_declaration": NodeMapping(
            symbol_type="enum",
            name_child="identifier",
            body_child="enum_body",
        ),
        "method_declaration": NodeMapping(
            symbol_type="method",
            name_child="identifier",
            signature_child="formal_parameters",
        ),
        "constructor_declaration": NodeMapping(
            symbol_type="method",
            name_child="identifier",
            signature_child="formal_parameters",
        ),
    },
    comment_types=["block_comment", "line_comment"],
    doc_comment_prefix="/**",
)


class JavaParser(TreeSitterParser):
    """Parser for Java files using tree-sitter."""

    config = JAVA_CONFIG
