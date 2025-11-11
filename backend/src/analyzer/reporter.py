"""Report generation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from analysis.complexity_engine import ComplexityResult
from parsing import ast_nodes


@dataclass(slots=True)
class AnalysisReport:
    """Structured report that other layers can serialize."""

    summary: Dict[str, str]
    annotations: Dict[str, str]
    raw_ast: ast_nodes.Program = field(repr=False)


class Reporter:
    """Builds AnalysisReport instances."""

    def build(self, program: ast_nodes.Program, result: ComplexityResult) -> AnalysisReport:
        summary = {
            "best_case": result.best_case,
            "worst_case": result.worst_case,
            "average_case": result.average_case,
        }
        annotations = dict(result.annotations)
        annotations["statement_count"] = str(self._count_statements(program.body))
        return AnalysisReport(summary=summary, annotations=annotations, raw_ast=program)

    def _count_statements(self, statements: List[ast_nodes.Statement]) -> int:
        total = 0
        for statement in statements:
            total += 1
            if isinstance(statement, ast_nodes.ForLoop):
                total += self._count_statements(statement.body)
            elif isinstance(statement, ast_nodes.WhileLoop):
                total += self._count_statements(statement.body)
            elif isinstance(statement, ast_nodes.RepeatUntilLoop):
                total += self._count_statements(statement.body)
            elif isinstance(statement, ast_nodes.IfStatement):
                total += self._count_statements(statement.then_branch)
                total += self._count_statements(statement.else_branch)
        return total
