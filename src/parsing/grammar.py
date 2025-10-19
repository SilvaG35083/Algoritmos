"""Grammar description and helper utilities.

This module provides a central place where the production rules and metadata
required by the parser live. The first iteration keeps things declarative so
future tooling (documentation, diagrams) can reuse the same definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class Production:
    """Represents a single grammar production."""

    name: str
    expansion: Sequence[str]
    description: str = ""


class Grammar:
    """Stores productions and exposes lookup helpers."""

    def __init__(self, productions: Sequence[Production]) -> None:
        self._productions: Dict[str, List[Production]] = {}
        for production in productions:
            self._productions.setdefault(production.name, []).append(production)

    def expansions_for(self, name: str) -> Sequence[Production]:
        """Return all expansions for a non terminal."""
        return self._productions.get(name, [])

    def as_markdown(self) -> str:
        """Render the grammar as a Markdown table."""
        lines = ["| Non terminal | Expansion | Descripcion |", "| --- | --- | --- |"]
        for key in sorted(self._productions):
            for production in self._productions[key]:
                expansion = " ".join(production.expansion)
                lines.append(f"| `{production.name}` | `{expansion}` | {production.description} |")
        return "\n".join(lines)


DEFAULT_PRODUCTIONS: Sequence[Production] = (
    Production("program", ("declarations", "begin", "statement_list", "end"), "Programa basico"),
    Production("statement", ("assignment",), "Asignacion simple"),
    Production("statement", ("for_loop",), "Bucle for"),
    Production("statement", ("while_loop",), "Bucle while"),
    Production("statement", ("repeat_until",), "Bucle repeat until"),
    Production("statement", ("if_statement",), "Condicional completo"),
)

DEFAULT_GRAMMAR = Grammar(DEFAULT_PRODUCTIONS)
