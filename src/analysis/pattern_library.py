"""Pattern detection utilities for algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from parsing import ast_nodes


@dataclass(slots=True)
class PatternMatch:
    """Represents a detected algorithmic pattern."""

    name: str
    description: str


class PatternLibrary:
    """Holds a list of recognizers that look for patterns in an AST."""

    def __init__(self, recognizers: Sequence["Recognizer"]) -> None:
        self._recognizers = list(recognizers)

    def match_program(self, program: ast_nodes.Program) -> List[PatternMatch]:
        matches: List[PatternMatch] = []
        for recognizer in self._recognizers:
            matches.extend(recognizer.match(program))
        return matches

    @classmethod
    def default(cls) -> "PatternLibrary":
        return cls([LoopRecognizer(), RecursionRecognizer()])


class Recognizer:
    """Interface for pattern recognizers."""

    def match(self, program: ast_nodes.Program) -> Iterable[PatternMatch]:
        raise NotImplementedError


class LoopRecognizer(Recognizer):
    """Detects presence of loops."""

    def match(self, program: ast_nodes.Program) -> Iterable[PatternMatch]:
        if self._contains_loop(program.body):
            yield PatternMatch("loop-structure", "El programa contiene estructuras iterativas.")

    def _contains_loop(self, statements: Sequence[ast_nodes.Statement]) -> bool:
        for statement in statements:
            if isinstance(statement, (ast_nodes.ForLoop, ast_nodes.WhileLoop, ast_nodes.RepeatUntilLoop)):
                return True
            if isinstance(statement, ast_nodes.IfStatement):
                if self._contains_loop(statement.then_branch) or self._contains_loop(statement.else_branch):
                    return True
        return False


class RecursionRecognizer(Recognizer):
    """Detects recursive calls by scanning statements."""

    def match(self, program: ast_nodes.Program) -> Iterable[PatternMatch]:
        known_procedures = {proc.name.lower() for proc in getattr(program, "procedures", [])}
        known_procedures.update({"self", "recurse"})
        if self._has_recursive_call(program.body, known_procedures):
            yield PatternMatch("recursion", "Se detecto un patron recursivo.")
        for procedure in getattr(program, "procedures", []):
            proc_names = set(known_procedures)
            proc_names.add(procedure.name.lower())
            if self._has_recursive_call(procedure.body, proc_names):
                yield PatternMatch("recursion", f"Se detecto recursividad en la subrutina {procedure.name}.")
                break

    def _has_recursive_call(self, statements: Sequence[ast_nodes.Statement], known_names: set[str]) -> bool:
        for statement in statements:
            if isinstance(statement, ast_nodes.CallStatement):
                if statement.name.lower() in known_names:
                    return True
            elif isinstance(statement, ast_nodes.IfStatement):
                if self._has_recursive_call(statement.then_branch, known_names):
                    return True
                if self._has_recursive_call(statement.else_branch, known_names):
                    return True
            elif isinstance(statement, ast_nodes.ForLoop):
                if self._has_recursive_call(statement.body, known_names):
                    return True
            elif isinstance(statement, ast_nodes.WhileLoop):
                if self._has_recursive_call(statement.body, known_names):
                    return True
            elif isinstance(statement, ast_nodes.RepeatUntilLoop):
                if self._has_recursive_call(statement.body, known_names):
                    return True
        return False
