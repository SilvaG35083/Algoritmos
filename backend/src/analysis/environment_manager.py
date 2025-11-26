"""Gestor de entornos y variables para análisis semántico."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(slots=True)
class Variable:
    """Representa una variable en el entorno."""

    name: str
    value: Any = None
    type: str = "unknown"  # "int", "array", "object", etc.


@dataclass(slots=True)
class Environment:
    """Representa un entorno de ejecución con variables."""

    variables: Dict[str, Variable] = field(default_factory=dict)
    parent: Optional["Environment"] = None

    def get(self, name: str) -> Optional[Variable]:
        """Obtiene una variable del entorno actual o de los padres."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, value: Any, var_type: str = "unknown") -> None:
        """Establece una variable en el entorno actual."""
        self.variables[name] = Variable(name=name, value=value, type=var_type)

    def has(self, name: str) -> bool:
        """Verifica si una variable existe en el entorno."""
        return self.get(name) is not None


class EnvironmentManager:
    """Gestiona múltiples entornos (scope) durante el análisis."""

    def __init__(self):
        self._environments: Dict[str, Environment] = {}
        self._current_scope: str = "global"

    def create_environment(self, scope_name: str, parent: Optional[str] = None) -> Environment:
        """Crea un nuevo entorno."""
        parent_env = None
        if parent:
            parent_env = self._environments.get(parent)
        
        env = Environment(parent=parent_env)
        self._environments[scope_name] = env
        return env

    def get_environment(self, scope_name: str) -> Optional[Environment]:
        """Obtiene un entorno por nombre."""
        return self._environments.get(scope_name)

    def set_current_scope(self, scope_name: str) -> None:
        """Establece el scope actual."""
        self._current_scope = scope_name

    def get_current_environment(self) -> Environment:
        """Obtiene el entorno actual."""
        if self._current_scope not in self._environments:
            self.create_environment(self._current_scope)
        return self._environments[self._current_scope]

