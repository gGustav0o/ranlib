from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


WorkKey: TypeAlias = str
CategoryName: TypeAlias = str
PartNumber: TypeAlias = int
Parts: TypeAlias = tuple[PartNumber, ...]


@dataclass(frozen=True, slots=True)
class Item:
    """A work and the canonical set of its parts in one category."""

    key: WorkKey
    title: str
    parts: Parts


@dataclass(frozen=True, slots=True)
class Category:
    """A fixed, ordered category of works."""

    name: CategoryName
    items: tuple[Item, ...] = ()


@dataclass(frozen=True, slots=True)
class Library:
    """The complete immutable library state."""

    categories: tuple[Category, ...] = ()
