from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar


ValueT = TypeVar("ValueT")
ErrorT = TypeVar("ErrorT")


@dataclass(frozen=True, slots=True)
class Ok(Generic[ValueT]):
    """A successful pure computation."""

    value: ValueT


@dataclass(frozen=True, slots=True)
class Err(Generic[ErrorT]):
    """A failed pure computation with an explicit error value."""

    error: ErrorT


Result: TypeAlias = Ok[ValueT] | Err[ErrorT]
