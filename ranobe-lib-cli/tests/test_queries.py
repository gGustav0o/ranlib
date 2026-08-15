from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    DuplicateCategorySelection,
    InvalidCategoryName,
    InvalidCategorySelection,
    UnknownCategory,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.queries import list_category_names, select_categories
from ranobe_lib.domain.result import Err, Ok


class CategoryQueriesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.on_hand = Category(
            "on-hand",
            (Item("overlord", "Overlord", (1,)),),
        )
        self.required = Category(
            "required",
            (Item("sao", "Sword Art Online", (2,)),),
        )
        self.necessary = Category("absolutely-necessary")
        self.library = Library(
            categories=(self.on_hand, self.required, self.necessary)
        )

    def test_lists_category_names_in_library_order(self) -> None:
        self.assertEqual(
            list_category_names(self.library),
            ("on-hand", "required", "absolutely-necessary"),
        )

    def test_selects_all_categories_when_selection_is_omitted(self) -> None:
        result = select_categories(self.library)

        self.assertEqual(result, Ok(self.library.categories))
        self.assertIs(result.value, self.library.categories)

    def test_preserves_explicit_selection_order_and_category_boundaries(self) -> None:
        result = select_categories(
            self.library,
            ("required", "on-hand"),
        )

        self.assertEqual(result, Ok((self.required, self.on_hand)))
        self.assertEqual(result.value[0].name, "required")
        self.assertEqual(result.value[0].items[0].key, "sao")
        self.assertEqual(result.value[1].name, "on-hand")

    def test_accepts_an_empty_explicit_selection(self) -> None:
        self.assertEqual(select_categories(self.library, ()), Ok(()))

    def test_rejects_an_unknown_category(self) -> None:
        result = select_categories(self.library, ("on-hand", "unknown"))

        self.assertEqual(result, Err(UnknownCategory("unknown")))

    def test_rejects_duplicate_category_names(self) -> None:
        result = select_categories(self.library, ("required", "required"))

        self.assertEqual(
            result,
            Err(DuplicateCategorySelection("required")),
        )

    def test_rejects_a_mutable_selection_collection(self) -> None:
        categories = ["on-hand"]

        result = select_categories(self.library, categories)

        self.assertEqual(result, Err(InvalidCategorySelection(categories)))

    def test_rejects_an_invalid_category_name(self) -> None:
        result = select_categories(self.library, ("",))

        self.assertEqual(result, Err(InvalidCategoryName("")))


if __name__ == "__main__":
    unittest.main()
