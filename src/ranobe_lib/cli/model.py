from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from ranobe_lib.application.commands import Command
from ranobe_lib.domain.model import Category, CategoryName
from ranobe_lib.domain.search import CategoryMatches


@dataclass(frozen=True, slots=True)
class Invocation:
    path: Path
    command: Command


@dataclass(frozen=True, slots=True)
class HelpRequested:
    text: str


ParsedInvocation: TypeAlias = Invocation | HelpRequested


@dataclass(frozen=True, slots=True)
class CategoriesListed:
    names: tuple[CategoryName, ...]


@dataclass(frozen=True, slots=True)
class ItemsListed:
    categories: tuple[Category, ...]


@dataclass(frozen=True, slots=True)
class SearchResultsFound:
    matches: tuple[CategoryMatches, ...]


@dataclass(frozen=True, slots=True)
class CommandCompleted:
    pass


CliOutput: TypeAlias = (
    CategoriesListed | ItemsListed | SearchResultsFound | CommandCompleted
)


__all__ = (
    "CategoriesListed",
    "CliOutput",
    "CommandCompleted",
    "HelpRequested",
    "Invocation",
    "ItemsListed",
    "ParsedInvocation",
    "SearchResultsFound",
)
