from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TypeVar

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    DomainError,
    MissingTitle,
    UnknownCategory,
)
from ranobe_lib.domain.model import (
    Category,
    CategoryName,
    Item,
    Library,
    Parts,
    WorkKey,
)
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import (
    validate_category_name,
    validate_title,
    validate_work_key,
)


ReplacementT = TypeVar("ReplacementT")


@dataclass(frozen=True, slots=True)
class _AddPartsInput:
    category: CategoryName
    key: WorkKey
    parts: Parts
    title: str | None


@dataclass(frozen=True, slots=True)
class _PreparedAddition:
    category_index: int
    key: WorkKey
    parts: Parts
    title: str


def add_parts(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
    title: object | None = None,
) -> Result[Library, DomainError]:
    """Add parts to a canonical library without mutating it."""

    prepared_result = _prepare_addition(
        library,
        category=category,
        key=key,
        parts=parts,
        title=title,
    )
    if isinstance(prepared_result, Err):
        return prepared_result
    return Ok(_apply_addition(library, prepared_result.value))


def _prepare_addition(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
    title: object | None,
) -> Result[_PreparedAddition, DomainError]:
    input_result = _validate_add_parts_input(
        category=category,
        key=key,
        parts=parts,
        title=title,
    )
    if isinstance(input_result, Err):
        return input_result
    return _resolve_addition(library, input_result.value)


def _validate_add_parts_input(
    *,
    category: object,
    key: object,
    parts: object,
    title: object | None,
) -> Result[_AddPartsInput, DomainError]:
    identity_result = _validate_identity(category=category, key=key)
    if isinstance(identity_result, Err):
        return identity_result
    return _validate_add_parts_details(identity_result.value, parts, title)


def _validate_add_parts_details(
    identity: tuple[CategoryName, WorkKey],
    parts: object,
    title: object | None,
) -> Result[_AddPartsInput, DomainError]:
    category_name, work_key = identity

    parts_result = normalize_parts(parts)
    if isinstance(parts_result, Err):
        return parts_result

    return _build_add_parts_input(
        category=category_name,
        key=work_key,
        parts=parts_result.value,
        title=title,
    )


def _build_add_parts_input(
    *,
    category: CategoryName,
    key: WorkKey,
    parts: Parts,
    title: object | None,
) -> Result[_AddPartsInput, DomainError]:
    title_result = _validate_optional_title(key, title)
    if isinstance(title_result, Err):
        return title_result

    return Ok(
        _AddPartsInput(
            category=category,
            key=key,
            parts=parts,
            title=title_result.value,
        )
    )


def _validate_identity(
    *,
    category: object,
    key: object,
) -> Result[tuple[CategoryName, WorkKey], DomainError]:
    category_result = validate_category_name(category)
    if isinstance(category_result, Err):
        return category_result

    key_result = validate_work_key(key)
    if isinstance(key_result, Err):
        return key_result

    return Ok((category_result.value, key_result.value))


def _validate_optional_title(
    key: WorkKey,
    title: object | None,
) -> Result[str | None, DomainError]:
    if title is None:
        return Ok(None)
    return validate_title(key, title)


def _resolve_addition(
    library: Library,
    addition: _AddPartsInput,
) -> Result[_PreparedAddition, DomainError]:
    category_result = _find_category_index(library, addition.category)
    if isinstance(category_result, Err):
        return category_result

    title_result = _resolve_title(library, addition.key, addition.title)
    if isinstance(title_result, Err):
        return title_result

    return Ok(
        _PreparedAddition(
            category_index=category_result.value,
            key=addition.key,
            parts=addition.parts,
            title=title_result.value,
        )
    )


def _find_category_index(
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


def _resolve_title(
    library: Library,
    key: WorkKey,
    provided: str | None,
) -> Result[str, MissingTitle | ConflictingTitle]:
    existing = _title_for_key(library, key)
    if existing is None:
        return _require_new_title(key, provided)
    if provided is not None and provided != existing:
        return Err(
            ConflictingTitle(
                key=key,
                expected=existing,
                actual=provided,
            )
        )
    return Ok(existing)


def _require_new_title(
    key: WorkKey,
    provided: str | None,
) -> Result[str, MissingTitle]:
    if provided is None:
        return Err(MissingTitle(key))
    return Ok(provided)


def _title_for_key(library: Library, key: WorkKey) -> str | None:
    return next(
        (
            item.title
            for category in library.categories
            for item in category.items
            if item.key == key
        ),
        None,
    )


def _apply_addition(
    library: Library,
    addition: _PreparedAddition,
) -> Library:
    category = library.categories[addition.category_index]
    updated = _upsert_item(category, addition)
    if updated is category:
        return library
    return _replace_category(library, addition.category_index, updated)


def _upsert_item(
    category: Category,
    addition: _PreparedAddition,
) -> Category:
    index = _item_index(category, addition.key)
    if index is None:
        return _append_item(category, addition)
    return _merge_item_parts(category, index, addition.parts)


def _item_index(category: Category, key: WorkKey) -> int | None:
    return next(
        (
            index
            for index, item in enumerate(category.items)
            if item.key == key
        ),
        None,
    )


def _append_item(category: Category, addition: _PreparedAddition) -> Category:
    item = Item(
        key=addition.key,
        title=addition.title,
        parts=addition.parts,
    )
    return replace(category, items=(*category.items, item))


def _merge_item_parts(
    category: Category,
    item_index: int,
    parts: Parts,
) -> Category:
    item = category.items[item_index]
    merged_parts = _merge_parts(item.parts, parts)
    if merged_parts == item.parts:
        return category

    updated_item = replace(item, parts=merged_parts)
    items = _replace_at(category.items, item_index, updated_item)
    return replace(category, items=items)


def _merge_parts(existing: Parts, added: Parts) -> Parts:
    return tuple(sorted(set(existing).union(added)))


def _replace_category(
    library: Library,
    index: int,
    category: Category,
) -> Library:
    categories = _replace_at(library.categories, index, category)
    return replace(library, categories=categories)


def _replace_at(
    values: tuple[ReplacementT, ...],
    index: int,
    value: ReplacementT,
) -> tuple[ReplacementT, ...]:
    return (*values[:index], value, *values[index + 1 :])
