from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import TypeVar

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    DomainError,
    DuplicateCategoryName,
    DuplicateItemKey,
    InvalidCategoriesCollection,
    InvalidCategoryName,
    InvalidItemsCollection,
    InvalidTitle,
    InvalidWorkKey,
    NonCanonicalParts,
)
from ranobe_lib.domain.model import (
    Category,
    CategoryName,
    Item,
    Library,
    WorkKey,
)
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok, Result, sequence_checks


StringErrorT = TypeVar("StringErrorT", bound=DomainError)


def validate_category_name(
    value: object,
) -> Result[CategoryName, InvalidCategoryName]:
    return _validate_non_blank_string(value, InvalidCategoryName)


def validate_work_key(value: object) -> Result[WorkKey, InvalidWorkKey]:
    return _validate_non_blank_string(value, InvalidWorkKey)


def validate_title(key: WorkKey, value: object) -> Result[str, InvalidTitle]:
    return _validate_non_blank_string(
        value,
        lambda invalid: InvalidTitle(key=key, value=invalid),
    )


def validate_library(library: Library) -> Result[Library, DomainError]:
    """Validate a library at a construction or decoding boundary."""

    validation_result = _validate_library_categories(library.categories)
    if isinstance(validation_result, Err):
        return validation_result
    return Ok(library)


def _validate_library_categories(value: object) -> Result[None, DomainError]:
    categories_result = _validate_categories_collection(value)
    if isinstance(categories_result, Err):
        return categories_result

    categories = categories_result.value
    validators = (
        _validate_category_names,
        _validate_unique_category_names,
        _validate_categories,
        _validate_global_titles,
    )
    return sequence_checks(
        validate(categories) for validate in validators
    )


def _validate_non_blank_string(
    value: object,
    error: Callable[[object], StringErrorT],
) -> Result[str, StringErrorT]:
    if not isinstance(value, str) or not value.strip():
        return Err(error(value))
    return Ok(value)


def _validate_categories_collection(
    value: object,
) -> Result[tuple[Category, ...], InvalidCategoriesCollection]:
    if not isinstance(value, tuple):
        return Err(InvalidCategoriesCollection(value))
    return Ok(value)


def _validate_category_names(
    categories: tuple[Category, ...],
) -> Result[None, DomainError]:
    return sequence_checks(
        validate_category_name(category.name) for category in categories
    )


def _validate_unique_category_names(
    categories: tuple[Category, ...],
) -> Result[None, DuplicateCategoryName]:
    duplicate = _find_duplicate(category.name for category in categories)
    if duplicate is not None:
        return Err(DuplicateCategoryName(duplicate))
    return Ok(None)


def _validate_categories(
    categories: tuple[Category, ...],
) -> Result[None, DomainError]:
    return sequence_checks(_validate_category(category) for category in categories)


def _validate_category(category: Category) -> Result[None, DomainError]:
    items_result = _validate_items_collection(category)
    if isinstance(items_result, Err):
        return items_result

    validators = (_validate_items, _validate_unique_item_keys)
    return sequence_checks(validate(category) for validate in validators)


def _validate_items_collection(
    category: Category,
) -> Result[tuple[Item, ...], InvalidItemsCollection]:
    if not isinstance(category.items, tuple):
        return Err(
            InvalidItemsCollection(
                category=category.name,
                value=category.items,
            )
        )
    return Ok(category.items)


def _validate_items(category: Category) -> Result[None, DomainError]:
    return sequence_checks(
        _validate_item(category.name, item) for item in category.items
    )


def _validate_item(
    category: CategoryName,
    item: Item,
) -> Result[None, DomainError]:
    key_result = validate_work_key(item.key)
    if isinstance(key_result, Err):
        return key_result

    title_result = validate_title(item.key, item.title)
    if isinstance(title_result, Err):
        return title_result

    return _validate_canonical_parts(category, item)


def _validate_canonical_parts(
    category: CategoryName,
    item: Item,
) -> Result[None, DomainError]:
    parts_result = normalize_parts(item.parts)
    if isinstance(parts_result, Err):
        return parts_result
    if parts_result.value == item.parts:
        return Ok(None)
    return Err(
        NonCanonicalParts(
            category=category,
            key=item.key,
            actual=item.parts,
            expected=parts_result.value,
        )
    )


def _validate_unique_item_keys(
    category: Category,
) -> Result[None, DuplicateItemKey]:
    duplicate = _find_duplicate(item.key for item in category.items)
    if duplicate is not None:
        return Err(DuplicateItemKey(category=category.name, key=duplicate))
    return Ok(None)


def _validate_global_titles(
    categories: tuple[Category, ...],
) -> Result[None, ConflictingTitle]:
    titles_by_key: dict[WorkKey, str] = {}
    for item in _all_items(categories):
        expected_title = titles_by_key.setdefault(item.key, item.title)
        if expected_title != item.title:
            return Err(
                ConflictingTitle(
                    key=item.key,
                    expected=expected_title,
                    actual=item.title,
                )
            )
    return Ok(None)


def _all_items(categories: tuple[Category, ...]) -> Iterator[Item]:
    return (
        item
        for category in categories
        for item in category.items
    )


def _find_duplicate(values: Iterable[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
