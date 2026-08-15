from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import (
    DuplicateCategoryName,
    EmptyParts,
    InvalidPartNumber,
    NonCanonicalParts,
)
from ranobe_lib.domain.model import Category, Item, Library
from ranobe_lib.domain.result import Err, Ok
from ranobe_lib.infrastructure.json_codec import (
    decode_library,
    dumps_library,
    encode_library,
    loads_library,
)
from ranobe_lib.infrastructure.json_errors import (
    DuplicateJsonField,
    InvalidJsonValue,
    InvalidObjectFields,
    JsonSyntaxError,
    UnexpectedJsonType,
)


class DecodeLibraryTest(unittest.TestCase):
    def test_decodes_a_canonical_library(self) -> None:
        value = [
            {
                "category": "on-hand",
                "items": [
                    {
                        "key": "overlord",
                        "title": "Overlord",
                        "parts": [1, 2, 3],
                    }
                ],
            }
        ]

        result = decode_library(value)

        self.assertEqual(
            result,
            Ok(
                Library(
                    categories=(
                        Category(
                            "on-hand",
                            (Item("overlord", "Overlord", (1, 2, 3)),),
                        ),
                    )
                )
            ),
        )

    def test_reports_the_path_of_an_invalid_part(self) -> None:
        value = [
            {
                "category": "on-hand",
                "items": [
                    {
                        "key": "overlord",
                        "title": "Overlord",
                        "parts": [1, True],
                    }
                ],
            }
        ]

        result = decode_library(value)

        self.assertEqual(
            result,
            Err(
                InvalidJsonValue(
                    path=(0, "items", 0, "parts", 1),
                    error=InvalidPartNumber(True),
                )
            ),
        )

    def test_rejects_non_canonical_stored_parts(self) -> None:
        value = [
            {
                "category": "on-hand",
                "items": [
                    {
                        "key": "overlord",
                        "title": "Overlord",
                        "parts": [2, 1, 2],
                    }
                ],
            }
        ]

        result = decode_library(value)

        self.assertEqual(
            result,
            Err(
                InvalidJsonValue(
                    path=(0, "items", 0, "parts"),
                    error=NonCanonicalParts(
                        category="on-hand",
                        key="overlord",
                        actual=(2, 1, 2),
                        expected=(1, 2),
                    ),
                )
            ),
        )

    def test_rejects_an_item_without_parts(self) -> None:
        value = [
            {
                "category": "on-hand",
                "items": [
                    {
                        "key": "overlord",
                        "title": "Overlord",
                        "parts": [],
                    }
                ],
            }
        ]

        result = decode_library(value)

        self.assertEqual(
            result,
            Err(
                InvalidJsonValue(
                    path=(0, "items", 0, "parts"),
                    error=EmptyParts(),
                )
            ),
        )

    def test_reports_missing_and_unknown_fields_together(self) -> None:
        value = [{"category": "on-hand", "entries": []}]

        result = decode_library(value)

        self.assertEqual(
            result,
            Err(
                InvalidObjectFields(
                    path=(0,),
                    missing=("items",),
                    unknown=("entries",),
                )
            ),
        )

    def test_rejects_a_non_array_root(self) -> None:
        result = decode_library({"category": "on-hand"})

        self.assertEqual(
            result,
            Err(UnexpectedJsonType((), expected="array", actual="object")),
        )

    def test_wraps_cross_category_invariant_errors(self) -> None:
        value = [
            {"category": "required", "items": []},
            {"category": "required", "items": []},
        ]

        result = decode_library(value)

        self.assertEqual(
            result,
            Err(InvalidJsonValue((), DuplicateCategoryName("required"))),
        )


class LoadsLibraryTest(unittest.TestCase):
    def test_reports_json_syntax_errors(self) -> None:
        result = loads_library('[{"category":]')

        self.assertIsInstance(result, Err)
        self.assertIsInstance(result.error, JsonSyntaxError)
        self.assertEqual(result.error.line, 1)
        self.assertGreater(result.error.column, 0)

    def test_rejects_duplicate_json_fields(self) -> None:
        result = loads_library(
            '[{"category":"on-hand","category":"required","items":[]}]'
        )

        self.assertEqual(result, Err(DuplicateJsonField("category")))


class EncodeLibraryTest(unittest.TestCase):
    def test_serializes_stable_human_readable_unicode_json(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("ascendance", "Восхождение книжного червя", (1, 2)),),
                ),
            )
        )

        result = dumps_library(library)

        expected = """[
    {
        "category": "on-hand",
        "items": [
            {
                "key": "ascendance",
                "title": "Восхождение книжного червя",
                "parts": [
                    1,
                    2
                ]
            }
        ]
    }
]
"""
        self.assertEqual(result, Ok(expected))
        self.assertEqual(loads_library(result.value), Ok(library))

    def test_encodes_fields_in_schema_order(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (1,)),),
                ),
            )
        )

        result = encode_library(library)

        self.assertIsInstance(result, Ok)
        self.assertEqual(
            result.value,
            [
                {
                    "category": "on-hand",
                    "items": [
                        {
                            "key": "overlord",
                            "title": "Overlord",
                            "parts": [1],
                        }
                    ],
                }
            ],
        )

    def test_refuses_to_encode_a_non_canonical_library(self) -> None:
        library = Library(
            categories=(
                Category(
                    "on-hand",
                    (Item("overlord", "Overlord", (2, 1)),),
                ),
            )
        )

        result = dumps_library(library)

        self.assertEqual(
            result,
            Err(
                NonCanonicalParts(
                    category="on-hand",
                    key="overlord",
                    actual=(2, 1),
                    expected=(1, 2),
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
