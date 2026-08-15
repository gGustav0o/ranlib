from __future__ import annotations

from dataclasses import dataclass, replace

from ranobe_lib.domain._library_edit import (
    ItemLocation,
    find_item_location,
    missing_parts,
    remove_at,
    replace_at,
    replace_category,
    subtract_parts,
)
from ranobe_lib.domain._operation_inputs import (
    PartsInput,
    validate_identity,
    validate_parts_input,
)
from ranobe_lib.domain.errors import DomainError, MissingParts
from ranobe_lib.domain.model import Category, Item, Library, Parts
from ranobe_lib.domain.result import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class PreparedRemoval:
    location: ItemLocation
    item: Item
    parts: Parts
    remaining_parts: Parts


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
    return Ok(apply_removal(library, prepared_result.value))


def remove_item(
    library: Library,
    *,
    category: object,
    key: object,
) -> Result[Library, DomainError]:
    """Remove one complete item entry without affecting other categories."""

    identity_result = validate_identity(category=category, key=key)
    if isinstance(identity_result, Err):
        return identity_result

    category_name, work_key = identity_result.value
    location_result = find_item_location(library, category_name, work_key)
    if isinstance(location_result, Err):
        return location_result
    return Ok(_apply_item_removal(library, location_result.value))


def _prepare_removal(
    library: Library,
    *,
    category: object,
    key: object,
    parts: object,
) -> Result[PreparedRemoval, DomainError]:
    input_result = validate_parts_input(category=category, key=key, parts=parts)
    if isinstance(input_result, Err):
        return input_result
    return resolve_removal(library, input_result.value)


def resolve_removal(
    library: Library,
    removal: PartsInput,
) -> Result[PreparedRemoval, DomainError]:
    location_result = find_item_location(library, removal.category, removal.key)
    if isinstance(location_result, Err):
        return location_result

    location = location_result.value
    category = library.categories[location.category_index]
    return _prepare_item_removal(location, category.items[location.item_index], removal)


def _prepare_item_removal(
    location: ItemLocation,
    item: Item,
    removal: PartsInput,
) -> Result[PreparedRemoval, MissingParts]:
    missing = missing_parts(item.parts, removal.parts)
    if missing:
        return Err(MissingParts(removal.category, item.key, missing))
    return Ok(_build_prepared_removal(location, item, removal.parts))


def _build_prepared_removal(
    location: ItemLocation,
    item: Item,
    parts: Parts,
) -> PreparedRemoval:
    return PreparedRemoval(
        location=location,
        item=item,
        parts=parts,
        remaining_parts=subtract_parts(item.parts, parts),
    )


def apply_removal(library: Library, removal: PreparedRemoval) -> Library:
    category_index = removal.location.category_index
    category = library.categories[category_index]
    updated = _apply_category_removal(category, removal)
    return replace_category(library, category_index, updated)


def _apply_category_removal(
    category: Category,
    removal: PreparedRemoval,
) -> Category:
    item_index = removal.location.item_index
    if not removal.remaining_parts:
        return replace(category, items=remove_at(category.items, item_index))

    item = replace(removal.item, parts=removal.remaining_parts)
    return replace(category, items=replace_at(category.items, item_index, item))


def _apply_item_removal(library: Library, location: ItemLocation) -> Library:
    category = library.categories[location.category_index]
    items = remove_at(category.items, location.item_index)
    updated = replace(category, items=items)
    return replace_category(library, location.category_index, updated)


__all__ = ("remove_item", "remove_parts")
