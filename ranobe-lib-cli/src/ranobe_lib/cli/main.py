# src/ranobe_lib/cli/main.py

from __future__ import annotations

import sys
from collections.abc import Sequence

from ranobe_lib.cli.parser import parse_invocation
from ranobe_lib.cli.runner import run


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _resolve_arguments(argv)
    invocation = parse_invocation(arguments)

    return run(invocation)


def _resolve_arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
