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
    """Complexity expression: base^n * n^degree * (log n)^log_power.
    
    - exponential_base > 1: exponencial (2^n, 3^n, etc)
    - exponential_base = 0: polinomial/logarítmico
    """

    degree: int = 0
    log_power: int = 0
    exponential_base: int = 0  # 0=no exponencial, 2=2^n, 3=3^n, etc

    def dominates(self, other: "ComplexityMeasure") -> bool:
        # Exponencial siempre domina sobre polinomial
        if self.exponential_base > 0 and other.exponential_base == 0:
            return True
        if self.exponential_base == 0 and other.exponential_base > 0:
            return False
        
        # Ambos exponenciales: comparar bases
        if self.exponential_base > 0 and other.exponential_base > 0:
            return self.exponential_base >= other.exponential_base
        
        # Ambos polinomiales: comparar grado y log
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
        # Caso trivial: constante
        if self.degree == 0 and self.log_power == 0 and self.exponential_base == 0:
            return f"{prefix}(1)"
        
        factors: List[str] = []
        
        # Exponencial (más significativo)
        if self.exponential_base > 0:
            factors.append(f"{self.exponential_base}^n")
        
        # Polinomial
        if self.degree > 0:
            factors.append("n" if self.degree == 1 else f"n^{self.degree}")
        
        # Logarítmico
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
        
        # Detectar recursión manualmente si el PatternLibrary no la detectó
        if not has_recursion and program.procedures:
            for proc in program.procedures:
                if self._count_recursive_calls(proc) > 0:
                    has_recursion = True
                    annotations["pattern_summary"] = f"Se detecto recursividad en la subrutina {proc.name}."
                    break

        context = AnalysisContext(loop_iterators=set())
        program_case = self._analyze_block(program.body, context)
        
        # Si hay procedimientos, también analizarlos (especialmente recursivos)
        if program.procedures:
            for proc in program.procedures:
                proc_case = self._analyze_block(proc.body, context)
                # Combinar con el caso del programa principal
                program_case = program_case.max_with(proc_case)
        
        # Detectar patrón recursivo específico si hay recursión
        recursive_pattern = "unknown"
        if has_recursion and program.procedures:
            # Buscar el procedimiento recursivo (no auxiliar)
            recursive_proc = None
            for proc in program.procedures:
                if self._count_recursive_calls(proc) > 0:
                    recursive_proc = proc
                    break
            
            # Si encontramos el recursivo, detectar su patrón
            if recursive_proc:
                recursive_pattern = self._detect_recursive_pattern(recursive_proc)
                print(f"DEBUG: Patrón recursivo detectado: '{recursive_pattern}' para {recursive_proc.name}")
            else:
                # Fallback: analizar el último (probablemente el principal)
                recursive_pattern = self._detect_recursive_pattern(program.procedures[-1])
                print(f"DEBUG: Patrón recursivo (fallback): '{recursive_pattern}'")
        
        if has_recursion:
            # Aplicar heurísticas según el patrón detectado
            if recursive_pattern == "fibonacci":
                # Fibonacci: exponencial O(2^n) en todos los casos
                recursion_case = CaseComplexity(
                    best=ComplexityMeasure(exponential_base=2),  # 2^n
                    worst=ComplexityMeasure(exponential_base=2),  # 2^n
                    average=ComplexityMeasure(exponential_base=2),  # 2^n
                )
            elif recursive_pattern == "hanoi":
                # Torres de Hanoi: T(n) = 2*T(n-1) + 1 → O(2^n)
                recursion_case = CaseComplexity(
                    best=ComplexityMeasure(exponential_base=2),  # 2^n
                    worst=ComplexityMeasure(exponential_base=2),  # 2^n
                    average=ComplexityMeasure(exponential_base=2),  # 2^n
                )
            elif recursive_pattern == "quicksort":
                # QuickSort: mejor O(n log n), peor O(n²), promedio O(n log n)
                recursion_case = CaseComplexity(
                    best=ComplexityMeasure(degree=1, log_power=1),  # n log n
                    worst=ComplexityMeasure(degree=2),  # n²
                    average=ComplexityMeasure(degree=1, log_power=1),  # n log n
                )
            elif recursive_pattern == "mergesort":
                # MergeSort: siempre O(n log n)
                recursion_case = CaseComplexity(
                    best=ComplexityMeasure(degree=1, log_power=1),
                    worst=ComplexityMeasure(degree=1, log_power=1),
                    average=ComplexityMeasure(degree=1, log_power=1),
                )
            elif recursive_pattern == "binarysearch":
                # Búsqueda binaria: mejor O(1), peor O(log n)
                recursion_case = CaseComplexity(
                    best=ComplexityMeasure(),  # 1
                    worst=ComplexityMeasure(log_power=1),  # log n
                    average=ComplexityMeasure(log_power=1),
                )
            else:
                # Heurística genérica recursiva
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
            pattern_desc = f" Patrón: {recursive_pattern}." if recursive_pattern != "unknown" else ""
            heuristica_partes.append(f"Se aplicó heurística recursiva.{pattern_desc}")
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
    
    def _detect_recursive_pattern(self, proc: ast_nodes.Procedure) -> str:
        """Detecta patrones recursivos específicos para aplicar heurísticas correctas.
        
        Retorna:
        - 'fibonacci': Recursión múltiple tipo Fibonacci (exponencial)
        - 'quicksort': Patrón de QuickSort (2 llamadas recursivas con partición)
        - 'mergesort': Patrón de MergeSort (2 llamadas recursivas con merge)
        - 'binarysearch': Búsqueda binaria (1 llamada en condición)
        - 'generic_divide': Divide y conquista genérico
        - 'linear': Recursión lineal (n-1)
        - 'unknown': No se reconoce el patrón
        """
        # Contar llamadas recursivas
        recursive_calls = self._count_recursive_calls(proc)
        
        if recursive_calls == 0:
            return "unknown"
        
        # 2+ llamadas recursivas: distinguir entre patrones
        if recursive_calls >= 2:
            has_loops = self._has_loops(proc)
            has_partition = self._has_partition_pattern(proc)
            has_early_return = self._has_early_return_in_condition(proc)
            
            # Fibonacci: múltiples recursiones, sin bucles, con return temprano
            if not has_loops and not has_partition and has_early_return:
                return "fibonacci"
            
            # Torres de Hanoi: 2 llamadas recursivas lineales (n-1), sin bucles
            # Distinguir de MergeSort porque Hanoi no tiene merge (sin bucles después)
            if recursive_calls == 2 and not has_loops and not has_partition:
                # Verificar que las llamadas son lineales (n-1 o similar)
                if self._has_linear_recursive_calls(proc):
                    return "hanoi"
            
            # QuickSort: 2 llamadas + partición
            if has_partition:
                return "quicksort"
            
            # MergeSort: 2 llamadas sin partición (tiene bucles para merge)
            return "mergesort"
        
        # Búsqueda binaria: 1 llamada recursiva en estructura condicional
        if recursive_calls == 1:
            has_binary_condition = self._has_binary_search_condition(proc)
            if has_binary_condition:
                return "binarysearch"
            return "linear"
        
        return "generic_divide"
    
    def _count_recursive_calls(self, proc: ast_nodes.Procedure) -> int:
        """Cuenta llamadas recursivas en un procedimiento."""
        count = 0
        
        def visit(statements):
            nonlocal count
            for stmt in statements:
                if isinstance(stmt, ast_nodes.CallStatement):
                    if stmt.name.lower() == proc.name.lower() or stmt.name == 'self':
                        count += 1
                elif isinstance(stmt, ast_nodes.IfStatement):
                    visit(stmt.then_branch)
                    visit(stmt.else_branch)
                elif isinstance(stmt, (ast_nodes.WhileLoop, ast_nodes.ForLoop)):
                    visit(stmt.body)
        
        visit(proc.body)
        return count
    
    def _has_partition_pattern(self, proc: ast_nodes.Procedure) -> bool:
        """Detecta si hay un patrón de partición (bucles con comparaciones de pivote)."""
        # Buscar recursivamente en statements anidados
        def search_statements(statements):
            for stmt in statements:
                if isinstance(stmt, ast_nodes.WhileLoop):
                    # Buscar condiciones que comparen con un pivote
                    if self._contains_comparison(stmt.condition):
                        return True
                    if search_statements(stmt.body):
                        return True
                elif isinstance(stmt, ast_nodes.CallStatement):
                    # Buscar llamada a función de partición
                    if 'particion' in stmt.name.lower() or 'partition' in stmt.name.lower():
                        return True
                elif isinstance(stmt, ast_nodes.IfStatement):
                    if search_statements(stmt.then_branch):
                        return True
                    if search_statements(stmt.else_branch):
                        return True
                elif isinstance(stmt, ast_nodes.ForLoop):
                    if search_statements(stmt.body):
                        return True
            return False
        
        return search_statements(proc.body)
    
    def _has_binary_search_condition(self, proc: ast_nodes.Procedure) -> bool:
        """Detecta condiciones típicas de búsqueda binaria."""
        for stmt in proc.body:
            if isinstance(stmt, ast_nodes.IfStatement):
                # Buscar cálculo de punto medio
                if self._contains_midpoint_calculation(stmt.then_branch) or \
                   self._contains_midpoint_calculation(stmt.else_branch):
                    return True
        return False
    
    def _contains_comparison(self, expr: ast_nodes.Expression | None) -> bool:
        """Verifica si una expresión contiene comparaciones."""
        if expr is None:
            return False
        if isinstance(expr, ast_nodes.BinaryOperation):
            if expr.operator in {"<", "<=", ">", ">=", "="}:
                return True
            return self._contains_comparison(expr.left) or self._contains_comparison(expr.right)
        return False
    
    def _contains_midpoint_calculation(self, statements) -> bool:
        """Busca cálculo de punto medio (low+high)/2."""
        for stmt in statements:
            if isinstance(stmt, ast_nodes.Assignment):
                if isinstance(stmt.value, ast_nodes.BinaryOperation):
                    if stmt.value.operator in {"/", "div"}:
                        if isinstance(stmt.value.left, ast_nodes.BinaryOperation):
                            if stmt.value.left.operator == "+":
                                return True
        return False
    
    def _has_loops(self, proc: ast_nodes.Procedure) -> bool:
        """Detecta si el procedimiento tiene bucles."""
        def search(statements):
            for stmt in statements:
                if isinstance(stmt, (ast_nodes.WhileLoop, ast_nodes.ForLoop, ast_nodes.RepeatUntilLoop)):
                    return True
                if isinstance(stmt, ast_nodes.IfStatement):
                    if search(stmt.then_branch) or search(stmt.else_branch):
                        return True
            return False
        return search(proc.body)
    
    def _has_early_return_in_condition(self, proc: ast_nodes.Procedure) -> bool:
        """Detecta if con return en el then_branch (caso base de recursión)."""
        for stmt in proc.body:
            if isinstance(stmt, ast_nodes.IfStatement):
                for then_stmt in stmt.then_branch:
                    if isinstance(then_stmt, ast_nodes.ReturnStatement):
                        return True
        return False
    
    def _has_linear_recursive_calls(self, proc: ast_nodes.Procedure) -> bool:
        """Verifica si las llamadas recursivas son lineales (n-1, n-k)."""
        def search(statements):
            for stmt in statements:
                if isinstance(stmt, ast_nodes.CallStatement):
                    if stmt.name.lower() == proc.name.lower():
                        # Verificar si algún argumento tiene resta (n-1, n-k)
                        for arg in stmt.arguments:
                            if isinstance(arg, ast_nodes.BinaryOperation) and arg.operator == "-":
                                return True
                elif isinstance(stmt, ast_nodes.IfStatement):
                    if search(stmt.then_branch) or search(stmt.else_branch):
                        return True
            return False
        return search(proc.body)
