from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TypeVar

from ranobe_lib.domain.errors import UnknownCategory, UnknownItem
from ranobe_lib.domain.model import (
    Category,
    CategoryName,
    Library,
    Parts,
    WorkKey,
)
from ranobe_lib.domain.result import Err, Ok, Result


ReplacementT = TypeVar("ReplacementT")


@dataclass(frozen=True, slots=True)
class ItemLocation:
    category_index: int
    item_index: int


def find_category_index(
    library: Library,
    name: CategoryName,
) -> Result[int, UnknownCategory]:
    index = next(
        (
            index
            for index, category in enumerate(library.categories)
            if category.name == name
        ),
        None,
    )
    if index is None:
        return Err(UnknownCategory(name))
    return Ok(index)


def find_item_location(
    library: Library,
    category: CategoryName,
    key: WorkKey,
) -> Result[ItemLocation, UnknownCategory | UnknownItem]:
    category_result = find_category_index(library, category)
    if isinstance(category_result, Err):
        return category_result

    category_index = category_result.value
    item_result = find_item_index(library.categories[category_index], key)
    if isinstance(item_result, Err):
        return item_result
    return Ok(ItemLocation(category_index, item_result.value))


def find_item_index(
    category: Category,
    key: WorkKey,
) -> Result[int, UnknownItem]:
    index = item_index(category, key)
    if index is None:
        return Err(UnknownItem(category.name, key))
    return Ok(index)


def item_index(category: Category, key: WorkKey) -> int | None:
    return next(
        (
            index
            for index, item in enumerate(category.items)
            if item.key == key
        ),
        None,
    )


def title_for_key(library: Library, key: WorkKey) -> str | None:
    return next(
        (
            item.title
            for category in library.categories
            for item in category.items
            if item.key == key
        ),
        None,
    )


def merge_parts(existing: Parts, added: Parts) -> Parts:
    return tuple(sorted(set(existing).union(added)))


def missing_parts(existing: Parts, requested: Parts) -> Parts:
    available = set(existing)
    return tuple(part for part in requested if part not in available)


def subtract_parts(existing: Parts, removed: Parts) -> Parts:
    removed_set = set(removed)
    return tuple(part for part in existing if part not in removed_set)


def replace_category(library: Library, index: int, category: Category) -> Library:
    categories = replace_at(library.categories, index, category)
    return replace(library, categories=categories)


def replace_at(
    values: tuple[ReplacementT, ...],
    index: int,
    value: ReplacementT,
) -> tuple[ReplacementT, ...]:
    return (*values[:index], value, *values[index + 1 :])


def remove_at(
    values: tuple[ReplacementT, ...],
    index: int,
) -> tuple[ReplacementT, ...]:
    return (*values[:index], *values[index + 1 :])
