from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    DuplicateCategorySelection,
    InvalidSearchText,
    UnknownCategory,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.result import Err, Ok
from ranobe_lib.domain.search import CategoryMatches, search_items


class SearchItemsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sao = Item("sao", "Sword Art Online", (1,))
        self.overlord = Item("overlord", "Overlord", (2,))
        self.artbook = Item("artbook", "A Guide to Manga", (3,))
        self.spice = Item("spice-and-wolf", "Spice and Wolf", (4,))
        self.library = Library(
            (
                Category("on-hand", (self.sao, self.overlord)),
                Category("required", (self.artbook, self.spice)),
                Category("completed"),
            )
        )

    def test_matches_keys_and_titles_without_case_sensitivity(self) -> None:
        result = search_items(self.library, "  aRt  ")

        self.assertEqual(
            result,
            Ok(
                (
                    CategoryMatches("on-hand", (self.sao,)),
                    CategoryMatches("required", (self.artbook,)),
                )
            ),
        )
        self.assertIs(result.value[0].items[0], self.sao)

    def test_preserves_selected_category_order(self) -> None:
        result = search_items(
            self.library,
            "art",
            ("required", "on-hand"),
        )

        self.assertEqual(
            result,
            Ok(
                (
                    CategoryMatches("required", (self.artbook,)),
                    CategoryMatches("on-hand", (self.sao,)),
                )
            ),
        )

    def test_omits_categories_without_matches(self) -> None:
        self.assertEqual(
            search_items(self.library, "lord"),
            Ok((CategoryMatches("on-hand", (self.overlord,)),)),
        )

    def test_returns_an_empty_success_when_nothing_matches(self) -> None:
        self.assertEqual(search_items(self.library, "missing"), Ok(()))

    def test_accepts_an_empty_explicit_category_selection(self) -> None:
        self.assertEqual(search_items(self.library, "art", ()), Ok(()))

    def test_rejects_invalid_search_text(self) -> None:
        for value in ("", "   ", None, 42):
            with self.subTest(value=value):
                self.assertEqual(
                    search_items(self.library, value),
                    Err(InvalidSearchText(value)),
                )

    def test_reuses_category_selection_validation(self) -> None:
        self.assertEqual(
            search_items(self.library, "art", ("unknown",)),
            Err(UnknownCategory("unknown")),
        )
        self.assertEqual(
            search_items(self.library, "art", ("on-hand", "on-hand")),
            Err(DuplicateCategorySelection("on-hand")),
        )


if __name__ == "__main__":
    unittest.main()
