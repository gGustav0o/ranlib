from __future__ import annotations

from functools import singledispatch

from ranobe_lib.domain.errors import (
    ConflictingTitle,
    DomainError,
    DuplicateCategoryName,
    DuplicateCategorySelection,
    DuplicateItemKey,
    EmptyParts,
    InvalidCategoriesCollection,
    InvalidCategoryName,
    InvalidCategorySelection,
    InvalidItemsCollection,
    InvalidPartNumber,
    InvalidPartsCollection,
    InvalidSearchText,
    InvalidTitle,
    InvalidWorkKey,
    MissingParts,
    MissingTitle,
    NonCanonicalParts,
    SameCategoryMove,
    UnknownCategory,
    UnknownItem,
)
from ranobe_lib.infrastructure.json_errors import (
    DuplicateJsonField,
    InvalidJsonValue,
    InvalidObjectFields,
    JsonCodecError,
    JsonPath,
    JsonSyntaxError,
    UnexpectedJsonType,
)
from ranobe_lib.infrastructure.store_errors import (
    InvalidLibraryFile,
    JsonStoreError,
    LibraryEncodingError,
    LibraryReadError,
    LibraryWriteError,
)


@singledispatch
def describe_error(error: object) -> str:
    return f"Unexpected error: {error!r}."


@describe_error.register
def _describe_domain_error(error: DomainError) -> str:
    return f"Unsupported domain error: {error!r}."


@describe_error.register
def _describe_json_error(error: JsonCodecError) -> str:
    return f"Unsupported JSON error: {error!r}."


@describe_error.register
def _describe_store_error(error: JsonStoreError) -> str:
    return f"Unsupported library file error: {error!r}."


@describe_error.register
def _describe_invalid_categories(error: InvalidCategoriesCollection) -> str:
    return f"Categories must be stored as an immutable tuple, got {error.value!r}."


@describe_error.register
def _describe_invalid_category(error: InvalidCategoryName) -> str:
    return f"Category name must be a non-blank string, got {error.value!r}."


@describe_error.register
def _describe_duplicate_category(error: DuplicateCategoryName) -> str:
    return f"Category {error.name!r} occurs more than once."


@describe_error.register
def _describe_unknown_category(error: UnknownCategory) -> str:
    return f"Unknown category {error.name!r}."


@describe_error.register
def _describe_invalid_selection(error: InvalidCategorySelection) -> str:
    return f"Category selection must be an immutable tuple, got {error.value!r}."


@describe_error.register
def _describe_duplicate_selection(error: DuplicateCategorySelection) -> str:
    return f"Category {error.name!r} was selected more than once."


@describe_error.register
def _describe_same_category(error: SameCategoryMove) -> str:
    return f"Cannot move volumes within category {error.category!r}."


@describe_error.register
def _describe_invalid_items(error: InvalidItemsCollection) -> str:
    return f"Items in category {error.category!r} must be an immutable tuple."


@describe_error.register
def _describe_invalid_key(error: InvalidWorkKey) -> str:
    return f"Item key must be a non-blank string, got {error.value!r}."


@describe_error.register
def _describe_invalid_title(error: InvalidTitle) -> str:
    return f"Title for key {error.key!r} must be non-blank, got {error.value!r}."


@describe_error.register
def _describe_invalid_search_text(error: InvalidSearchText) -> str:
    return f"Search text must be a non-blank string, got {error.value!r}."


@describe_error.register
def _describe_missing_title(error: MissingTitle) -> str:
    return f"A title is required for new key {error.key!r}."


@describe_error.register
def _describe_duplicate_item(error: DuplicateItemKey) -> str:
    return f"Key {error.key!r} occurs more than once in {error.category!r}."


@describe_error.register
def _describe_unknown_item(error: UnknownItem) -> str:
    return f"Unknown key {error.key!r} in category {error.category!r}."


@describe_error.register
def _describe_conflicting_title(error: ConflictingTitle) -> str:
    return (
        f"Title for key {error.key!r} is {error.expected!r}, "
        f"not {error.actual!r}."
    )


@describe_error.register
def _describe_invalid_parts(error: InvalidPartsCollection) -> str:
    return f"Volumes must be provided as an immutable tuple, got {error.value!r}."


@describe_error.register
def _describe_invalid_part(error: InvalidPartNumber) -> str:
    return f"Volume number must be a positive integer, got {error.value!r}."


@describe_error.register
def _describe_empty_parts(error: EmptyParts) -> str:
    return "At least one volume number is required."


@describe_error.register
def _describe_non_canonical_parts(error: NonCanonicalParts) -> str:
    return (
        f"Volumes for {error.key!r} in {error.category!r} are not canonical: "
        f"expected {error.expected!r}, got {error.actual!r}."
    )


@describe_error.register
def _describe_missing_parts(error: MissingParts) -> str:
    return (
        f"Volumes {_render_parts(error.parts)} are missing from key "
        f"{error.key!r} in category {error.category!r}."
    )


@describe_error.register
def _describe_json_syntax(error: JsonSyntaxError) -> str:
    return (
        f"JSON syntax error at line {error.line}, column {error.column}: "
        f"{error.message}."
    )


@describe_error.register
def _describe_duplicate_json_field(error: DuplicateJsonField) -> str:
    return f"JSON field {error.field!r} occurs more than once."


@describe_error.register
def _describe_unexpected_json_type(error: UnexpectedJsonType) -> str:
    return (
        f"Unexpected value at {_render_json_path(error.path)}: "
        f"expected {error.expected}, got {error.actual}."
    )


@describe_error.register
def _describe_invalid_object_fields(error: InvalidObjectFields) -> str:
    details = _render_field_issues(error.missing, error.unknown)
    return f"Invalid fields at {_render_json_path(error.path)}: {details}."


@describe_error.register
def _describe_invalid_json_value(error: InvalidJsonValue) -> str:
    return f"At {_render_json_path(error.path)}: {describe_error(error.error)}"


@describe_error.register
def _describe_read_error(error: LibraryReadError) -> str:
    return f"Cannot read library file {str(error.path)!r}: {error.reason}."


@describe_error.register
def _describe_invalid_file(error: InvalidLibraryFile) -> str:
    return f"Invalid library file {str(error.path)!r}: {describe_error(error.error)}"


@describe_error.register
def _describe_encoding_error(error: LibraryEncodingError) -> str:
    details = describe_error(error.error)
    return f"Cannot encode library file {str(error.path)!r}: {details}"


@describe_error.register
def _describe_write_error(error: LibraryWriteError) -> str:
    return f"Cannot write library file {str(error.path)!r}: {error.reason}."


def _render_parts(parts: tuple[int, ...]) -> str:
    return ", ".join(str(part) for part in parts)


def _render_json_path(path: JsonPath) -> str:
    return "$" + "".join(_render_path_segment(segment) for segment in path)


def _render_path_segment(segment: str | int) -> str:
    if isinstance(segment, int):
        return f"[{segment}]"
    return f".{segment}"


def _render_field_issues(
    missing: tuple[str, ...],
    unknown: tuple[str, ...],
) -> str:
    issues = (
        _render_fields("missing", missing),
        _render_fields("unknown", unknown),
    )
    return "; ".join(issue for issue in issues if issue)


def _render_fields(label: str, fields: tuple[str, ...]) -> str:
    if not fields:
        return ""
    return f"{label} {', '.join(repr(field) for field in fields)}"


__all__ = ("describe_error",)
