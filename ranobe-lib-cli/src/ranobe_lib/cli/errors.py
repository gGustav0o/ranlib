from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from ranobe_lib.domain.errors import DomainError
from ranobe_lib.infrastructure.store_errors import (
    JsonStoreLoadError,
    JsonStoreSaveError,
)


@dataclass(frozen=True, slots=True)
class CliParseError:
    message: str
    usage: str


CliExecutionError: TypeAlias = (
    DomainError | JsonStoreLoadError | JsonStoreSaveError
)


__all__ = ("CliExecutionError", "CliParseError")
