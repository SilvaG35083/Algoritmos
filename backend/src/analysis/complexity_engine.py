"""Core engine that coordinates complexity analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set

from parsing import ast_nodes
from .cost_model import CostModel
from .pattern_library import PatternLibrary
from .recurrence_solver import RecurrenceSolver

OMEGA = "\u03a9"
THETA = "\u0398"


@dataclass(slots=True)
class ComplexityResult:
    """Stores the complexity estimation for different scenarios."""

    best_case: str
    worst_case: str
    average_case: str
    annotations: Dict[str, str]


@dataclass(slots=True)
class EngineConfig:
    """Tunable parameters for the engine."""

    enable_case_analysis: bool = True
    track_space_complexity: bool = True


@dataclass(slots=True)
class ComplexityMeasure:
    """Polynomial-like complexity expression: n^degree * (log n)^log_power."""

    degree: int = 0
    log_power: int = 0

    def dominates(self, other: "ComplexityMeasure") -> bool:
        if self.degree != other.degree:
            return self.degree > other.degree
        return self.log_power >= other.log_power

    def max_with(self, other: "ComplexityMeasure") -> "ComplexityMeasure":
        return self if self.dominates(other) else other

    def min_with(self, other: "ComplexityMeasure") -> "ComplexityMeasure":
        return other if self.dominates(other) else self

    def add_degree(self, amount: int) -> "ComplexityMeasure":
        return ComplexityMeasure(degree=self.degree + amount, log_power=self.log_power)

    def add_log(self, amount: int) -> "ComplexityMeasure":
        return ComplexityMeasure(degree=self.degree, log_power=self.log_power + amount)

    def to_notation(self, prefix: str) -> str:
        if self.degree == 0 and self.log_power == 0:
            return f"{prefix}(1)"
        factors: List[str] = []
        if self.degree > 0:
            factors.append("n" if self.degree == 1 else f"n^{self.degree}")
        if self.log_power > 0:
            if self.log_power == 1:
                factors.append("log n")
            else:
                factors.append(f"(log n)^{self.log_power}")
        expr = " ".join(factors) if factors else "1"
        return f"{prefix}({expr})"


@dataclass(slots=True)
class CaseComplexity:
    """Stores best/worst/average complexity measures."""

    best: ComplexityMeasure
    worst: ComplexityMeasure
    average: ComplexityMeasure

    @classmethod
    def constant(cls) -> "CaseComplexity":
        base = ComplexityMeasure()
        return cls(best=base, worst=base, average=base)

    def combine_sequence(self, other: "CaseComplexity") -> "CaseComplexity":
        return CaseComplexity(
            best=self.best.max_with(other.best),
            worst=self.worst.max_with(other.worst),
            average=self.average.max_with(other.average),
        )

    def combine_branch(self, other: "CaseComplexity") -> "CaseComplexity":
        return CaseComplexity(
            best=self.best.min_with(other.best),
            worst=self.worst.max_with(other.worst),
            average=self.average.max_with(other.average),
        )

    def scale_by_degree(self, degree: int) -> "CaseComplexity":
        if degree == 0:
            return self
        return CaseComplexity(
            best=self.best.add_degree(degree),
            worst=self.worst.add_degree(degree),
            average=self.average.add_degree(degree),
        )

    def max_with(self, other: "CaseComplexity") -> "CaseComplexity":
        return CaseComplexity(
            best=self.best.max_with(other.best),
            worst=self.worst.max_with(other.worst),
            average=self.average.max_with(other.average),
        )


@dataclass(slots=True)
class AnalysisContext:
    """Stores contextual information during analysis."""

    loop_iterators: Set[str]

    def with_iterator(self, iterator: str) -> "AnalysisContext":
        new_iterators = set(self.loop_iterators)
        new_iterators.add(iterator)
        return AnalysisContext(loop_iterators=new_iterators)


class ComplexityEngine:
    """Main entry point for AST based analysis."""

    def __init__(
        self,
        cost_model: CostModel | None = None,
        patterns: PatternLibrary | None = None,
        solver: RecurrenceSolver | None = None,
        config: EngineConfig | None = None,
    ) -> None:
        self._cost_model = cost_model or CostModel()
        self._patterns = patterns or PatternLibrary.default()
        self._solver = solver or RecurrenceSolver.default()
        self._config = config or EngineConfig()

    def analyze(self, program: ast_nodes.Program, raw_source: str | None = None) -> ComplexityResult:
        annotations: Dict[str, str] = {}
        matches = self._patterns.match_program(program)
        if matches:
            annotations["pattern_summary"] = "; ".join(match.description for match in matches)
        else:
            annotations["pattern_summary"] = "No se detectaron patrones relevantes."
        has_recursion = any(match.name == "recursion" for match in matches)

        context = AnalysisContext(loop_iterators=set())
        program_case = self._analyze_block(program.body, context)
        if has_recursion:
            recursion_case = CaseComplexity(
                best=ComplexityMeasure(degree=1),
                worst=ComplexityMeasure(degree=1, log_power=1),
                average=ComplexityMeasure(degree=1, log_power=1),
            )
            program_case = program_case.max_with(recursion_case)

        heuristica_partes = [
            f"Grado polinomico estimado -> mejor: {program_case.best.degree}, "
            f"peor: {program_case.worst.degree}, promedio: {program_case.average.degree}."
        ]
        if has_recursion:
            heuristica_partes.append("Se aplico heuristica recursiva (>= O(n log n)).")
        annotations["heuristica"] = " ".join(heuristica_partes)
        annotations["nota"] = "Complejidad estimada mediante analisis estructural."

        best_case = program_case.best.to_notation(OMEGA)
        worst_case = program_case.worst.to_notation("O")
        average_case = program_case.average.to_notation(THETA)

        return ComplexityResult(
            best_case=best_case,
            worst_case=worst_case,
            average_case=average_case,
            annotations=annotations,
        )

    # ------------------------------------------------------------------
    # Block and statement analysis
    # ------------------------------------------------------------------

    def _analyze_block(self, statements: Sequence[ast_nodes.Statement], context: AnalysisContext) -> CaseComplexity:
        result = CaseComplexity.constant()
        for statement in statements:
            result = result.combine_sequence(self._analyze_statement(statement, context))
        return result

    def _analyze_statement(self, statement: ast_nodes.Statement, context: AnalysisContext) -> CaseComplexity:
        if isinstance(statement, ast_nodes.ForLoop):
            return self._analyze_for(statement, context)
        if isinstance(statement, ast_nodes.WhileLoop):
            return self._analyze_while(statement, context)
        if isinstance(statement, ast_nodes.RepeatUntilLoop):
            return self._analyze_repeat(statement, context)
        if isinstance(statement, ast_nodes.IfStatement):
            return self._analyze_if(statement, context)
        if isinstance(statement, ast_nodes.CallStatement):
            return CaseComplexity.constant()
        if isinstance(statement, ast_nodes.ReturnStatement):
            return CaseComplexity.constant()
        if isinstance(statement, ast_nodes.Assignment):
            return CaseComplexity.constant()
        # Fallback: treat as constant
        return CaseComplexity.constant()

    def _analyze_for(self, loop: ast_nodes.ForLoop, context: AnalysisContext) -> CaseComplexity:
        body_case = self._analyze_block(loop.body, context.with_iterator(loop.iterator))
        iteration_degree = self._infer_iteration_degree(loop.start, loop.stop, {loop.iterator})
        return body_case.scale_by_degree(iteration_degree)

    def _analyze_while(self, loop: ast_nodes.WhileLoop, context: AnalysisContext) -> CaseComplexity:
        body_case = self._analyze_block(loop.body, context)
        loop_var = self._extract_loop_variable(loop.condition)
        degree = 1
        if loop_var:
            if self._body_progresses_variable(loop.body, loop_var):
                degree = self._infer_condition_degree(loop.condition, ignore={loop_var})
        
        # Check for early exit conditions (e.g., binary search pattern)
        has_early_exit = self._has_early_exit_condition(loop)
        
        if has_early_exit:
            # Best case: can exit on first iteration (constant time)
            best = ComplexityMeasure()
        else:
            # No early exit: must complete all iterations
            best = body_case.best.add_degree(degree)
        
        worst = body_case.worst.add_degree(degree)
        average = body_case.average.add_degree(degree)
        return CaseComplexity(best=best, worst=worst, average=average)

    def _analyze_repeat(self, loop: ast_nodes.RepeatUntilLoop, context: AnalysisContext) -> CaseComplexity:
        body_case = self._analyze_block(loop.body, context)
        degree = self._infer_condition_degree(loop.condition, ignore=set()) if loop.condition else 1
        return body_case.scale_by_degree(degree)

    def _analyze_if(self, node: ast_nodes.IfStatement, context: AnalysisContext) -> CaseComplexity:
        then_case = self._analyze_block(node.then_branch, context)
        else_case = self._analyze_block(node.else_branch, context)
        combined = then_case.combine_branch(else_case)
        return combined

    # ------------------------------------------------------------------
    # Helpers for iteration degree inference
    # ------------------------------------------------------------------

    def _infer_iteration_degree(
        self,
        start: ast_nodes.Expression,
        stop: ast_nodes.Expression,
        ignore: Set[str],
    ) -> int:
        if not self._expression_depends_on_input(stop, ignore):
            return 1 if self._expression_depends_on_input(start, ignore) else 0
        return 1

    def _infer_condition_degree(self, expr: ast_nodes.Expression | None, ignore: Set[str]) -> int:
        if expr is None:
            return 1
        if isinstance(expr, ast_nodes.BinaryOperation) and expr.operator in {"<", "<=", ">", ">=", "="}:
            depends_left = self._expression_depends_on_input(expr.left, ignore)
            depends_right = self._expression_depends_on_input(expr.right, ignore)
            return 1 if depends_left or depends_right else 0
        return 1 if self._expression_depends_on_input(expr, ignore) else 0

    # ------------------------------------------------------------------
    # Auxiliary analysis helpers
    # ------------------------------------------------------------------

    def _expression_depends_on_input(self, expr: ast_nodes.Expression, ignore: Set[str]) -> bool:
        if isinstance(expr, ast_nodes.Number):
            return False
        if isinstance(expr, ast_nodes.BooleanLiteral):
            return False
        if isinstance(expr, ast_nodes.NullLiteral):
            return False
        if isinstance(expr, ast_nodes.StringLiteral):
            return False
        if isinstance(expr, ast_nodes.Identifier):
            return expr.name not in ignore
        if isinstance(expr, ast_nodes.LengthCall):
            return True
        if isinstance(expr, ast_nodes.ArrayAccess):
            return self._expression_depends_on_input(expr.base, ignore) or self._expression_depends_on_input(expr.index, ignore)
        if isinstance(expr, ast_nodes.FieldAccess):
            return self._expression_depends_on_input(expr.base, ignore)
        if isinstance(expr, ast_nodes.RangeExpression):
            return self._expression_depends_on_input(expr.start, ignore) or self._expression_depends_on_input(expr.end, ignore)
        if isinstance(expr, ast_nodes.UnaryOperation):
            return self._expression_depends_on_input(expr.operand, ignore)
        if isinstance(expr, ast_nodes.BinaryOperation):
            return self._expression_depends_on_input(expr.left, ignore) or self._expression_depends_on_input(expr.right, ignore)
        return True

    def _extract_loop_variable(self, expr: ast_nodes.Expression) -> str | None:
        if isinstance(expr, ast_nodes.BinaryOperation) and expr.operator in {"<", "<=", ">", ">=", "="}:
            if isinstance(expr.left, ast_nodes.Identifier):
                return expr.left.name
            if isinstance(expr.right, ast_nodes.Identifier):
                return expr.right.name
        return None

    def _body_progresses_variable(self, statements: Sequence[ast_nodes.Statement], var_name: str) -> bool:
        for statement in statements:
            if isinstance(statement, ast_nodes.Assignment):
                if self._assignment_progresses_variable(statement, var_name):
                    return True
            elif isinstance(statement, ast_nodes.IfStatement):
                if self._body_progresses_variable(statement.then_branch, var_name):
                    return True
                if self._body_progresses_variable(statement.else_branch, var_name):
                    return True
        return False

    def _assignment_progresses_variable(self, assignment: ast_nodes.Assignment, var_name: str) -> bool:
        if isinstance(assignment.target, ast_nodes.Identifier) and assignment.target.name == var_name:
            value = assignment.value
            if isinstance(value, ast_nodes.BinaryOperation) and isinstance(value.left, ast_nodes.Identifier):
                if value.left.name == var_name and isinstance(value.right, ast_nodes.Number):
                    if value.operator in {"+", "-"}:
                        return True
        return False

    def _has_early_exit_condition(self, loop: ast_nodes.WhileLoop) -> bool:
        """Detects if a while loop has early exit conditions (e.g., found flag in binary search)."""
        # Check loop condition for exit flag
        if self._condition_has_exit_flag(loop.condition):
            # Check if body can set that flag
            if self._body_can_set_exit_flag(loop.body, loop.condition):
                return True
        return False

    def _condition_has_exit_flag(self, condition: ast_nodes.Expression | None) -> bool:
        """Check if condition includes an exit flag (e.g., 'encontro = 0')."""
        if condition is None:
            return False
        if isinstance(condition, ast_nodes.BinaryOperation):
            if condition.operator in {"and", "or"}:
                return self._condition_has_exit_flag(condition.left) or self._condition_has_exit_flag(condition.right)
            # Look for patterns like 'encontro = 0' or 'found = false'
            if condition.operator == "=":
                if isinstance(condition.left, ast_nodes.Identifier):
                    var_name = condition.left.name.lower()
                    if any(keyword in var_name for keyword in ["encontr", "found", "flag", "exist"]):
                        return True
                if isinstance(condition.right, ast_nodes.Identifier):
                    var_name = condition.right.name.lower()
                    if any(keyword in var_name for keyword in ["encontr", "found", "flag", "exist"]):
                        return True
        return False

    def _body_can_set_exit_flag(self, statements: Sequence[ast_nodes.Statement], condition: ast_nodes.Expression) -> bool:
        """Check if loop body contains assignments that can trigger early exit."""
        flag_names = self._extract_flag_names(condition)
        if not flag_names:
            return False
        
        for statement in statements:
            if isinstance(statement, ast_nodes.Assignment):
                if isinstance(statement.target, ast_nodes.Identifier):
                    if statement.target.name in flag_names:
                        return True
            elif isinstance(statement, ast_nodes.IfStatement):
                # Check if any branch sets the flag
                if self._body_can_set_exit_flag(statement.then_branch, condition):
                    return True
                if self._body_can_set_exit_flag(statement.else_branch, condition):
                    return True
        return False

    def _extract_flag_names(self, condition: ast_nodes.Expression | None) -> Set[str]:
        """Extract variable names that act as exit flags from condition."""
        names: Set[str] = set()
        if condition is None:
            return names
        if isinstance(condition, ast_nodes.BinaryOperation):
            if condition.operator in {"and", "or"}:
                names.update(self._extract_flag_names(condition.left))
                names.update(self._extract_flag_names(condition.right))
            elif condition.operator == "=":
                if isinstance(condition.left, ast_nodes.Identifier):
                    var_name = condition.left.name.lower()
                    if any(keyword in var_name for keyword in ["encontr", "found", "flag", "exist"]):
                        names.add(condition.left.name)
                if isinstance(condition.right, ast_nodes.Identifier):
                    var_name = condition.right.name.lower()
                    if any(keyword in var_name for keyword in ["encontr", "found", "flag", "exist"]):
                        names.add(condition.right.name)
        return names
