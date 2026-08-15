from __future__ import annotations

from ranobe_lib.domain.errors import (
    DomainError,
    DuplicateCategorySelection,
    InvalidCategorySelection,
    UnknownCategory,
)
from ranobe_lib.domain.model import Category, CategoryName, Library
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import validate_category_name


def list_category_names(library: Library) -> tuple[CategoryName, ...]:
    """Return category names in their canonical file order."""

    return tuple(category.name for category in library.categories)


def select_categories(
    library: Library,
    categories: object | None = None,
) -> Result[tuple[Category, ...], DomainError]:
    """Select categories without flattening their item collections."""

    if categories is None:
        return Ok(library.categories)

    names_result = _validate_selection(categories)
    if isinstance(names_result, Err):
        return names_result
    return _select_known_categories(library, names_result.value)


def _validate_selection(
    categories: object,
) -> Result[tuple[CategoryName, ...], DomainError]:
    if not isinstance(categories, tuple):
        return Err(InvalidCategorySelection(categories))

    names_result = _validate_category_names(categories)
    if isinstance(names_result, Err):
        return names_result
    return _reject_duplicate_names(names_result.value)


def _validate_category_names(
    categories: tuple[object, ...],
) -> Result[tuple[CategoryName, ...], DomainError]:
    names: list[CategoryName] = []
    for category in categories:
        result = validate_category_name(category)
        if isinstance(result, Err):
            return result
        names.append(result.value)
    return Ok(tuple(names))


def _reject_duplicate_names(
    names: tuple[CategoryName, ...],
) -> Result[tuple[CategoryName, ...], DuplicateCategorySelection]:
    duplicate = _first_duplicate(names)
    if duplicate is not None:
        return Err(DuplicateCategorySelection(duplicate))
    return Ok(names)


def _first_duplicate(names: tuple[CategoryName, ...]) -> CategoryName | None:
    return next(
        (name for index, name in enumerate(names) if name in names[:index]),
        None,
    )


def _select_known_categories(
    library: Library,
    names: tuple[CategoryName, ...],
) -> Result[tuple[Category, ...], UnknownCategory]:
    selected: list[Category] = []
    for name in names:
        category = _category_named(library, name)
        if category is None:
            return Err(UnknownCategory(name))
        selected.append(category)
    return Ok(tuple(selected))


def _category_named(library: Library, name: CategoryName) -> Category | None:
    return next(
        (category for category in library.categories if category.name == name),
        None,
    )


__all__ = ("list_category_names", "select_categories")
