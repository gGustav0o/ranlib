from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import TypeAlias, TypeVar

from ranobe_lib.domain.errors import DomainError, NonCanonicalParts
from ranobe_lib.domain.model import (
    Category,
    CategoryName,
    Item,
    Library,
    Parts,
    WorkKey,
)
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import (
    validate_category_name,
    validate_library,
    validate_title,
    validate_work_key,
)
from ranobe_lib.infrastructure.json_errors import (
    DuplicateJsonField,
    InvalidJsonValue,
    InvalidObjectFields,
    JsonDecodingError,
    JsonPath,
    JsonSyntaxError,
    UnexpectedJsonType,
)


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = (
    JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
)

DecodedT = TypeVar("DecodedT")
DomainValueT = TypeVar("DomainValueT")
DomainErrorT = TypeVar("DomainErrorT", bound=DomainError)

_CATEGORY_FIELDS = frozenset(("category", "items"))
_ITEM_FIELDS = frozenset(("key", "title", "parts"))


class _DuplicateFieldError(ValueError):
    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(field)


def loads_library(text: str) -> Result[Library, JsonDecodingError]:
    """Decode a JSON document into a canonical immutable library."""

    parsed_result = _parse_json(text)
    if isinstance(parsed_result, Err):
        return parsed_result
    return decode_library(parsed_result.value)


def decode_library(value: object) -> Result[Library, JsonDecodingError]:
    """Decode a JSON-compatible value without performing any I/O."""

    categories_result = _decode_array(value, (), _decode_category)
    if isinstance(categories_result, Err):
        return categories_result

    library = Library(categories_result.value)
    validation_result = validate_library(library)
    if isinstance(validation_result, Err):
        return Err(InvalidJsonValue((), validation_result.error))
    return Ok(library)


def encode_library(
    library: Library,
) -> Result[list[JsonValue], DomainError]:
    """Encode a canonical library into a JSON-compatible value."""

    validation_result = validate_library(library)
    if isinstance(validation_result, Err):
        return validation_result
    return Ok([_encode_category(category) for category in library.categories])


def dumps_library(library: Library) -> Result[str, DomainError]:
    """Serialize a canonical library into stable human-readable JSON."""

    encoded_result = encode_library(library)
    if isinstance(encoded_result, Err):
        return encoded_result

    text = json.dumps(
        encoded_result.value,
        ensure_ascii=False,
        indent=4,
    )
    return Ok(f"{text}\n")


def _parse_json(text: str) -> Result[object, JsonDecodingError]:
    try:
        return Ok(json.loads(text, object_pairs_hook=_object_from_pairs))
    except _DuplicateFieldError as error:
        return Err(DuplicateJsonField(error.field))
    except json.JSONDecodeError as error:
        return Err(
            JsonSyntaxError(
                message=error.msg,
                line=error.lineno,
                column=error.colno,
            )
        )


def _object_from_pairs(
    pairs: Iterable[tuple[str, JsonValue]],
) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for field, value in pairs:
        if field in result:
            raise _DuplicateFieldError(field)
        result[field] = value
    return result


def _decode_category(
    value: object,
    path: JsonPath,
) -> Result[Category, JsonDecodingError]:
    object_result = _expect_object(value, path, _CATEGORY_FIELDS)
    if isinstance(object_result, Err):
        return object_result
    fields = object_result.value

    name_result = _at_json_path(
        (*path, "category"),
        validate_category_name(fields["category"]),
    )
    if isinstance(name_result, Err):
        return name_result

    return _decode_category_items(fields, path, name_result.value)


def _decode_category_items(
    fields: dict[str, JsonValue],
    path: JsonPath,
    name: CategoryName,
) -> Result[Category, JsonDecodingError]:
    def decode_item(value: object, item_path: JsonPath) -> Result[
        Item, JsonDecodingError
    ]:
        return _decode_item(value, item_path, name)

    items_result = _decode_array(
        fields["items"],
        (*path, "items"),
        decode_item,
    )
    if isinstance(items_result, Err):
        return items_result
    return Ok(Category(name=name, items=items_result.value))


def _decode_item(
    value: object,
    path: JsonPath,
    category: CategoryName,
) -> Result[Item, JsonDecodingError]:
    object_result = _expect_object(value, path, _ITEM_FIELDS)
    if isinstance(object_result, Err):
        return object_result
    fields = object_result.value

    key_result = _decode_work_key(fields, path)
    if isinstance(key_result, Err):
        return key_result

    return _decode_item_details(
        fields,
        path=path,
        category=category,
        key=key_result.value,
    )


def _decode_item_details(
    fields: dict[str, JsonValue],
    *,
    path: JsonPath,
    category: CategoryName,
    key: WorkKey,
) -> Result[Item, JsonDecodingError]:
    title_result = _decode_title(fields, path, key)
    if isinstance(title_result, Err):
        return title_result

    parts_result = _decode_parts(
        fields["parts"],
        path=(*path, "parts"),
        category=category,
        key=key,
    )
    if isinstance(parts_result, Err):
        return parts_result

    return Ok(Item(key=key, title=title_result.value, parts=parts_result.value))


def _decode_work_key(
    fields: dict[str, JsonValue],
    path: JsonPath,
) -> Result[WorkKey, JsonDecodingError]:
    return _at_json_path(
        (*path, "key"),
        validate_work_key(fields["key"]),
    )


def _decode_title(
    fields: dict[str, JsonValue],
    path: JsonPath,
    key: WorkKey,
) -> Result[str, JsonDecodingError]:
    return _at_json_path(
        (*path, "title"),
        validate_title(key, fields["title"]),
    )


def _decode_parts(
    value: object,
    *,
    path: JsonPath,
    category: CategoryName,
    key: WorkKey,
) -> Result[Parts, JsonDecodingError]:
    parts_result = _decode_array(value, path, _decode_part)
    if isinstance(parts_result, Err):
        return parts_result

    return _require_canonical_parts(
        parts_result.value,
        path=path,
        category=category,
        key=key,
    )


def _require_canonical_parts(
    parts: Parts,
    *,
    path: JsonPath,
    category: CategoryName,
    key: WorkKey,
) -> Result[Parts, JsonDecodingError]:
    normalized_result = _at_json_path(path, normalize_parts(parts))
    if isinstance(normalized_result, Err):
        return normalized_result
    if normalized_result.value != parts:
        return _non_canonical_parts_error(
            path=path,
            category=category,
            key=key,
            actual=parts,
            expected=normalized_result.value,
        )
    return normalized_result


def _non_canonical_parts_error(
    *,
    path: JsonPath,
    category: CategoryName,
    key: WorkKey,
    actual: Parts,
    expected: Parts,
) -> Err[InvalidJsonValue]:
    error = NonCanonicalParts(
        category=category,
        key=key,
        actual=actual,
        expected=expected,
    )
    return Err(InvalidJsonValue(path, error))


def _decode_part(
    value: object,
    path: JsonPath,
) -> Result[int, JsonDecodingError]:
    normalized_result = _at_json_path(path, normalize_parts((value,)))
    if isinstance(normalized_result, Err):
        return normalized_result
    return Ok(normalized_result.value[0])


def _at_json_path(
    path: JsonPath,
    result: Result[DomainValueT, DomainErrorT],
) -> Result[DomainValueT, JsonDecodingError]:
    if isinstance(result, Err):
        return Err(InvalidJsonValue(path, result.error))
    return result


def _expect_object(
    value: object,
    path: JsonPath,
    expected_fields: frozenset[str],
) -> Result[dict[str, JsonValue], JsonDecodingError]:
    if not isinstance(value, dict):
        return Err(UnexpectedJsonType(path, "object", _json_type_name(value)))

    fields = set(value)
    missing = tuple(sorted(expected_fields - fields))
    unknown = tuple(sorted(fields - expected_fields))
    if missing or unknown:
        return Err(InvalidObjectFields(path, missing, unknown))
    return Ok(value)


def _decode_array(
    value: object,
    path: JsonPath,
    decoder: Callable[
        [object, JsonPath],
        Result[DecodedT, JsonDecodingError],
    ],
) -> Result[tuple[DecodedT, ...], JsonDecodingError]:
    if not isinstance(value, list):
        return Err(UnexpectedJsonType(path, "array", _json_type_name(value)))

    decoded: list[DecodedT] = []
    for index, entry in enumerate(value):
        entry_result = decoder(entry, (*path, index))
        if isinstance(entry_result, Err):
            return entry_result
        decoded.append(entry_result.value)
    return Ok(tuple(decoded))


def _json_type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _encode_category(category: Category) -> dict[str, JsonValue]:
    return {
        "category": category.name,
        "items": [_encode_item(item) for item in category.items],
    }


def _encode_item(item: Item) -> dict[str, JsonValue]:
    return {
        "key": item.key,
        "title": item.title,
        "parts": list(item.parts),
    }
