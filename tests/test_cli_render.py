from __future__ import annotations

import unittest
from pathlib import Path

from ranobe_lib.cli.errors import CliParseError
from ranobe_lib.cli.model import (
    CategoriesListed,
    CommandCompleted,
    ItemsListed,
)
from ranobe_lib.cli.render import (
    render_execution_error,
    render_output,
    render_parse_error,
)
from ranobe_lib.domain.errors import InvalidPartNumber
from ranobe_lib.domain.model import Category, Item
from ranobe_lib.infrastructure.json_errors import InvalidJsonValue
from ranobe_lib.infrastructure.store_errors import InvalidLibraryFile


class CliRenderTest(unittest.TestCase):
    def test_renders_category_names_one_per_line(self) -> None:
        output = CategoriesListed(("on-hand", "required"))

        self.assertEqual(render_output(output), "on-hand\nrequired\n")

    def test_renders_items_without_hiding_their_categories(self) -> None:
        output = ItemsListed(
            (
                Category(
                    "on-hand",
                    (Item("sao", "Sword Art Online", (1, 2)),),
                ),
                Category("required"),
            )
        )

        self.assertEqual(
            render_output(output),
            (
                "on-hand:\n"
                "  sao | Sword Art Online | volumes: 1, 2\n"
                "\n"
                "required:\n"
                "  (empty)\n"
            ),
        )

    def test_renders_mutation_completion(self) -> None:
        self.assertEqual(render_output(CommandCompleted()), "Done.\n")

    def test_renders_parse_context_and_message(self) -> None:
        error = CliParseError("missing command", "usage: ranobe-lib COMMAND\n")

        self.assertEqual(
            render_parse_error(error),
            "usage: ranobe-lib COMMAND\nranobe-lib: error: missing command\n",
        )

    def test_renders_a_nested_json_validation_error(self) -> None:
        error = InvalidLibraryFile(
            Path("library.json"),
            InvalidJsonValue(
                (0, "items", 0, "parts", 1),
                InvalidPartNumber(True),
            ),
        )

        self.assertEqual(
            render_execution_error(error),
            (
                "error: Invalid library file 'library.json': "
                "At $[0].items[0].parts[1]: Volume number must be a "
                "positive integer, got True.\n"
            ),
        )


if __name__ == "__main__":
    unittest.main()
