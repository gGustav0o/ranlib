# ranobe-lib

## Installation

Install the project from its root directory:

```console
python -m pip install .
```

This installs the `ranobe-lib` command. Use `--help` to inspect the complete
command syntax:

```console
ranobe-lib --help
ranobe-lib add-parts --help
```

## Library path

Commands use `ranobe-lib.json` in the current directory by default. Select a
different file with the global `--file` option, placed before the command:

```console
ranobe-lib --file example/ranobe-lib.json list-items
```

The file must already exist. Categories are defined by that file and are not
created, renamed, or removed by the CLI.

## Commands

List category names:

```console
ranobe-lib list-categories
```

List every category, or select one or more categories without flattening their
results:

```console
ranobe-lib list-items
ranobe-lib list-items --category on-hand --category required
```

Add volumes to an existing item:

```console
ranobe-lib add-parts --category on-hand --key overlord 7 8
```

Creating a new item additionally requires a title:

```console
ranobe-lib add-parts --category required --key spice-and-wolf --title "Spice and Wolf" 1 2
```

Remove selected volumes or an entire item entry:

```console
ranobe-lib remove-parts --category on-hand --key overlord 2 3
ranobe-lib remove-item --category required --key spice-and-wolf
```

Move selected volumes between categories:

```console
ranobe-lib move-parts --source on-hand --destination required --key overlord 4 5
```

## Data contract

A complete canonical file is available at
[`example/ranobe-lib.json`](example/ranobe-lib.json).

The storage contract is deliberately strict:

- category names are unique;
- item keys are unique within a category;
- equal keys across categories must have equal titles;
- titles do not have to be unique;
- `parts` contains sorted, unique positive integers;
- booleans are not accepted as volume numbers;
- an item with empty `parts` is not stored;
- missing, unknown, duplicate, or contradictory fields are errors.

`add-parts` merges and normalizes volume numbers. `remove-parts` deletes the item
after its final volume is removed. `move-parts` is atomic: if any requested
volume is absent from the source, the file is left unchanged. Moving within the
same category is an error.

Successful mutations replace the original file atomically. Output is encoded
as UTF-8 with four-space indentation, unescaped Unicode, stable field order,
and a final newline.

## Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | The command or help request succeeded. |
| `1` | Loading, validation, domain execution, or saving failed. |
| `2` | Command-line arguments are invalid. |

Errors are written to standard error. Successful output and help are written
to standard output.

## Development

Run the standard-library test suite from the project root:

```console
python -m unittest discover -s tests
```
