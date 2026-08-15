from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TypeVar

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    DomainError,
    MissingParts,
    MissingTitle,
    SameCategoryMove,
    UnknownCategory,
    UnknownItem,
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
class _PartsInput:
    category: CategoryName
    key: WorkKey
    parts: Parts


@dataclass(frozen=True, slots=True)
class _AddPartsInput(_PartsInput):
    title: str | None


@dataclass(frozen=True, slots=True)
class _PreparedAddition:
    category_index: int
    key: WorkKey
    parts: Parts
    title: str


@dataclass(frozen=True, slots=True)
class _PreparedRemoval:
    category_index: int
    item_index: int
    item: Item
    parts: Parts
    remaining_parts: Parts


@dataclass(frozen=True, slots=True)
class _MovePartsInput:
    source: _PartsInput
    destination: CategoryName


@dataclass(frozen=True, slots=True)
class _PreparedMove:
    removal: _PreparedRemoval
    destination_index: int


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


def remove_parts(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
) -> Result[Library, DomainError]:
    """Remove all requested parts from a canonical immutable library."""

    prepared_result = _prepare_removal(
        library,
        category=category,
        key=key,
        parts=parts,
    )
    if isinstance(prepared_result, Err):
        return prepared_result
    return Ok(_apply_removal(library, prepared_result.value))


def move_parts(
    library: Library,
    *,
    source: object,
    destination: object,
    key: object,
    parts: object,
) -> Result[Library, DomainError]:
    """Move all requested parts between categories as one pure operation."""

    prepared_result = _prepare_move(
        library,
        source=source,
        destination=destination,
        key=key,
        parts=parts,
    )
    if isinstance(prepared_result, Err):
        return prepared_result
    return Ok(_apply_move(library, prepared_result.value))


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
    input_result = _validate_parts_input(
        category=category,
        key=key,
        parts=parts,
    )
    if isinstance(input_result, Err):
        return input_result

    return _attach_optional_title(input_result.value, title)


def _attach_optional_title(
    request: _PartsInput,
    title: object | None,
) -> Result[_AddPartsInput, DomainError]:
    title_result = _validate_optional_title(request.key, title)
    if isinstance(title_result, Err):
        return title_result

    return Ok(
        _AddPartsInput(
            category=request.category,
            key=request.key,
            parts=request.parts,
            title=title_result.value,
        )
    )


def _validate_parts_input(
    *,
    category: object,
    key: object,
    parts: object,
) -> Result[_PartsInput, DomainError]:
    identity_result = _validate_identity(category=category, key=key)
    if isinstance(identity_result, Err):
        return identity_result

    parts_result = normalize_parts(parts)
    if isinstance(parts_result, Err):
        return parts_result

    category_name, work_key = identity_result.value
    return Ok(_PartsInput(category_name, work_key, parts_result.value))


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


def _prepare_removal(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
) -> Result[_PreparedRemoval, DomainError]:
    input_result = _validate_parts_input(
        category=category,
        key=key,
        parts=parts,
    )
    if isinstance(input_result, Err):
        return input_result
    return _resolve_removal(library, input_result.value)


def _prepare_move(
    library: Library,
    *,
    source: object,
    destination: object,
    key: object,
    parts: object,
) -> Result[_PreparedMove, DomainError]:
    input_result = _validate_move_parts_input(
        source=source,
        destination=destination,
        key=key,
        parts=parts,
    )
    if isinstance(input_result, Err):
        return input_result
    return _resolve_move(library, input_result.value)


def _validate_move_parts_input(
    *,
    source: object,
    destination: object,
    key: object,
    parts: object,
) -> Result[_MovePartsInput, DomainError]:
    source_result = _validate_parts_input(
        category=source,
        key=key,
        parts=parts,
    )
    if isinstance(source_result, Err):
        return source_result

    destination_result = validate_category_name(destination)
    if isinstance(destination_result, Err):
        return destination_result
    return _build_move_parts_input(source_result.value, destination_result.value)


def _build_move_parts_input(
    source: _PartsInput,
    destination: CategoryName,
) -> Result[_MovePartsInput, SameCategoryMove]:
    if source.category == destination:
        return Err(SameCategoryMove(source.category))
    return Ok(_MovePartsInput(source, destination))


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


def _resolve_removal(
    library: Library,
    removal: _PartsInput,
) -> Result[_PreparedRemoval, DomainError]:
    category_result = _find_category_index(library, removal.category)
    if isinstance(category_result, Err):
        return category_result

    category_index = category_result.value
    category = library.categories[category_index]
    item_result = _find_item_index(category, removal.key)
    if isinstance(item_result, Err):
        return item_result
    return _prepare_item_removal(category_index, item_result.value, category, removal)


def _prepare_item_removal(
    category_index: int,
    item_index: int,
    category: Category,
    removal: _PartsInput,
) -> Result[_PreparedRemoval, MissingParts]:
    item = category.items[item_index]
    missing = _missing_parts(item.parts, removal.parts)
    if missing:
        return Err(MissingParts(category.name, item.key, missing))

    return Ok(_build_prepared_removal(category_index, item_index, item, removal))


def _build_prepared_removal(
    category_index: int,
    item_index: int,
    item: Item,
    removal: _PartsInput,
) -> _PreparedRemoval:
    return _PreparedRemoval(
        category_index=category_index,
        item_index=item_index,
        item=item,
        parts=removal.parts,
        remaining_parts=_subtract_parts(item.parts, removal.parts),
    )


def _resolve_move(
    library: Library,
    move: _MovePartsInput,
) -> Result[_PreparedMove, DomainError]:
    removal_result = _resolve_removal(library, move.source)
    if isinstance(removal_result, Err):
        return removal_result

    destination_result = _find_category_index(library, move.destination)
    if isinstance(destination_result, Err):
        return destination_result
    return Ok(_PreparedMove(removal_result.value, destination_result.value))


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


def _apply_removal(
    library: Library,
    removal: _PreparedRemoval,
) -> Library:
    category = library.categories[removal.category_index]
    updated = _apply_category_removal(category, removal)
    return _replace_category(library, removal.category_index, updated)


def _apply_category_removal(
    category: Category,
    removal: _PreparedRemoval,
) -> Category:
    if not removal.remaining_parts:
        items = _remove_at(category.items, removal.item_index)
        return replace(category, items=items)

    item = replace(removal.item, parts=removal.remaining_parts)
    items = _replace_at(category.items, removal.item_index, item)
    return replace(category, items=items)


def _apply_move(library: Library, move: _PreparedMove) -> Library:
    without_source = _apply_removal(library, move.removal)
    addition = _PreparedAddition(
        category_index=move.destination_index,
        key=move.removal.item.key,
        parts=move.removal.parts,
        title=move.removal.item.title,
    )
    return _apply_addition(without_source, addition)


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


def _find_item_index(
    category: Category,
    key: WorkKey,
) -> Result[int, UnknownItem]:
    index = _item_index(category, key)
    if index is None:
        return Err(UnknownItem(category.name, key))
    return Ok(index)


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


def _missing_parts(existing: Parts, requested: Parts) -> Parts:
    available = set(existing)
    return tuple(part for part in requested if part not in available)


def _subtract_parts(existing: Parts, removed: Parts) -> Parts:
    removed_set = set(removed)
    return tuple(part for part in existing if part not in removed_set)


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


def _remove_at(
    values: tuple[ReplacementT, ...],
    index: int,
) -> tuple[ReplacementT, ...]:
    return (*values[:index], *values[index + 1 :])
