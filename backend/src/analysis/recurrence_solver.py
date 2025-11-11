"""Utilities for recurrence relations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass(slots=True)
class RecurrenceRelation:
    """Simple representation of a recurrence T(n) = sum(a_i * T(n/b_i)) + f(n)."""

    identifier: str
    recurrence: str
    base_case: str
    notes: str = ""


@dataclass(slots=True)
class RecurrenceSolution:
    """Stores the symbolic solution for a recurrence."""

    theta: str
    upper: str
    lower: str
    justification: str


class RecurrenceSolver:
    """Registry of solvers that can be composed."""

    def __init__(self) -> None:
        self._solvers: Dict[str, Callable[[RecurrenceRelation], Optional[RecurrenceSolution]]] = {}

    def register(self, name: str, handler: Callable[[RecurrenceRelation], Optional[RecurrenceSolution]]) -> None:
        self._solvers[name] = handler

    def solve(self, relation: RecurrenceRelation) -> Optional[RecurrenceSolution]:
        """Try each registered solver until one returns a result."""
        for handler in self._solvers.values():
            result = handler(relation)
            if result is not None:
                return result
        return None

    @classmethod
    def default(cls) -> "RecurrenceSolver":
        solver = cls()
        solver.register("master", solve_with_master_theorem)
        solver.register("substitution", solve_with_substitution)
        return solver


def solve_with_master_theorem(relation: RecurrenceRelation) -> Optional[RecurrenceSolution]:
    """Placeholder master theorem solver."""
    if "T(n/2)" in relation.recurrence and "2*T(n/2)" in relation.recurrence:
        return RecurrenceSolution(
            theta="Theta(n log n)",
            upper="O(n log n)",
            lower="Omega(n log n)",
            justification="Matched balanced divide and conquer form.",
        )
    return None


def solve_with_substitution(relation: RecurrenceRelation) -> Optional[RecurrenceSolution]:
    """Placeholder substitution solver."""
    if relation.recurrence.endswith("+ n"):
        return RecurrenceSolution(
            theta="Theta(n)",
            upper="O(n)",
            lower="Omega(n)",
            justification="Linear recurrence solved by telescoping.",
        )
    return None
