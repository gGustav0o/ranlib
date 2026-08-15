from __future__ import annotations

import unittest

from ranobe_lib.domain.errors import EmptyParts, InvalidPartNumber
from ranobe_lib.domain.normalize import normalize_parts
from ranobe_lib.domain.result import Err, Ok


class NormalizePartsTest(unittest.TestCase):
    def test_sorts_and_deduplicates_parts(self) -> None:
        result = normalize_parts((3, 1, 2, 3, 1))

        self.assertEqual(result, Ok((1, 2, 3)))

    def test_rejects_empty_parts(self) -> None:
        result = normalize_parts(())

        self.assertEqual(result, Err(EmptyParts()))

    def test_rejects_boolean_part_numbers(self) -> None:
        for value in (True, False):
            with self.subTest(value=value):
                result = normalize_parts((1, value))

                self.assertEqual(result, Err(InvalidPartNumber(value)))

    def test_rejects_non_positive_and_non_integer_parts(self) -> None:
        for value in (0, -1, 1.5, "2"):
            with self.subTest(value=value):
                result = normalize_parts((value,))

                self.assertEqual(result, Err(InvalidPartNumber(value)))


if __name__ == "__main__":
    unittest.main()
