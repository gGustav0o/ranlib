from __future__ import annotations

from dataclasses import dataclass

from ranobe_lib.domain.errors import DomainError
from ranobe_lib.domain.model import Category, CategoryName, Item, Library
from ranobe_lib.domain.queries import select_categories
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import validate_search_text


@dataclass(frozen=True, slots=True)
class CategoryMatches:
    """Matching items projected from one library category."""

    name: CategoryName
    items: tuple[Item, ...]


def search_items(
    library: Library,
    text: object,
    categories: object | None = None,
) -> Result[tuple[CategoryMatches, ...], DomainError]:
    """Find key or title substrings within selected categories."""

    text_result = validate_search_text(text)
    if isinstance(text_result, Err):
        return text_result

    categories_result = select_categories(library, categories)
    if isinstance(categories_result, Err):
        return categories_result

    normalized_text = _normalize_search_text(text_result.value)
    matches = tuple(
        _search_category(category, normalized_text)
        for category in categories_result.value
    )
    return Ok(tuple(match for match in matches if match.items))


def _normalize_search_text(value: str) -> str:
    return value.strip().casefold()


def _search_category(category: Category, text: str) -> CategoryMatches:
    return CategoryMatches(
        name=category.name,
        items=tuple(item for item in category.items if _matches(item, text)),
    )


def _matches(item: Item, text: str) -> bool:
    return text in item.key.casefold() or text in item.title.casefold()


__all__ = ("CategoryMatches", "search_items")
