from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from ranobe_lib.domain.result import Ok
from ranobe_lib.infrastructure.json_codec import dumps_library
from ranobe_lib.infrastructure.json_store import load_json_library


_PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DistributionContractTest(unittest.TestCase):
    def test_exposes_the_existing_main_as_the_console_script(self) -> None:
        configuration = tomllib.loads(
            (_PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual(configuration["project"]["name"], "ranobe-lib")
        self.assertEqual(
            configuration["project"]["scripts"]["ranobe-lib"],
            "ranobe_lib.cli.main:main",
        )
        self.assertEqual(
            configuration["tool"]["setuptools"]["package-dir"],
            {"": "src"},
        )

    def test_example_is_a_canonical_library(self) -> None:
        path = _PROJECT_ROOT / "example" / "ranobe-lib.json"
        result = load_json_library(path)

        self.assertIsInstance(result, Ok)
        self.assertEqual(
            tuple(category.name for category in result.value.categories),
            ("on-hand", "required", "absolutely-necessary"),
        )
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            dumps_library(result.value).value,
        )


if __name__ == "__main__":
    unittest.main()
