from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from ranobe_lib.domain.errors import DomainError


JsonPathSegment: TypeAlias = str | int
JsonPath: TypeAlias = tuple[JsonPathSegment, ...]


class JsonCodecError:
    """Marker base class for expected JSON decoding failures."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class JsonSyntaxError(JsonCodecError):
    message: str
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class DuplicateJsonField(JsonCodecError):
    field: str


@dataclass(frozen=True, slots=True)
class UnexpectedJsonType(JsonCodecError):
    path: JsonPath
    expected: str
    actual: str


@dataclass(frozen=True, slots=True)
class InvalidObjectFields(JsonCodecError):
    path: JsonPath
    missing: tuple[str, ...]
    unknown: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvalidJsonValue(JsonCodecError):
    path: JsonPath
    error: DomainError


JsonDecodingError: TypeAlias = (
    JsonSyntaxError
    | DuplicateJsonField
    | UnexpectedJsonType
    | InvalidObjectFields
    | InvalidJsonValue
)
