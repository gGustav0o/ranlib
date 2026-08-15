from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.result import Err, Ok
from ranobe_lib.infrastructure.json_codec import dumps_library
from ranobe_lib.infrastructure.json_errors import JsonSyntaxError
from ranobe_lib.infrastructure.json_store import (
    load_json_library,
    save_json_library,
)
from ranobe_lib.infrastructure.store_errors import (
    InvalidLibraryFile,
    LibraryEncodingError,
    LibraryReadError,
    LibraryWriteError,
)


class JsonStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.path = self.directory / "library.json"
        self.library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("book", "Книга", (1, 2)),),
                ),
                Category("required"),
            )
        )

    def test_loads_a_canonical_utf8_library(self) -> None:
        text = dumps_library(self.library).value
        self.path.write_text(text, encoding="utf-8", newline="\n")

        result = load_json_library(self.path)

        self.assertEqual(result, Ok(self.library))

    def test_reports_a_structured_decoding_failure(self) -> None:
        self.path.write_text("{\n", encoding="utf-8")

        result = load_json_library(self.path)

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, InvalidLibraryFile)
        self.assertEqual(result.error.path, self.path)
        self.assertIsInstance(result.error.error, JsonSyntaxError)

    def test_reports_a_missing_file_as_a_read_failure(self) -> None:
        result = load_json_library(self.path)

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, LibraryReadError)
        self.assertEqual(result.error.path, self.path)

    def test_reports_invalid_utf8_as_a_read_failure(self) -> None:
        self.path.write_bytes(b"\xff")

        result = load_json_library(self.path)

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, LibraryReadError)

    def test_saves_exact_human_readable_utf8_json(self) -> None:
        result = save_json_library(self.path, self.library)

        self.assertEqual(result, Ok(None))
        actual = self.path.read_bytes()
        expected = dumps_library(self.library).value.encode("utf-8")
        self.assertEqual(actual, expected)
        self.assertTrue(actual.endswith(b"\n"))
        self.assertIn("Книга", actual.decode("utf-8"))

    def test_does_not_touch_the_original_after_an_encoding_failure(self) -> None:
        self.path.write_text("original\n", encoding="utf-8")
        invalid = Library(
            (Category("on-hand", (Item("book", "Book", (2, 1)),)),)
        )

        result = save_json_library(self.path, invalid)

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, LibraryEncodingError)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "original\n")

    def test_keeps_the_original_and_removes_the_temporary_on_replace_failure(
        self,
    ) -> None:
        self.path.write_text("original\n", encoding="utf-8")
        replace_arguments: list[tuple[Path, Path]] = []

        def reject_replace(source: os.PathLike[str], target: os.PathLike[str]) -> None:
            replace_arguments.append((Path(source), Path(target)))
            raise OSError("replace failed")

        with patch(
            "ranobe_lib.infrastructure.json_store.os.replace",
            side_effect=reject_replace,
        ):
            result = save_json_library(self.path, self.library)

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, LibraryWriteError)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "original\n")
        self.assertEqual(replace_arguments[0][0].parent, self.path.parent)
        self.assertEqual(replace_arguments[0][1], self.path)
        self.assertEqual(tuple(self.directory.iterdir()), (self.path,))


if __name__ == "__main__":
    unittest.main()
