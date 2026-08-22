from __future__ import annotations

import unittest

from pathlib import Path

from ranobe_lib.cli.errors import CliParseError
from ranobe_lib.cli.model import (
    CategoriesListed,
    CommandCompleted,
    ItemsListed,
    SearchResultsFound,
)
from ranobe_lib.cli.render import (
    render_execution_error,
    render_output,
    render_parse_error,
)
from ranobe_lib.domain.errors import InvalidPartNumber, InvalidSearchText
from ranobe_lib.domain.model import Category, Item
from ranobe_lib.domain.search import CategoryMatches
from ranobe_lib.infrastructure.json_errors import InvalidJsonValue
from ranobe_lib.infrastructure.store_errors import InvalidLibraryFile


class CliRenderTest(unittest.TestCase):
    def test_renders_category_names_one_per_line(self) -> None:
        output = CategoriesListed(("on-hand", "required"))

        self.assertEqual(
            render_output(output),
            "on-hand\nrequired\n",
        )

    def test_renders_items_without_hiding_their_categories(self) -> None:
        output = ItemsListed(
            (
                Category(
                    "on-hand",
                    (
                        Item("sao", "Sword Art Online", (1, 2)),
                        Item("overlord", "Overlord", (5, 6, 7)),
                    ),
                ),
                Category("required"),
            )
        )

        self.assertEqual(
            render_output(output),
            (
                "on-hand:\n"
                "\n"
                "Sword Art Online\n"
                "1, 2\n"
                "-----\n"
                "Overlord\n"
                "5, 6, 7\n"
                "\n"
                "required:\n"
                "\n"
                "(empty)\n"
            ),
        )

    def test_renders_search_results_with_the_shared_item_format(self) -> None:
        output = SearchResultsFound(
            (
                CategoryMatches(
                    "on-hand",
                    (Item("sao", "Sword Art Online", (1, 2)),),
                ),
            )
        )

        self.assertEqual(
            render_output(output),
            "on-hand:\n\nSword Art Online\n1, 2\n",
        )

    def test_renders_an_explicit_empty_search_result(self) -> None:
        self.assertEqual(
            render_output(SearchResultsFound(())),
            "No matches.\n",
        )

    def test_renders_mutation_completion(self) -> None:
        self.assertEqual(
            render_output(CommandCompleted()),
            "Done.\n",
        )

    def test_renders_parse_context_and_message(self) -> None:
        error = CliParseError(
            "missing command",
            "usage: ranobe-lib COMMAND\n",
        )

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

    def test_renders_an_invalid_search_text(self) -> None:
        self.assertEqual(
            render_execution_error(InvalidSearchText(" ")),
            "error: Search text must be a non-blank string, got ' '.\n",
        )


if __name__ == "__main__":
    unittest.main()
