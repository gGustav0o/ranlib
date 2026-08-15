from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar


ValueT_co = TypeVar("ValueT_co", covariant=True)
ErrorT_co = TypeVar("ErrorT_co", covariant=True)
CheckErrorT = TypeVar("CheckErrorT")


@dataclass(frozen=True, slots=True)
class Ok(Generic[ValueT_co]):
    """A successful pure computation."""

    value: ValueT_co


@dataclass(frozen=True, slots=True)
class Err(Generic[ErrorT_co]):
    """A failed pure computation with an explicit error value."""

    error: ErrorT_co


Result: TypeAlias = Ok[ValueT_co] | Err[ErrorT_co]


def sequence_checks(
    checks: Iterable[Result[object, CheckErrorT]],
) -> Result[None, CheckErrorT]:
    """Return the first failure from lazily evaluated checks."""

    for check in checks:
        if isinstance(check, Err):
            return check
    return Ok(None)
