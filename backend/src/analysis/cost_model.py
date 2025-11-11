"""Definitions and helpers for instruction cost models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, MutableMapping


@dataclass(slots=True)
class CostModel:
    """Stores base operation costs and allows user customization."""

    base_costs: MutableMapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.base_costs:
            self.base_costs.update(default_costs())

    def cost_for(self, operation: str) -> float:
        """Return the cost assigned to a given operation."""
        return self.base_costs.get(operation, self.base_costs["default"])

    def override(self, mapping: Mapping[str, float]) -> None:
        """Override a subset of costs."""
        self.base_costs.update(mapping)

    def available_operations(self) -> Iterable[str]:
        return sorted(self.base_costs.keys())


def default_costs() -> Dict[str, float]:
    """Default instruction costs (unit steps)."""
    return {
        "default": 1.0,
        "assignment": 1.0,
        "comparison": 1.0,
        "arithmetic": 1.0,
        "array_access": 2.0,
        "field_access": 2.0,
        "function_call": 3.0,
        "loop_iteration": 1.0,
        "recursion_setup": 5.0,
    }
