from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    InvalidPartNumber,
    MissingTitle,
    UnknownCategory,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.operations import add_parts
from ranobe_lib.domain.result import Err, Ok


class AddPartsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.library = Library(
            categories=(
                Category("on-hand"),
                Category("required"),
                Category("absolutely-necessary"),
            )
        )

    def test_adds_a_new_item_with_canonical_parts(self) -> None:
        result = add_parts(
            self.library,
            category="on-hand",
            key="overlord",
            title="Overlord",
            parts=(3, 1, 3, 2),
        )

        expected = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1, 2, 3)),),
                ),
                Category("required"),
                Category("absolutely-necessary"),
            )
        )
        self.assertEqual(result, Ok(expected))
        self.assertEqual(self.library.categories[0].items, ())

    def test_merges_parts_without_requiring_an_existing_title(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1, 3)),),
                ),
                Category("required"),
            )
        )

        result = add_parts(
            library,
            category="on-hand",
            key="overlord",
            parts=(3, 2),
        )

        self.assertEqual(
            result,
            Ok(
                Library(
                    categories=(
                        Category(
                            "on-hand",
                            (Item("overlord", "Overlord", (1, 2, 3)),),
                        ),
                        Category("required"),
                    )
                )
            ),
        )

    def test_reuses_the_global_title_when_adding_to_another_category(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1,)),),
                ),
                Category("required"),
            )
        )

        result = add_parts(
            library,
            category="required",
            key="overlord",
            parts=(2,),
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(
            result.value.categories[1].items,
            (Item("overlord", "Overlord", (2,)),),
        )

    def test_requires_a_title_for_a_new_key(self) -> None:
        result = add_parts(
            self.library,
            category="on-hand",
            key="overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(MissingTitle("overlord")))

    def test_rejects_a_conflicting_title_for_a_known_key(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1,)),),
                ),
                Category("required"),
            )
        )

        result = add_parts(
            library,
            category="required",
            key="overlord",
            title="Another Overlord",
            parts=(2,),
        )

        self.assertEqual(
            result,
            Err(
                ConflictingTitle(
                    key="overlord",
                    expected="Overlord",
                    actual="Another Overlord",
                )
            ),
        )
        self.assertEqual(library.categories[1].items, ())

    def test_allows_equal_titles_for_different_keys(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("work-a", "Shared Title", (1,)),),
                ),
                Category("required"),
            )
        )

        result = add_parts(
            library,
            category="required",
            key="work-b",
            title="Shared Title",
            parts=(1,),
        )

        self.assertIsInstance(result, Ok)
        self.assertEqual(result.value.categories[1].items[0].key, "work-b")

    def test_rejects_an_unknown_category(self) -> None:
        result = add_parts(
            self.library,
            category="unknown",
            key="overlord",
            title="Overlord",
            parts=(1,),
        )

        self.assertEqual(result, Err(UnknownCategory("unknown")))

    def test_rejects_boolean_parts(self) -> None:
        result = add_parts(
            self.library,
            category="on-hand",
            key="overlord",
            title="Overlord",
            parts=(True,),
        )

        self.assertEqual(result, Err(InvalidPartNumber(True)))

    def test_returns_the_same_library_when_nothing_changes(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1, 2)),),
                ),
            )
        )

        result = add_parts(
            library,
            category="on-hand",
            key="overlord",
            parts=(2, 1, 2),
        )

        self.assertEqual(result, Ok(library))
        self.assertIs(result.value, library)


if __name__ == "__main__":
    unittest.main()
