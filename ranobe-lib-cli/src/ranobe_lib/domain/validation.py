from __future__ import annotations

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
from ranobe_lib.domain.model import CategoryName, Library, WorkKey
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok, Result


def validate_category_name(
    value: object,
) -> Result[CategoryName, InvalidCategoryName]:
    if not isinstance(value, str) or not value.strip():
        return Err(InvalidCategoryName(value))
    return Ok(value)


def validate_work_key(value: object) -> Result[WorkKey, InvalidWorkKey]:
    if not isinstance(value, str) or not value.strip():
        return Err(InvalidWorkKey(value))
    return Ok(value)


def validate_title(key: WorkKey, value: object) -> Result[str, InvalidTitle]:
    if not isinstance(value, str) or not value.strip():
        return Err(InvalidTitle(key=key, value=value))
    return Ok(value)


def validate_library(library: Library) -> Result[Library, DomainError]:
    """Validate whole-state invariants and return the original canonical value."""

    if not isinstance(library.categories, tuple):
        return Err(InvalidCategoriesCollection(library.categories))

    category_names: set[CategoryName] = set()
    titles_by_key: dict[WorkKey, str] = {}

    for category in library.categories:
        category_name_result = validate_category_name(category.name)
        if isinstance(category_name_result, Err):
            return category_name_result

        if category.name in category_names:
            return Err(DuplicateCategoryName(category.name))
        category_names.add(category.name)

        if not isinstance(category.items, tuple):
            return Err(
                InvalidItemsCollection(
                    category=category.name,
                    value=category.items,
                )
            )

        item_keys: set[WorkKey] = set()
        for item in category.items:
            key_result = validate_work_key(item.key)
            if isinstance(key_result, Err):
                return key_result

            if item.key in item_keys:
                return Err(DuplicateItemKey(category=category.name, key=item.key))
            item_keys.add(item.key)

            title_result = validate_title(item.key, item.title)
            if isinstance(title_result, Err):
                return title_result

            expected_title = titles_by_key.get(item.key)
            if expected_title is not None and expected_title != item.title:
                return Err(
                    ConflictingTitle(
                        key=item.key,
                        expected=expected_title,
                        actual=item.title,
                    )
                )
            titles_by_key[item.key] = item.title

            parts_result = normalize_parts(item.parts)
            if isinstance(parts_result, Err):
                return parts_result
            if parts_result.value != item.parts:
                return Err(
                    NonCanonicalParts(
                        category=category.name,
                        key=item.key,
                        actual=item.parts,
                        expected=parts_result.value,
                    )
                )

    return Ok(library)
