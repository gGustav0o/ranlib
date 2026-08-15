from __future__ import annotations

import os
import tempfile
from contextlib import AbstractContextManager
from pathlib import Path
from typing import TextIO

from ranobe_lib.domain.model import Library
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.infrastructure.json_codec import dumps_library, loads_library
from ranobe_lib.infrastructure.store_errors import (
    InvalidLibraryFile,
    JsonStoreLoadError,
    JsonStoreSaveError,
    LibraryEncodingError,
    LibraryReadError,
    LibraryWriteError,
)


def load_json_library(path: Path) -> Result[Library, JsonStoreLoadError]:
    """Read and decode one UTF-8 JSON library file."""

    text_result = _read_utf8(path)
    if isinstance(text_result, Err):
        return text_result

    library_result = loads_library(text_result.value)
    if isinstance(library_result, Err):
        return Err(InvalidLibraryFile(path, library_result.error))
    return library_result


def save_json_library(
    path: Path,
    library: Library,
) -> Result[None, JsonStoreSaveError]:
    """Encode and atomically replace one UTF-8 JSON library file."""

    text_result = dumps_library(library)
    if isinstance(text_result, Err):
        return Err(LibraryEncodingError(path, text_result.error))
    return _write_atomically(path, text_result.value)


def _read_utf8(path: Path) -> Result[str, LibraryReadError]:
    try:
        return Ok(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        return Err(LibraryReadError(path, str(error)))


def _write_atomically(
    path: Path,
    text: str,
) -> Result[None, LibraryWriteError]:
    temporary_result = _write_temporary_file(path, text)
    if isinstance(temporary_result, Err):
        return temporary_result
    return _replace_original(temporary_result.value, path)


def _write_temporary_file(
    path: Path,
    text: str,
) -> Result[Path, LibraryWriteError]:
    try:
        return Ok(_persist_temporary(path, text))
    except OSError as error:
        return Err(LibraryWriteError(path, str(error)))


def _persist_temporary(path: Path, text: str) -> Path:
    temporary: Path | None = None
    try:
        with _open_temporary(path) as stream:
            temporary = Path(stream.name)
            _write_and_sync(stream, text)
        return temporary
    except OSError:
        _discard_temporary(temporary)
        raise


def _open_temporary(path: Path) -> AbstractContextManager[TextIO]:
    return tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )


def _write_and_sync(stream: TextIO, text: str) -> None:
    stream.write(text)
    stream.flush()
    os.fsync(stream.fileno())


def _replace_original(
    temporary: Path,
    path: Path,
) -> Result[None, LibraryWriteError]:
    try:
        os.replace(temporary, path)
        return Ok(None)
    except OSError as error:
        _discard_temporary(temporary)
        return Err(LibraryWriteError(path, str(error)))


def _discard_temporary(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


__all__ = ("load_json_library", "save_json_library")
