from __future__ import annotations

import tempfile
import unittest
from io import StringIO
from pathlib import Path

from ranobe_lib.cli.main import main
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.infrastructure.json_codec import dumps_library
from ranobe_lib.infrastructure.json_store import load_json_library


class CliMainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stdout = StringIO()
        self.stderr = StringIO()

    def test_help_is_successful_and_does_not_open_a_library(self) -> None:
        status = main(
            ("--file", "missing.json", "--help"),
            stdout=self.stdout,
            stderr=self.stderr,
        )

        self.assertEqual(status, 0)
        self.assertIn("list-categories", self.stdout.getvalue())
        self.assertEqual(self.stderr.getvalue(), "")

    def test_invalid_arguments_use_the_usage_exit_code(self) -> None:
        status = main((), stdout=self.stdout, stderr=self.stderr)

        self.assertEqual(status, 2)
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertIn("usage:", self.stderr.getvalue())

    def test_file_failure_uses_the_execution_exit_code(self) -> None:
        status = main(
            ("--file", "missing.json", "list-categories"),
            stdout=self.stdout,
            stderr=self.stderr,
        )

        self.assertEqual(status, 1)
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertIn("Cannot read library file", self.stderr.getvalue())

    def test_runs_a_query_and_mutation_against_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            library = Library(
                (
                    Category(
                        "on-hand",
                        (Item("sao", "Sword Art Online", (1,)),),
                    ),
                    Category("required"),
                )
            )
            path.write_text(dumps_library(library).value, encoding="utf-8")

            query_status = main(
                ("--file", str(path), "list-items", "-c", "on-hand"),
                stdout=self.stdout,
                stderr=self.stderr,
            )
            mutation_status = main(
                (
                    "--file",
                    str(path),
                    "add-parts",
                    "--category",
                    "on-hand",
                    "--key",
                    "sao",
                    "2",
                ),
                stdout=self.stdout,
                stderr=self.stderr,
            )

            loaded = load_json_library(path).value

        self.assertEqual((query_status, mutation_status), (0, 0))
        self.assertIn("on-hand:", self.stdout.getvalue())
        self.assertTrue(self.stdout.getvalue().endswith("Done.\n"))
        self.assertEqual(self.stderr.getvalue(), "")
        self.assertEqual(loaded.categories[0].items[0].parts, (1, 2))

    def test_searches_json_items_within_selected_categories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            library = Library(
                (
                    Category(
                        "on-hand",
                        (Item("sao", "Sword Art Online", (1,)),),
                    ),
                    Category(
                        "required",
                        (Item("artbook", "Manga Guide", (2,)),),
                    ),
                )
            )
            path.write_text(dumps_library(library).value, encoding="utf-8")

            status = main(
                (
                    "--file",
                    str(path),
                    "search-items",
                    "ART",
                    "--category",
                    "on-hand",
                ),
                stdout=self.stdout,
                stderr=self.stderr,
            )

        self.assertEqual(status, 0)
        self.assertEqual(
            self.stdout.getvalue(),
            "on-hand:\n\nSword Art Online\n1\n",
        )
        self.assertEqual(self.stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
