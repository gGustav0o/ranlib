from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    DuplicateCategoryName,
    DuplicateItemKey,
    InvalidCategoriesCollection,
    InvalidCategoryName,
    InvalidItemsCollection,
    InvalidWorkKey,
    NonCanonicalParts,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.result import Err, Ok
from ranobe_lib.domain.validation import validate_library


class ValidateLibraryTest(unittest.TestCase):
    def test_accepts_a_canonical_library(self) -> None:
        library = Library(
            categories=(
                Category(
                    name="on-hand",
                    items=(Item("overlord", "Overlord", (1, 2)),),
                ),
                Category(
                    name="required",
                    items=(Item("overlord", "Overlord", (3,)),),
                ),
            )
        )

        result = validate_library(library)

        self.assertEqual(result, Ok(library))
        self.assertIs(result.value, library)

    def test_rejects_a_mutable_categories_collection(self) -> None:
        categories = [Category("on-hand")]
        library = Library(categories=categories)  # type: ignore[arg-type]

        result = validate_library(library)

        self.assertEqual(result, Err(InvalidCategoriesCollection(categories)))

    def test_stops_after_an_invalid_category_name(self) -> None:
        invalid_name: object = []
        category = Category(invalid_name)  # type: ignore[arg-type]
        library = Library(categories=(category,))

        result = validate_library(library)

        self.assertEqual(result, Err(InvalidCategoryName(invalid_name)))

    def test_rejects_a_mutable_items_collection(self) -> None:
        items = [Item("overlord", "Overlord", (1,))]
        category = Category("on-hand", items)  # type: ignore[arg-type]
        library = Library(categories=(category,))

        result = validate_library(library)

        self.assertEqual(
            result,
            Err(InvalidItemsCollection(category="on-hand", value=items)),
        )

    def test_stops_after_an_invalid_item_key(self) -> None:
        invalid_key: object = []
        item = Item(invalid_key, "Overlord", (1,))  # type: ignore[arg-type]
        library = Library(categories=(Category("on-hand", (item,)),))

        result = validate_library(library)

        self.assertEqual(result, Err(InvalidWorkKey(invalid_key)))

    def test_rejects_duplicate_category_names(self) -> None:
        library = Library(
            categories=(Category("required"), Category("required"))
        )

        result = validate_library(library)

        self.assertEqual(result, Err(DuplicateCategoryName("required")))

    def test_rejects_duplicate_keys_within_a_category(self) -> None:
        library = Library(
            categories=(
                Category(
                    name="required",
                    items=(
                        Item("sao", "Sword Art Online", (1,)),
                        Item("sao", "Sword Art Online", (2,)),
                    ),
                ),
            )
        )

        result = validate_library(library)

        self.assertEqual(result, Err(DuplicateItemKey("required", "sao")))

    def test_rejects_different_titles_for_the_same_key(self) -> None:
        library = Library(
            categories=(
                Category("on-hand", (Item("sao", "SAO", (1,)),)),
                Category(
                    "required",
                    (Item("sao", "Sword Art Online", (2,)),),
                ),
            )
        )

        result = validate_library(library)

        self.assertEqual(
            result,
            Err(ConflictingTitle("sao", "SAO", "Sword Art Online")),
        )

    def test_rejects_unsorted_or_duplicate_stored_parts(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (2, 1, 2)),),
                ),
            )
        )

        result = validate_library(library)

        self.assertEqual(
            result,
            Err(
                NonCanonicalParts(
                    category="on-hand",
                    key="overlord",
                    actual=(2, 1, 2),
                    expected=(1, 2),
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
