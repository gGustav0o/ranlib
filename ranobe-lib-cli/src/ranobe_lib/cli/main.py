from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from ranobe_lib.cli.model import HelpRequested, Invocation
from ranobe_lib.cli.parser import parse_invocation
from ranobe_lib.cli.render import (
    render_execution_error,
    render_output,
    render_parse_error,
)
from ranobe_lib.cli.runner import run
from ranobe_lib.domain.result import Err


_SUCCESS = 0
_EXECUTION_FAILURE = 1
_USAGE_FAILURE = 2


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    arguments = _resolve_arguments(argv)
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr
    return run_cli(arguments, stdout=output_stream, stderr=error_stream)


def run_cli(
    arguments: Sequence[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    parsed_result = parse_invocation(arguments)
    if isinstance(parsed_result, Err):
        _write(stderr, render_parse_error(parsed_result.error))
        return _USAGE_FAILURE
    return _run_parsed(parsed_result.value, stdout, stderr)


def _run_parsed(
    parsed: Invocation | HelpRequested,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if isinstance(parsed, HelpRequested):
        _write(stdout, parsed.text)
        return _SUCCESS
    return _run_invocation(parsed, stdout, stderr)


def _run_invocation(
    invocation: Invocation,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    result = run(invocation)
    if isinstance(result, Err):
        _write(stderr, render_execution_error(result.error))
        return _EXECUTION_FAILURE
    _write(stdout, render_output(result.value))
    return _SUCCESS


def _resolve_arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def _write(stream: TextIO, text: str) -> None:
    if text:
        stream.write(text)


if __name__ == "__main__":
    raise SystemExit(main())
