from __future__ import annotations

import unittest
from pathlib import Path

from ranobe_lib.application.commands import AddParts, ListCategories, ListItems
from ranobe_lib.cli.model import (
    CategoriesListed,
    CommandCompleted,
    ItemsListed,
)
from ranobe_lib.cli.runner import execute_command
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.result import Err, Ok
from ranobe_lib.infrastructure.store_errors import LibraryReadError


class CliRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library(
            (
                Category("on-hand", (Item("sao", "Sword Art Online", (1,)),)),
                Category("required"),
            )
        )
        self.saved: list[Library] = []

    def load(self) -> Ok[Library]:
        return Ok(self.library)

    def save(self, library: Library) -> Ok[None]:
        self.saved.append(library)
        return Ok(None)

    def test_maps_category_query_to_a_cli_value(self) -> None:
        result = execute_command(
            ListCategories(),
            load=self.load,
            save=self.save,
        )

        self.assertEqual(
            result,
            Ok(CategoriesListed(("on-hand", "required"))),
        )
        self.assertEqual(self.saved, [])

    def test_keeps_category_boundaries_in_an_items_query(self) -> None:
        result = execute_command(
            ListItems(("required", "on-hand")),
            load=self.load,
            save=self.save,
        )

        self.assertEqual(
            result,
            Ok(
                ItemsListed(
                    (self.library.categories[1], self.library.categories[0])
                )
            ),
        )

    def test_maps_a_successful_mutation_to_completion(self) -> None:
        result = execute_command(
            AddParts("sao", (2,), "on-hand"),
            load=self.load,
            save=self.save,
        )

        self.assertEqual(result, Ok(CommandCompleted()))
        self.assertEqual(self.saved[0].categories[0].items[0].parts, (1, 2))

    def test_preserves_a_structured_load_error(self) -> None:
        error = LibraryReadError(Path("missing.json"), "not found")

        result = execute_command(
            ListCategories(),
            load=lambda: Err(error),
            save=self.save,
        )

        self.assertEqual(result, Err(error))
        self.assertEqual(self.saved, [])


if __name__ == "__main__":
    unittest.main()
