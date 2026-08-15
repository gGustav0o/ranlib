from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias, TypeVar

from ranobe_lib.domain.model import Library
from ranobe_lib.domain.result import Result


LoadErrorT_co = TypeVar("LoadErrorT_co", covariant=True)
SaveErrorT_co = TypeVar("SaveErrorT_co", covariant=True)


LoadLibrary: TypeAlias = Callable[[], Result[Library, LoadErrorT_co]]
SaveLibrary: TypeAlias = Callable[[Library], Result[None, SaveErrorT_co]]


__all__ = ("LoadLibrary", "SaveLibrary")
