"""Validation utilities for parsed programs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from parsing import ast_nodes


class ValidationError(RuntimeError):
    """Raised when a structural rule fails."""


@dataclass(slots=True)
class ValidatorResult:
    name: str
    warnings: List[str]


class Validator:
    """Validates an AST or part of it."""

    name: str = "base-validator"

    def validate(self, program: ast_nodes.Program) -> ValidatorResult:
        raise NotImplementedError


class ValidatorSuite:
    """Aggregates multiple validators."""

    def __init__(self, validators: Sequence[Validator]) -> None:
        self._validators = list(validators)

    def validate(self, program: ast_nodes.Program) -> List[ValidatorResult]:
        results: List[ValidatorResult] = []
        for validator in self._validators:
            results.append(validator.validate(program))
        return results

    @classmethod
    def default(cls) -> "ValidatorSuite":
        return cls([EmptyProgramValidator()])


class EmptyProgramValidator(Validator):
    """Warns when the program body is empty."""

    name = "empty-program"

    def validate(self, program: ast_nodes.Program) -> ValidatorResult:
        warnings: List[str] = []
        if not program.body:
            warnings.append("Program body is empty. Analysis result may be trivial.")
        return ValidatorResult(name=self.name, warnings=warnings)
