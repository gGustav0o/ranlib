from __future__ import annotations

from dataclasses import dataclass

from ranobe_lib.domain.errors import DomainError
from ranobe_lib.domain.model import CategoryName, Parts, WorkKey
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.domain.validation import validate_category_name, validate_work_key


@dataclass(frozen=True, slots=True)
class PartsInput:
    category: CategoryName
    key: WorkKey
    parts: Parts


def validate_parts_input(
    *,
    category: object,
    key: object,
    parts: object,
) -> Result[PartsInput, DomainError]:
    identity_result = validate_identity(category=category, key=key)
    if isinstance(identity_result, Err):
        return identity_result

    parts_result = normalize_parts(parts)
    if isinstance(parts_result, Err):
        return parts_result

    category_name, work_key = identity_result.value
    return Ok(PartsInput(category_name, work_key, parts_result.value))


def validate_identity(
    *,
    category: object,
    key: object,
) -> Result[tuple[CategoryName, WorkKey], DomainError]:
    category_result = validate_category_name(category)
    if isinstance(category_result, Err):
        return category_result

    key_result = validate_work_key(key)
    if isinstance(key_result, Err):
        return key_result

    return Ok((category_result.value, key_result.value))
