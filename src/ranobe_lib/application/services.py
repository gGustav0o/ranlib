from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TypeVar

from ranobe_lib.application.commands import (
    AddParts,
    ListItems,
    MoveParts,
    RemoveItem,
    RemoveParts,
    SearchItems,
)
from ranobe_lib.application.ports import LoadLibrary, SaveLibrary
from ranobe_lib.domain.errors import DomainError
from ranobe_lib.domain.model import Category, CategoryName, Library
from ranobe_lib.domain.operations import (
    add_parts as add_domain_parts,
    move_parts as move_domain_parts,
    remove_item as remove_domain_item,
    remove_parts as remove_domain_parts,
)
from ranobe_lib.domain.queries import list_category_names, select_categories
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.search import (
    CategoryMatches,
    search_items as search_domain_items,
)


ValueT = TypeVar("ValueT")
LoadErrorT = TypeVar("LoadErrorT")
SaveErrorT = TypeVar("SaveErrorT")
QueryErrorT = TypeVar("QueryErrorT")
TransitionErrorT = TypeVar("TransitionErrorT")


def list_categories(
    *,
    load: LoadLibrary[LoadErrorT],
) -> Result[tuple[CategoryName, ...], LoadErrorT]:
    """Load the library and return category names in canonical order."""

    return _read_library(load, list_category_names)


def list_items(
    command: ListItems,
    *,
    load: LoadLibrary[LoadErrorT],
) -> Result[tuple[Category, ...], LoadErrorT | DomainError]:
    """Load and select categories without flattening their items."""

    query = partial(select_categories, categories=command.categories)
    return _query_library(load, query)


def search_items(
    command: SearchItems,
    *,
    load: LoadLibrary[LoadErrorT],
) -> Result[tuple[CategoryMatches, ...], LoadErrorT | DomainError]:
    """Load the library and find matching items in selected categories."""

    query = partial(
        search_domain_items,
        text=command.text,
        categories=command.categories,
    )
    return _query_library(load, query)


def add_parts(
    command: AddParts,
    *,
    load: LoadLibrary[LoadErrorT],
    save: SaveLibrary[SaveErrorT],
) -> Result[Library, LoadErrorT | DomainError | SaveErrorT]:
    transition = partial(
        add_domain_parts,
        category=command.category,
        key=command.key,
        parts=command.parts,
        title=command.title,
    )
    return _update_library(load, save, transition)


def remove_parts(
    command: RemoveParts,
    *,
    load: LoadLibrary[LoadErrorT],
    save: SaveLibrary[SaveErrorT],
) -> Result[Library, LoadErrorT | DomainError | SaveErrorT]:
    transition = partial(
        remove_domain_parts,
        category=command.category,
        key=command.key,
        parts=command.parts,
    )
    return _update_library(load, save, transition)


def remove_item(
    command: RemoveItem,
    *,
    load: LoadLibrary[LoadErrorT],
    save: SaveLibrary[SaveErrorT],
) -> Result[Library, LoadErrorT | DomainError | SaveErrorT]:
    transition = partial(
        remove_domain_item,
        category=command.category,
        key=command.key,
    )
    return _update_library(load, save, transition)


def move_parts(
    command: MoveParts,
    *,
    load: LoadLibrary[LoadErrorT],
    save: SaveLibrary[SaveErrorT],
) -> Result[Library, LoadErrorT | DomainError | SaveErrorT]:
    transition = partial(
        move_domain_parts,
        source=command.source,
        destination=command.destination,
        key=command.key,
        parts=command.parts,
    )
    return _update_library(load, save, transition)


def _read_library(
    load: LoadLibrary[LoadErrorT],
    query: Callable[[Library], ValueT],
) -> Result[ValueT, LoadErrorT]:
    library_result = load()
    if isinstance(library_result, Err):
        return library_result
    return Ok(query(library_result.value))


def _query_library(
    load: LoadLibrary[LoadErrorT],
    query: Callable[[Library], Result[ValueT, QueryErrorT]],
) -> Result[ValueT, LoadErrorT | QueryErrorT]:
    library_result = load()
    if isinstance(library_result, Err):
        return library_result
    return query(library_result.value)


def _update_library(
    load: LoadLibrary[LoadErrorT],
    save: SaveLibrary[SaveErrorT],
    transition: Callable[[Library], Result[Library, TransitionErrorT]],
) -> Result[Library, LoadErrorT | TransitionErrorT | SaveErrorT]:
    library_result = load()
    if isinstance(library_result, Err):
        return library_result
    return _transition_and_save(library_result.value, save, transition)


def _transition_and_save(
    library: Library,
    save: SaveLibrary[SaveErrorT],
    transition: Callable[[Library], Result[Library, TransitionErrorT]],
) -> Result[Library, TransitionErrorT | SaveErrorT]:
    updated_result = transition(library)
    if isinstance(updated_result, Err):
        return updated_result
    if updated_result.value is library:
        return updated_result
    return _save_updated_library(updated_result.value, save)


def _save_updated_library(
    library: Library,
    save: SaveLibrary[SaveErrorT],
) -> Result[Library, SaveErrorT]:
    saved_result = save(library)
    if isinstance(saved_result, Err):
        return saved_result
    return Ok(library)


__all__ = (
    "add_parts",
    "list_categories",
    "list_items",
    "move_parts",
    "remove_item",
    "remove_parts",
    "search_items",
)
