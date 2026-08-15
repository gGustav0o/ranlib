from __future__ import annotations

import unittest

from ranobe_lib.application.commands import (
    AddParts,
    ListItems,
    MoveParts,
    RemoveItem,
    RemoveParts,
)
from ranobe_lib.application.services import (
    add_parts,
    list_categories,
    list_items,
    move_parts,
    remove_item,
    remove_parts,
)
from ranobe_lib.domain.errors import MissingParts
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.result import Err, Ok


class ApplicationServicesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1, 2)),),
                ),
                Category("required"),
            )
        )
        self.saved: list[Library] = []

    def load(self) -> Ok[Library]:
        return Ok(self.library)

    def save(self, library: Library) -> Ok[None]:
        self.saved.append(library)
        return Ok(None)

    def test_lists_categories_without_a_save_effect(self) -> None:
        result = list_categories(load=self.load)

        self.assertEqual(result, Ok(("on-hand", "required")))
        self.assertEqual(self.saved, [])

    def test_lists_selected_categories_without_flattening_items(self) -> None:
        result = list_items(
            ListItems(("required", "on-hand")),
            load=self.load,
        )

        self.assertEqual(
            result,
            Ok((self.library.categories[1], self.library.categories[0])),
        )

    def test_adds_parts_and_saves_the_result_once(self) -> None:
        result = add_parts(
            AddParts("overlord", (3,), "on-hand"),
            load=self.load,
            save=self.save,
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value.categories[0].items[0].parts, (1, 2, 3))
        self.assertEqual(self.saved, [result.value])

    def test_skips_saving_when_a_transition_is_a_no_op(self) -> None:
        result = add_parts(
            AddParts("overlord", (2,), "on-hand"),
            load=self.load,
            save=self.save,
        )

        self.assertEqual(result, Ok(self.library))
        self.assertIs(result.value, self.library)
        self.assertEqual(self.saved, [])

    def test_does_not_save_after_a_domain_failure(self) -> None:
        result = remove_parts(
            RemoveParts("overlord", (3,), "on-hand"),
            load=self.load,
            save=self.save,
        )

        self.assertEqual(
            result,
            Err(MissingParts("on-hand", "overlord", (3,))),
        )
        self.assertEqual(self.saved, [])

    def test_stops_before_the_transition_after_a_load_failure(self) -> None:
        result = remove_item(
            RemoveItem("overlord", "on-hand"),
            load=lambda: Err("load failed"),
            save=self.save,
        )

        self.assertEqual(result, Err("load failed"))
        self.assertEqual(self.saved, [])

    def test_propagates_a_save_failure(self) -> None:
        result = remove_item(
            RemoveItem("overlord", "on-hand"),
            load=self.load,
            save=lambda library: Err("save failed"),
        )

        self.assertEqual(result, Err("save failed"))
        self.assertEqual(self.library.categories[0].items[0].parts, (1, 2))

    def test_removes_an_item_through_its_command(self) -> None:
        result = remove_item(
            RemoveItem("overlord", "on-hand"),
            load=self.load,
            save=self.save,
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value.categories[0].items, ())

    def test_moves_parts_through_its_command(self) -> None:
        result = move_parts(
            MoveParts("overlord", (2,), "on-hand", "required"),
            load=self.load,
            save=self.save,
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value.categories[0].items[0].parts, (1,))
        self.assertEqual(
            result.value.categories[1].items,
            (Item("overlord", "Overlord", (2,)),),
        )


if __name__ == "__main__":
    unittest.main()
