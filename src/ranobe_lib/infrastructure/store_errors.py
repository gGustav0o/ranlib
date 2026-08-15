from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from ranobe_lib.domain.errors import DomainError
from ranobe_lib.infrastructure.json_errors import JsonDecodingError


class JsonStoreError:
    """Marker base class for expected JSON file failures."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class LibraryReadError(JsonStoreError):
    path: Path
    reason: str


@dataclass(frozen=True, slots=True)
class InvalidLibraryFile(JsonStoreError):
    path: Path
    error: JsonDecodingError


@dataclass(frozen=True, slots=True)
class LibraryEncodingError(JsonStoreError):
    path: Path
    error: DomainError


@dataclass(frozen=True, slots=True)
class LibraryWriteError(JsonStoreError):
    path: Path
    reason: str


JsonStoreLoadError: TypeAlias = LibraryReadError | InvalidLibraryFile
JsonStoreSaveError: TypeAlias = LibraryEncodingError | LibraryWriteError


__all__ = (
    "InvalidLibraryFile",
    "JsonStoreError",
    "JsonStoreLoadError",
    "JsonStoreSaveError",
    "LibraryEncodingError",
    "LibraryReadError",
    "LibraryWriteError",
)
