from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    InvalidPartNumber,
    MissingParts,
    UnknownCategory,
    UnknownItem,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.operations import remove_parts
from ranobe_lib.domain.result import Err, Ok


class RemovePartsTest(unittest.TestCase):
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
                Category("required"),
            )
        )

    def test_removes_only_requested_parts(self) -> None:
        result = remove_parts(
            self.library,
            category="on-hand",
            key="overlord",
            parts=(3, 1, 3),
        )

        expected = Library(
            categories=(
                Category(
                    "on-hand",
                    (
                        Item("overlord", "Overlord", (2,)),
                        Item("sao", "Sword Art Online", (1,)),
                    ),
                ),
                Category("required"),
            )
        )
        self.assertEqual(result, Ok(expected))
        self.assertEqual(
            self.library.categories[0].items[0].parts,
            (1, 2, 3),
        )

    def test_removes_the_item_after_its_last_part(self) -> None:
        result = remove_parts(
            self.library,
            category="on-hand",
            key="sao",
            parts=(1,),
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(
            result.value.categories[0].items,
            (Item("overlord", "Overlord", (1, 2, 3)),),
        )

    def test_rejects_a_partial_removal_when_any_part_is_missing(self) -> None:
        result = remove_parts(
            self.library,
            category="on-hand",
            key="overlord",
            parts=(2, 4),
        )

        self.assertEqual(
            result,
            Err(MissingParts("on-hand", "overlord", (4,))),
        )
        self.assertEqual(
            self.library.categories[0].items[0].parts,
            (1, 2, 3),
        )

    def test_rejects_an_unknown_item(self) -> None:
        result = remove_parts(
            self.library,
            category="required",
            key="overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(UnknownItem("required", "overlord")))

    def test_rejects_an_unknown_category(self) -> None:
        result = remove_parts(
            self.library,
            category="unknown",
            key="overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(UnknownCategory("unknown")))

    def test_rejects_boolean_parts(self) -> None:
        result = remove_parts(
            self.library,
            category="on-hand",
            key="overlord",
            parts=(True,),
        )

        self.assertEqual(result, Err(InvalidPartNumber(True)))


if __name__ == "__main__":
    unittest.main()
