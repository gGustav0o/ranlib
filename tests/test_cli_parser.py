from __future__ import annotations

import unittest
from pathlib import Path

from ranobe_lib.application.commands import (
    AddParts,
    ListCategories,
    ListItems,
    MoveParts,
    RemoveItem,
    RemoveParts,
    SearchItems,
)
from ranobe_lib.cli.errors import CliParseError
from ranobe_lib.cli.model import HelpRequested, Invocation
from ranobe_lib.cli.parser import parse_invocation
from ranobe_lib.domain.result import Err, Ok


class CliParserTest(unittest.TestCase):
    def test_treats_help_as_a_successful_value(self) -> None:
        result = parse_invocation(("--help",))

        self.assertIsInstance(result, Ok)
        self.assertIsInstance(result.value, HelpRequested)
        self.assertIn("list-categories", result.value.text)

    def test_builds_a_query_with_the_default_path(self) -> None:
        result = parse_invocation(("list-categories",))

        self.assertEqual(
            result,
            Ok(Invocation(Path("ranobe-lib.json"), ListCategories())),
        )

    def test_preserves_selected_category_order(self) -> None:
        result = parse_invocation(
            (
                "--file",
                "custom.json",
                "list-items",
                "--category",
                "required",
                "--category",
                "on-hand",
            )
        )

        self.assertEqual(
            result,
            Ok(
                Invocation(
                    Path("custom.json"),
                    ListItems(("required", "on-hand")),
                )
            ),
        )

    def test_builds_a_search_with_selected_categories(self) -> None:
        result = parse_invocation(
            (
                "search-items",
                "Sword",
                "--category",
                "required",
                "--category",
                "on-hand",
            )
        )

        self.assertEqual(
            result,
            Ok(
                Invocation(
                    Path("ranobe-lib.json"),
                    SearchItems("Sword", ("required", "on-hand")),
                )
            ),
        )

    def test_builds_each_mutation_without_normalizing_parts(self) -> None:
        cases = (
            (
                (
                    "add-parts",
                    "--category",
                    "on-hand",
                    "--key",
                    "sao",
                    "--title",
                    "Sword Art Online",
                    "2",
                    "1",
                    "2",
                ),
                AddParts(
                    "sao",
                    (2, 1, 2),
                    "on-hand",
                    "Sword Art Online",
                ),
            ),
            (
                (
                    "remove-parts",
                    "--category",
                    "on-hand",
                    "--key",
                    "sao",
                    "2",
                ),
                RemoveParts("sao", (2,), "on-hand"),
            ),
            (
                (
                    "remove-item",
                    "--category",
                    "on-hand",
                    "--key",
                    "sao",
                ),
                RemoveItem("sao", "on-hand"),
            ),
            (
                (
                    "move-parts",
                    "--source",
                    "on-hand",
                    "--destination",
                    "required",
                    "--key",
                    "sao",
                    "2",
                    "4",
                ),
                MoveParts("sao", (2, 4), "on-hand", "required"),
            ),
        )

        for arguments, expected in cases:
            with self.subTest(command=arguments[0]):
                result = parse_invocation(arguments)
                self.assertEqual(
                    result,
                    Ok(Invocation(Path("ranobe-lib.json"), expected)),
                )

    def test_returns_a_parse_error_instead_of_exiting(self) -> None:
        result = parse_invocation(("add-parts",))

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, CliParseError)
        self.assertIn("required", result.error.message)
        self.assertTrue(result.error.usage.startswith("usage:"))

    def test_rejects_booleans_as_volume_numbers(self) -> None:
        result = parse_invocation(
            (
                "remove-parts",
                "--category",
                "on-hand",
                "--key",
                "sao",
                "true",
            )
        )

        self.assertIsInstance(result, Err)
        self.assertIn("invalid int value", result.error.message)


if __name__ == "__main__":
    unittest.main()
