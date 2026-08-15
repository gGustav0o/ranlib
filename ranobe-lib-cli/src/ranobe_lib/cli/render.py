from __future__ import annotations

from typing import assert_never

from ranobe_lib.cli.error_render import describe_error
from ranobe_lib.cli.errors import CliExecutionError, CliParseError
from ranobe_lib.cli.model import (
    CategoriesListed,
    CliOutput,
    CommandCompleted,
    ItemsListed,
)
from ranobe_lib.domain.model import Category, Item


def render_output(output: CliOutput) -> str:
    """Render a successful CLI value without writing to a stream."""

    if isinstance(output, CategoriesListed):
        return _with_final_newline("\n".join(output.names))
    if isinstance(output, ItemsListed):
        return _render_categories(output.categories)
    if isinstance(output, CommandCompleted):
        return "Done.\n"
    assert_never(output)


def render_parse_error(error: CliParseError) -> str:
    return f"{error.usage}ranobe-lib: error: {error.message}\n"


def render_execution_error(error: CliExecutionError) -> str:
    return f"error: {describe_error(error)}\n"


def _render_categories(categories: tuple[Category, ...]) -> str:
    text = "\n\n".join(_render_category(category) for category in categories)
    return _with_final_newline(text)


def _render_category(category: Category) -> str:
    lines = [f"{category.name}:"]
    if not category.items:
        lines.append("  (empty)")
    else:
        lines.extend(_render_item(item) for item in category.items)
    return "\n".join(lines)


def _render_item(item: Item) -> str:
    parts = ", ".join(str(part) for part in item.parts)
    return f"  {item.key} | {item.title} | volumes: {parts}"


def _with_final_newline(text: str) -> str:
    return "" if not text else f"{text}\n"


__all__ = ("render_execution_error", "render_output", "render_parse_error")
