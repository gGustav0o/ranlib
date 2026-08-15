from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import UnknownCategory, UnknownItem
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.operations import remove_item
from ranobe_lib.domain.result import Err, Ok


class RemoveItemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library(
            categories=(
                Category(
                    "on-hand",
                    (
                        Item("overlord", "Overlord", (1, 2, 3)),
                        Item("sao", "Sword Art Online", (1,)),
                    ),
                ),
                Category(
                    "required",
                    (Item("overlord", "Overlord", (4,)),),
                ),
            )
        )

    def test_removes_only_the_selected_category_entry(self) -> None:
        result = remove_item(
            self.library,
            category="on-hand",
            key="overlord",
        )

        self.assertEqual(
            result,
            Ok(
                Library(
                    categories=(
                        Category(
                            "on-hand",
                            (Item("sao", "Sword Art Online", (1,)),),
                        ),
                        Category(
                            "required",
                            (Item("overlord", "Overlord", (4,)),),
                        ),
                    )
                )
            ),
        )

    def test_does_not_mutate_the_source_library(self) -> None:
        result = remove_item(
            self.library,
            category="on-hand",
            key="overlord",
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(len(self.library.categories[0].items), 2)

    def test_rejects_an_unknown_category(self) -> None:
        result = remove_item(
            self.library,
            category="unknown",
            key="overlord",
        )

        self.assertEqual(result, Err(UnknownCategory("unknown")))

    def test_rejects_an_unknown_item(self) -> None:
        result = remove_item(
            self.library,
            category="on-hand",
            key="unknown",
        )

        self.assertEqual(result, Err(UnknownItem("on-hand", "unknown")))


if __name__ == "__main__":
    unittest.main()
