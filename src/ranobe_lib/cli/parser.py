from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from ranobe_lib.application.commands import (
    AddParts,
    Command,
    ListCategories,
    ListItems,
    MoveParts,
    RemoveItem,
    RemoveParts,
    SearchItems,
)
from ranobe_lib.cli.errors import CliParseError
from ranobe_lib.cli.model import HelpRequested, Invocation, ParsedInvocation
from ranobe_lib.domain.result import Err, Ok, Result


_DEFAULT_LIBRARY_PATH = Path("ranobe-lib.json")
_CommandBuilder = Callable[[argparse.Namespace], Command]


class _Subparsers(Protocol):
    def add_parser(
        self,
        name: str,
        **kwargs: object,
    ) -> argparse.ArgumentParser: ...


class _HelpSignal(Exception):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__(text)


class _ParseSignal(Exception):
    def __init__(self, message: str, usage: str) -> None:
        self.message = message
        self.usage = usage
        super().__init__(message)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _ParseSignal(message, self.format_usage())

    def exit(self, status: int = 0, message: str | None = None) -> None:
        raise _ParseSignal(message or "argument parsing stopped", self.format_usage())


class _HelpAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        raise _HelpSignal(parser.format_help())


def parse_invocation(
    arguments: Sequence[str],
) -> Result[ParsedInvocation, CliParseError]:
    """Parse CLI arguments without writing output or terminating the process."""

    parser = _build_parser()
    try:
        namespace = parser.parse_args(tuple(arguments))
        return Ok(_build_invocation(namespace))
    except _HelpSignal as signal:
        return Ok(HelpRequested(signal.text))
    except _ParseSignal as signal:
        return Err(CliParseError(signal.message, signal.usage))


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="ranobe-lib",
        description="Manage categorized ranobe volumes in a JSON file.",
        add_help=False,
        allow_abbrev=False,
    )
    _add_help(parser)
    parser.add_argument(
        "--file",
        dest="library_path",
        type=Path,
        default=_DEFAULT_LIBRARY_PATH,
        help="library JSON path (default: ranobe-lib.json)",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)
    _add_commands(subparsers)
    return parser


def _add_commands(subparsers: _Subparsers) -> None:
    _add_list_categories(subparsers)
    _add_list_items(subparsers)
    _add_search_items(subparsers)
    _add_add_parts(subparsers)
    _add_remove_parts(subparsers)
    _add_remove_item(subparsers)
    _add_move_parts(subparsers)


def _add_command(
    subparsers: _Subparsers,
    name: str,
    description: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name,
        help=description,
        description=description,
        add_help=False,
        allow_abbrev=False,
    )
    _add_help(parser)
    return parser


def _add_help(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-h",
        "--help",
        action=_HelpAction,
        nargs=0,
        help="show this help message and exit",
    )


def _add_list_categories(subparsers: _Subparsers) -> None:
    _add_command(subparsers, "list-categories", "List category names.")


def _add_list_items(subparsers: _Subparsers) -> None:
    parser = _add_command(subparsers, "list-items", "List categorized items.")
    _add_category_selection(parser)


def _add_search_items(subparsers: _Subparsers) -> None:
    parser = _add_command(
        subparsers,
        "search-items",
        "Search categorized items by key or title.",
    )
    parser.add_argument("text", metavar="TEXT", help="substring to find")
    _add_category_selection(parser)


def _add_category_selection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-c",
        "--category",
        dest="categories",
        action="append",
        metavar="NAME",
        help="category to include; repeat to select several",
    )


def _add_add_parts(subparsers: _Subparsers) -> None:
    parser = _add_command(subparsers, "add-parts", "Add volumes to an item.")
    _add_category_and_key(parser)
    parser.add_argument("--title", help="title required for a new key")
    _add_parts(parser)


def _add_remove_parts(subparsers: _Subparsers) -> None:
    parser = _add_command(
        subparsers,
        "remove-parts",
        "Remove volumes from an item.",
    )
    _add_category_and_key(parser)
    _add_parts(parser)


def _add_remove_item(subparsers: _Subparsers) -> None:
    parser = _add_command(subparsers, "remove-item", "Remove one item entry.")
    _add_category_and_key(parser)


def _add_move_parts(subparsers: _Subparsers) -> None:
    parser = _add_command(
        subparsers,
        "move-parts",
        "Move volumes between categories.",
    )
    parser.add_argument("--source", required=True, metavar="NAME")
    parser.add_argument("--destination", required=True, metavar="NAME")
    parser.add_argument("--key", required=True, metavar="KEY")
    _add_parts(parser)


def _add_category_and_key(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--category", required=True, metavar="NAME")
    parser.add_argument("--key", required=True, metavar="KEY")


def _add_parts(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "parts",
        nargs="+",
        type=int,
        metavar="PART",
        help="one or more volume numbers",
    )


def _build_invocation(namespace: argparse.Namespace) -> Invocation:
    builder = _COMMAND_BUILDERS[namespace.command_name]
    return Invocation(namespace.library_path, builder(namespace))


def _build_list_categories(namespace: argparse.Namespace) -> Command:
    return ListCategories()


def _build_list_items(namespace: argparse.Namespace) -> Command:
    return ListItems(_selected_categories(namespace))


def _build_search_items(namespace: argparse.Namespace) -> Command:
    return SearchItems(
        text=namespace.text,
        categories=_selected_categories(namespace),
    )


def _selected_categories(
    namespace: argparse.Namespace,
) -> tuple[str, ...] | None:
    categories = namespace.categories
    return None if categories is None else tuple(categories)


def _build_add_parts(namespace: argparse.Namespace) -> Command:
    return AddParts(
        key=namespace.key,
        parts=tuple(namespace.parts),
        category=namespace.category,
        title=namespace.title,
    )


def _build_remove_parts(namespace: argparse.Namespace) -> Command:
    return RemoveParts(
        key=namespace.key,
        parts=tuple(namespace.parts),
        category=namespace.category,
    )


def _build_remove_item(namespace: argparse.Namespace) -> Command:
    return RemoveItem(key=namespace.key, category=namespace.category)


def _build_move_parts(namespace: argparse.Namespace) -> Command:
    return MoveParts(
        key=namespace.key,
        parts=tuple(namespace.parts),
        source=namespace.source,
        destination=namespace.destination,
    )


_COMMAND_BUILDERS: dict[str, _CommandBuilder] = {
    "list-categories": _build_list_categories,
    "list-items": _build_list_items,
    "search-items": _build_search_items,
    "add-parts": _build_add_parts,
    "remove-parts": _build_remove_parts,
    "remove-item": _build_remove_item,
    "move-parts": _build_move_parts,
}


__all__ = ("parse_invocation",)
