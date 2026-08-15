from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    InvalidPartNumber,
    MissingParts,
    SameCategoryMove,
    UnknownCategory,
    UnknownItem,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.operations import move_parts
from ranobe_lib.domain.result import Err, Ok


class MovePartsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1, 2, 3)),),
                ),
                Category("required"),
                Category("absolutely-necessary"),
            )
        )

    def test_moves_selected_parts_to_a_new_destination_item(self) -> None:
        result = move_parts(
            self.library,
            source="on-hand",
            destination="required",
            key="overlord",
            parts=(3, 2, 3),
        )

        expected = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1,)),),
                ),
                Category(
                    "required",
                    (Item("overlord", "Overlord", (2, 3)),),
                ),
                Category("absolutely-necessary"),
            )
        )
        self.assertEqual(result, Ok(expected))
        self.assertEqual(
            self.library.categories[0].items[0].parts,
            (1, 2, 3),
        )

    def test_merges_parts_with_an_existing_destination_item(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1, 2, 3)),),
                ),
                Category(
                    "required",
                    (Item("overlord", "Overlord", (3, 4)),),
                ),
            )
        )

        result = move_parts(
            library,
            source="on-hand",
            destination="required",
            key="overlord",
            parts=(2, 3),
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(
            result.value.categories[0].items[0].parts,
            (1,),
        )
        self.assertEqual(
            result.value.categories[1].items[0].parts,
            (2, 3, 4),
        )

    def test_removes_the_source_item_after_moving_its_last_part(self) -> None:
        result = move_parts(
            self.library,
            source="on-hand",
            destination="required",
            key="overlord",
            parts=(1, 2, 3),
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value.categories[0].items, ())
        self.assertEqual(
            result.value.categories[1].items,
            (Item("overlord", "Overlord", (1, 2, 3)),),
        )

    def test_is_atomic_when_any_source_part_is_missing(self) -> None:
        result = move_parts(
            self.library,
            source="on-hand",
            destination="required",
            key="overlord",
            parts=(2, 4),
        )

        self.assertEqual(
            result,
            Err(MissingParts("on-hand", "overlord", (4,))),
        )
        self.assertEqual(self.library.categories[1].items, ())
        self.assertEqual(
            self.library.categories[0].items[0].parts,
            (1, 2, 3),
        )

    def test_rejects_a_move_within_the_same_category(self) -> None:
        result = move_parts(
            self.library,
            source="on-hand",
            destination="on-hand",
            key="overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(SameCategoryMove("on-hand")))

    def test_rejects_an_unknown_source_item(self) -> None:
        result = move_parts(
            self.library,
            source="required",
            destination="on-hand",
            key="overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(UnknownItem("required", "overlord")))

    def test_rejects_an_unknown_destination_category(self) -> None:
        result = move_parts(
            self.library,
            source="on-hand",
            destination="unknown",
            key="overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(UnknownCategory("unknown")))

    def test_rejects_boolean_parts(self) -> None:
        result = move_parts(
            self.library,
            source="on-hand",
            destination="required",
            key="overlord",
            parts=(False,),
        )

        self.assertEqual(result, Err(InvalidPartNumber(False)))


if __name__ == "__main__":
    unittest.main()
