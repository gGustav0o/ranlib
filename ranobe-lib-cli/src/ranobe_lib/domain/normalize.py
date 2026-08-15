from __future__ import annotations

from collections.abc import Iterable
from typing import TypeAlias

from ranobe_lib.domain.errors import (
    EmptyParts,
    InvalidPartNumber,
    InvalidPartsCollection,
)
from ranobe_lib.domain.model import Parts
from ranobe_lib.domain.result import Err, Ok, Result


PartsNormalizationError: TypeAlias = (
    EmptyParts | InvalidPartNumber | InvalidPartsCollection
)


def normalize_parts(
    raw_parts: object,
) -> Result[Parts, PartsNormalizationError]:
    """Return sorted unique positive part numbers without mutating the input."""

    if isinstance(raw_parts, (str, bytes)) or not isinstance(raw_parts, Iterable):
        return Err(InvalidPartsCollection(raw_parts))

    unique_parts: set[int] = set()
    for part in raw_parts:
        if isinstance(part, bool) or not isinstance(part, int) or part <= 0:
            return Err(InvalidPartNumber(part))
        unique_parts.add(part)

    if not unique_parts:
        return Err(EmptyParts())

    return Ok(tuple(sorted(unique_parts)))
