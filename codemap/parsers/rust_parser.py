"""Rust parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping


def _is_async_rust(node) -> bool:
    """Check if a Rust function is async."""
    for child in node.children:
        if child.type == "async":
            return True
    return False


RUST_CONFIG = LanguageConfig(
    name="rust",
    extensions=[".rs"],
    grammar_module="rust",
    node_mappings={
        "function_item": NodeMapping(
            symbol_type="function",
            name_child="identifier",
            signature_child="parameters",
            is_async_check=_is_async_rust,
        ),
        "struct_item": NodeMapping(
            symbol_type="struct",
            name_child="type_identifier",
            body_child="field_declaration_list",
        ),
        "enum_item": NodeMapping(
            symbol_type="enum",
            name_child="type_identifier",
            body_child="enum_variant_list",
        ),
        "trait_item": NodeMapping(
            symbol_type="trait",
            name_child="type_identifier",
            body_child="declaration_list",
        ),
        "impl_item": NodeMapping(
            symbol_type="impl",
            name_child="type_identifier",
            body_child="declaration_list",
        ),
        "mod_item": NodeMapping(
            symbol_type="module",
            name_child="identifier",
            body_child="declaration_list",
        ),
    },
    comment_types=["line_comment", "block_comment"],
    doc_comment_prefix="///",
)


class RustParser(TreeSitterParser):
    """Parser for Rust files using tree-sitter."""

    config = RUST_CONFIG
