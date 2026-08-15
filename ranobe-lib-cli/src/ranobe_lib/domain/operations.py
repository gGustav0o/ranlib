from __future__ import annotations

from dataclasses import replace

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    DomainError,
    MissingTitle,
    UnknownCategory,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import (
    validate_category_name,
    validate_library,
    validate_title,
    validate_work_key,
)


def add_parts(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
    title: object | None = None,
) -> Result[Library, DomainError]:
    """Add parts and return a new canonical library or an explicit error."""

    library_result = validate_library(library)
    if isinstance(library_result, Err):
        return library_result

    category_result = validate_category_name(category)
    if isinstance(category_result, Err):
        return category_result

    key_result = validate_work_key(key)
    if isinstance(key_result, Err):
        return key_result

    parts_result = normalize_parts(parts)
    if isinstance(parts_result, Err):
        return parts_result

    category_name = category_result.value
    work_key = key_result.value
    normalized_parts = parts_result.value

    provided_title: str | None = None
    if title is not None:
        title_result = validate_title(work_key, title)
        if isinstance(title_result, Err):
            return title_result
        provided_title = title_result.value

    target_index = _category_index(library, category_name)
    if target_index is None:
        return Err(UnknownCategory(category_name))

    existing_title = _title_for_key(library, work_key)
    if existing_title is None:
        if provided_title is None:
            return Err(MissingTitle(work_key))
        canonical_title = provided_title
    else:
        if provided_title is not None and provided_title != existing_title:
            return Err(
                ConflictingTitle(
                    key=work_key,
                    expected=existing_title,
                    actual=provided_title,
                )
            )
        canonical_title = existing_title

    target = library.categories[target_index]
    updated_target = _add_to_category(
        target,
        key=work_key,
        title=canonical_title,
        parts=normalized_parts,
    )
    if updated_target is target:
        return Ok(library)

    categories = (
        *library.categories[:target_index],
        updated_target,
        *library.categories[target_index + 1 :],
    )
    return Ok(replace(library, categories=categories))


def _category_index(library: Library, name: str) -> int | None:
    return next(
        (
            index
            for index, category in enumerate(library.categories)
            if category.name == name
        ),
        None,
    )


def _title_for_key(library: Library, key: str) -> str | None:
    return next(
        (
            item.title
            for category in library.categories
            for item in category.items
            if item.key == key
        ),
        None,
    )


def _add_to_category(
    category: Category,
    *,
    key: str,
    title: str,
    parts: tuple[int, ...],
) -> Category:
    for index, item in enumerate(category.items):
        if item.key != key:
            continue

        merged_parts = tuple(sorted(set(item.parts).union(parts)))
        if merged_parts == item.parts:
            return category

        items = (
            *category.items[:index],
            replace(item, parts=merged_parts),
            *category.items[index + 1 :],
        )
        return replace(category, items=items)

    item = Item(key=key, title=title, parts=parts)
    return replace(category, items=(*category.items, item))
