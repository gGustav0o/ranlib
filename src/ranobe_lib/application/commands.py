# src/ranobe_lib/application/commands.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from ranobe_lib.domain.model import CategoryName, Parts, WorkKey


@dataclass(frozen=True, slots=True)
class ListCategories:
    """Request the list of available categories."""


@dataclass(frozen=True, slots=True)
class ListItems:
    """
    Request items from selected categories.

    None means that items from all categories are requested.
    """

    categories: tuple[CategoryName, ...] | None = None


@dataclass(frozen=True, slots=True)
class SearchItems:
    """Request items whose key or title contains the search text."""

    text: str
    categories: tuple[CategoryName, ...] | None = None


@dataclass(frozen=True, slots=True)
class AddParts:
    """
    Add parts of a work to a category.

    `title` is required only when `key` refers to a work that does not
    yet exist in the library.

    `parts` intentionally preserves the original sequence, including
    duplicates. Normalization belongs to the domain layer.
    """

    key: WorkKey
    parts: Parts
    category: CategoryName
    title: str | None = None


@dataclass(frozen=True, slots=True)
class RemoveParts:
    """Remove selected parts of a work from a category."""

    key: WorkKey
    parts: Parts
    category: CategoryName


@dataclass(frozen=True, slots=True)
class RemoveItem:
    """Remove the whole work entry from a category."""

    key: WorkKey
    category: CategoryName


@dataclass(frozen=True, slots=True)
class MoveParts:
    """Move selected parts of a work between categories."""

    key: WorkKey
    parts: Parts
    source: CategoryName
    destination: CategoryName


Command: TypeAlias = (
    ListCategories
    | ListItems
    | SearchItems
    | AddParts
    | RemoveParts
    | RemoveItem
    | MoveParts
)
