from __future__ import annotations

from dataclasses import dataclass

from ranobe_lib.domain._library_edit import find_category_index
from ranobe_lib.domain._operation_inputs import PartsInput, validate_parts_input
from ranobe_lib.domain.errors import DomainError, SameCategoryMove
from ranobe_lib.domain.model import CategoryName, Library
from ranobe_lib.domain.part_addition import PreparedAddition, apply_addition
from ranobe_lib.domain.part_removal import (
    PreparedRemoval,
    apply_removal,
    resolve_removal,
)
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import validate_category_name


@dataclass(frozen=True, slots=True)
class _MovePartsInput:
    source: PartsInput
    destination: CategoryName


@dataclass(frozen=True, slots=True)
class _PreparedMove:
    removal: PreparedRemoval
    destination_index: int


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
    source_result = validate_parts_input(category=source, key=key, parts=parts)
    if isinstance(source_result, Err):
        return source_result

    destination_result = validate_category_name(destination)
    if isinstance(destination_result, Err):
        return destination_result
    return _build_move_parts_input(source_result.value, destination_result.value)


def _build_move_parts_input(
    source: PartsInput,
    destination: CategoryName,
) -> Result[_MovePartsInput, SameCategoryMove]:
    if source.category == destination:
        return Err(SameCategoryMove(source.category))
    return Ok(_MovePartsInput(source, destination))


def _resolve_move(
    library: Library,
    move: _MovePartsInput,
) -> Result[_PreparedMove, DomainError]:
    removal_result = resolve_removal(library, move.source)
    if isinstance(removal_result, Err):
        return removal_result

    destination_result = find_category_index(library, move.destination)
    if isinstance(destination_result, Err):
        return destination_result
    return Ok(_PreparedMove(removal_result.value, destination_result.value))


def _apply_move(library: Library, move: _PreparedMove) -> Library:
    without_source = apply_removal(library, move.removal)
    addition = _destination_addition(move)
    return apply_addition(without_source, addition)


def _destination_addition(move: _PreparedMove) -> PreparedAddition:
    return PreparedAddition(
        category_index=move.destination_index,
        key=move.removal.item.key,
        parts=move.removal.parts,
        title=move.removal.item.title,
    )


__all__ = ("move_parts",)
