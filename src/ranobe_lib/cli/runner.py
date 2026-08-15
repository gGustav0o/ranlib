from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TypeAlias, TypeVar, assert_never

from ranobe_lib.application import services
from ranobe_lib.application.commands import (
    AddParts,
    Command,
    ListCategories,
    ListItems,
    MoveParts,
    RemoveItem,
    RemoveParts,
)
from ranobe_lib.application.ports import LoadLibrary, SaveLibrary
from ranobe_lib.cli.errors import CliExecutionError
from ranobe_lib.cli.model import (
    CategoriesListed,
    CliOutput,
    CommandCompleted,
    Invocation,
    ItemsListed,
)
from ranobe_lib.domain.model import Library
from ranobe_lib.domain.result import Err, Ok, Result
from ranobe_lib.infrastructure.json_store import (
    load_json_library,
    save_json_library,
)
from ranobe_lib.infrastructure.store_errors import (
    JsonStoreLoadError,
    JsonStoreSaveError,
)


ValueT = TypeVar("ValueT")
ErrorT = TypeVar("ErrorT")
QueryCommand: TypeAlias = ListCategories | ListItems
MutationCommand: TypeAlias = AddParts | RemoveParts | RemoveItem | MoveParts


def run(invocation: Invocation) -> Result[CliOutput, CliExecutionError]:
    """Bind a library path to effects and execute one invocation."""

    load = partial(load_json_library, invocation.path)
    save = partial(save_json_library, invocation.path)
    return execute_command(invocation.command, load=load, save=save)


def execute_command(
    command: Command,
    *,
    load: LoadLibrary[JsonStoreLoadError],
    save: SaveLibrary[JsonStoreSaveError],
) -> Result[CliOutput, CliExecutionError]:
    """Dispatch a closed application command without performing presentation."""

    if isinstance(command, (ListCategories, ListItems)):
        return _execute_query(command, load)
    return _execute_mutation(command, load, save)


def _execute_query(
    command: QueryCommand,
    load: LoadLibrary[JsonStoreLoadError],
) -> Result[CliOutput, CliExecutionError]:
    if isinstance(command, ListCategories):
        result = services.list_categories(load=load)
        return _map_output(result, CategoriesListed)
    if isinstance(command, ListItems):
        result = services.list_items(command, load=load)
        return _map_output(result, ItemsListed)
    assert_never(command)


def _execute_mutation(
    command: MutationCommand,
    load: LoadLibrary[JsonStoreLoadError],
    save: SaveLibrary[JsonStoreSaveError],
) -> Result[CliOutput, CliExecutionError]:
    if isinstance(command, AddParts):
        return _complete(services.add_parts(command, load=load, save=save))
    if isinstance(command, RemoveParts):
        return _complete(services.remove_parts(command, load=load, save=save))
    if isinstance(command, RemoveItem):
        return _complete(services.remove_item(command, load=load, save=save))
    if isinstance(command, MoveParts):
        return _complete(services.move_parts(command, load=load, save=save))
    assert_never(command)


def _map_output(
    result: Result[ValueT, ErrorT],
    build: Callable[[ValueT], CliOutput],
) -> Result[CliOutput, ErrorT]:
    if isinstance(result, Err):
        return result
    return Ok(build(result.value))


def _complete(
    result: Result[Library, ErrorT],
) -> Result[CliOutput, ErrorT]:
    if isinstance(result, Err):
        return result
    return Ok(CommandCompleted())


__all__ = ("execute_command", "run")
