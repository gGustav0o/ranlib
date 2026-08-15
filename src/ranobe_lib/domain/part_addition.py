from __future__ import annotations

from dataclasses import dataclass, replace

from ranobe_lib.domain._library_edit import (
    find_category_index,
    item_index,
    merge_parts,
    replace_at,
    replace_category,
    title_for_key,
)
from ranobe_lib.domain._operation_inputs import PartsInput, validate_parts_input
from ranobe_lib.domain.errors import ConflictingTitle, DomainError, MissingTitle
from ranobe_lib.domain.model import Category, Item, Library, Parts, WorkKey
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import validate_title


@dataclass(frozen=True, slots=True)
class _AddPartsInput:
    request: PartsInput
    title: str | None


@dataclass(frozen=True, slots=True)
class PreparedAddition:
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
    return Ok(apply_addition(library, prepared_result.value))


def _prepare_addition(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
    title: object | None,
) -> Result[PreparedAddition, DomainError]:
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
    input_result = validate_parts_input(category=category, key=key, parts=parts)
    if isinstance(input_result, Err):
        return input_result
    return _attach_optional_title(input_result.value, title)


def _attach_optional_title(
    request: PartsInput,
    title: object | None,
) -> Result[_AddPartsInput, DomainError]:
    title_result = _validate_optional_title(request.key, title)
    if isinstance(title_result, Err):
        return title_result
    return Ok(_AddPartsInput(request, title_result.value))


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
) -> Result[PreparedAddition, DomainError]:
    category_result = find_category_index(library, addition.request.category)
    if isinstance(category_result, Err):
        return category_result

    title_result = _resolve_title(library, addition.request.key, addition.title)
    if isinstance(title_result, Err):
        return title_result
    prepared = _build_prepared_addition(
        category_result.value,
        addition,
        title_result.value,
    )
    return Ok(prepared)


def _build_prepared_addition(
    category_index: int,
    addition: _AddPartsInput,
    title: str,
) -> PreparedAddition:
    return PreparedAddition(
        category_index=category_index,
        key=addition.request.key,
        parts=addition.request.parts,
        title=title,
    )


def _resolve_title(
    library: Library,
    key: WorkKey,
    provided: str | None,
) -> Result[str, MissingTitle | ConflictingTitle]:
    existing = title_for_key(library, key)
    if existing is None:
        return _require_new_title(key, provided)
    if provided is not None and provided != existing:
        return Err(ConflictingTitle(key, existing, provided))
    return Ok(existing)


def _require_new_title(
    key: WorkKey,
    provided: str | None,
) -> Result[str, MissingTitle]:
    if provided is None:
        return Err(MissingTitle(key))
    return Ok(provided)


def apply_addition(library: Library, addition: PreparedAddition) -> Library:
    category = library.categories[addition.category_index]
    updated = _upsert_item(category, addition)
    if updated is category:
        return library
    return replace_category(library, addition.category_index, updated)


def _upsert_item(category: Category, addition: PreparedAddition) -> Category:
    index = item_index(category, addition.key)
    if index is None:
        return _append_item(category, addition)
    return _merge_item_parts(category, index, addition.parts)


def _append_item(category: Category, addition: PreparedAddition) -> Category:
    item = Item(addition.key, addition.title, addition.parts)
    return replace(category, items=(*category.items, item))


def _merge_item_parts(
    category: Category,
    item_index: int,
    parts: Parts,
) -> Category:
    item = category.items[item_index]
    merged = merge_parts(item.parts, parts)
    if merged == item.parts:
        return category

    updated_item = replace(item, parts=merged)
    return replace(category, items=replace_at(category.items, item_index, updated_item))


__all__ = ("add_parts",)
