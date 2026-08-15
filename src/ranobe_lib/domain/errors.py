from __future__ import annotations

from dataclasses import dataclass

from ranobe_lib.domain.model import CategoryName, Parts, WorkKey


class DomainError:
    """Marker base class for expected domain failures."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class InvalidCategoriesCollection(DomainError):
    value: object


@dataclass(frozen=True, slots=True)
class InvalidCategoryName(DomainError):
    value: object


@dataclass(frozen=True, slots=True)
class DuplicateCategoryName(DomainError):
    name: CategoryName


@dataclass(frozen=True, slots=True)
class UnknownCategory(DomainError):
    name: CategoryName


@dataclass(frozen=True, slots=True)
class InvalidCategorySelection(DomainError):
    value: object


@dataclass(frozen=True, slots=True)
class DuplicateCategorySelection(DomainError):
    name: CategoryName


@dataclass(frozen=True, slots=True)
class SameCategoryMove(DomainError):
    category: CategoryName


@dataclass(frozen=True, slots=True)
class InvalidItemsCollection(DomainError):
    category: CategoryName
    value: object


@dataclass(frozen=True, slots=True)
class InvalidWorkKey(DomainError):
    value: object


@dataclass(frozen=True, slots=True)
class InvalidTitle(DomainError):
    key: WorkKey
    value: object


@dataclass(frozen=True, slots=True)
class MissingTitle(DomainError):
    key: WorkKey


@dataclass(frozen=True, slots=True)
class DuplicateItemKey(DomainError):
    category: CategoryName
    key: WorkKey


@dataclass(frozen=True, slots=True)
class UnknownItem(DomainError):
    category: CategoryName
    key: WorkKey


@dataclass(frozen=True, slots=True)
class ConflictingTitle(DomainError):
    key: WorkKey
    expected: str
    actual: str


@dataclass(frozen=True, slots=True)
class InvalidPartsCollection(DomainError):
    value: object


@dataclass(frozen=True, slots=True)
class InvalidPartNumber(DomainError):
    value: object


@dataclass(frozen=True, slots=True)
class EmptyParts(DomainError):
    pass


@dataclass(frozen=True, slots=True)
class NonCanonicalParts(DomainError):
    category: CategoryName
    key: WorkKey
    actual: object
    expected: Parts


@dataclass(frozen=True, slots=True)
class MissingParts(DomainError):
    category: CategoryName
    key: WorkKey
    parts: Parts
