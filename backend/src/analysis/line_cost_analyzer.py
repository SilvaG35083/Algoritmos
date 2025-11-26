"""Análisis de costo por línea de código."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from parsing import ast_nodes


@dataclass(slots=True)
class LineCost:
    """Costo de una línea específica."""

    line_number: int
    line_code: str
    scope: str
    cost: str  # O(1), O(n), etc.
    explanation: str
    source: str  # De dónde viene el costo (ej: "Asignación simple", "Bucle for anidado")


@dataclass(slots=True)
class LineCostAnalysis:
    """Análisis completo de costos por línea."""

    line_costs: List[LineCost] = field(default_factory=list)
    total_cost: str = ""
    complexity_breakdown: Dict[str, int] = field(default_factory=dict)


class LineCostAnalyzer:
    """Analiza el costo de cada línea del algoritmo."""

    def __init__(self):
        self._source_lines: List[str] = []
        self._current_loop_depth = 0  # Profundidad de bucles anidados

    def analyze(self, program: ast_nodes.Program, source: str) -> LineCostAnalysis:
        """Analiza el costo línea por línea del programa."""
        self._source_lines = source.splitlines()
        line_costs: List[LineCost] = []

        sections: List[Tuple[str, List[ast_nodes.Statement]]] = [
            ("Algoritmo principal", program.body)
        ]
        for proc in getattr(program, "procedures", []):
            sections.append((f"Procedimiento {proc.name}", proc.body))

        for scope, statements in sections:
            line_costs.extend(self._analyze_statements(statements, scope, current_line=1))

        total_cost = self._calculate_total_cost(line_costs)

        return LineCostAnalysis(
            line_costs=line_costs,
            total_cost=total_cost,
            complexity_breakdown=self._build_complexity_breakdown(line_costs),
        )

    def _analyze_statements(
        self, statements: List[ast_nodes.Statement], scope: str, current_line: int = 1
    ) -> List[LineCost]:
        """Analiza una lista de statements y retorna sus costos."""
        costs: List[LineCost] = []
        line = current_line

        for statement in statements:
            if isinstance(statement, ast_nodes.Assignment):
                cost = self._analyze_assignment(statement, line, scope)
                if cost:
                    costs.append(cost)
                line += 1

            elif isinstance(statement, ast_nodes.ForLoop):
                self._current_loop_depth += 1
                cost = self._analyze_for_loop(statement, line, scope)
                if cost:
                    costs.append(cost)
                # Analizar el cuerpo del bucle
                nested_costs = self._analyze_statements(statement.body, scope, line + 1)
                costs.extend(nested_costs)
                self._current_loop_depth -= 1
                line += 1

            elif isinstance(statement, ast_nodes.WhileLoop):
                self._current_loop_depth += 1
                cost = self._analyze_while_loop(statement, line, scope)
                if cost:
                    costs.append(cost)
                nested_costs = self._analyze_statements(statement.body, scope, line + 1)
                costs.extend(nested_costs)
                self._current_loop_depth -= 1
                line += 1

            elif isinstance(statement, ast_nodes.RepeatUntilLoop):
                self._current_loop_depth += 1
                cost = self._analyze_repeat_loop(statement, line, scope)
                if cost:
                    costs.append(cost)
                nested_costs = self._analyze_statements(statement.body, scope, line + 1)
                costs.extend(nested_costs)
                self._current_loop_depth -= 1
                line += 1

            elif isinstance(statement, ast_nodes.IfStatement):
                cost = self._analyze_if_statement(statement, line, scope)
                if cost:
                    costs.append(cost)
                nested_costs = self._analyze_statements(statement.then_branch, scope, line + 1)
                costs.extend(nested_costs)
                if statement.else_branch:
                    nested_costs = self._analyze_statements(statement.else_branch, scope, line + 1)
                    costs.extend(nested_costs)
                line += 1

            elif isinstance(statement, ast_nodes.CallStatement):
                cost = self._analyze_call(statement, line, scope)
                if cost:
                    costs.append(cost)
                line += 1

            elif isinstance(statement, ast_nodes.ReturnStatement):
                cost = self._analyze_return(statement, line, scope)
                if cost:
                    costs.append(cost)
                line += 1

            elif isinstance(statement, ast_nodes.PrintStatement):
                cost = self._analyze_print(statement, line, scope)
                if cost:
                    costs.append(cost)
                line += 1

            elif isinstance(statement, ast_nodes.Block):
                nested_costs = self._analyze_statements(statement.statements, scope, line)
                costs.extend(nested_costs)
                line += len(statement.statements)

        return costs

    def _line_cost(
        self,
        line: int,
        scope: str,
        cost: str,
        explanation: str,
        source: str,
    ) -> LineCost:
        """Crea un LineCost con el código de la línea."""
        line_code = self._source_lines[line - 1].strip() if 0 < line <= len(self._source_lines) else ""
        return LineCost(
            line_number=line,
            line_code=line_code,
            scope=scope,
            cost=cost,
            explanation=explanation,
            source=source,
        )

    def _analyze_assignment(self, stmt: ast_nodes.Assignment, line: int, scope: str) -> LineCost:
        """Analiza una asignación."""
        # Si está dentro de un bucle, el costo se multiplica
        if self._current_loop_depth > 0:
            if self._current_loop_depth == 1:
                cost_str = "O(n)"
                explanation = "Asignación dentro de un bucle (se ejecuta n veces)"
            elif self._current_loop_depth == 2:
                cost_str = "O(n²)"
                explanation = "Asignación dentro de bucles anidados (se ejecuta n² veces)"
            else:
                cost_str = f"O(n^{self._current_loop_depth})"
                explanation = f"Asignación dentro de {self._current_loop_depth} bucles anidados"
        else:
            cost_str = "O(1)"
            explanation = "Asignación simple"
        
        # Verificar si es acceso a arreglo
        if isinstance(stmt.target, ast_nodes.ArrayAccess):
            source = "Acceso a arreglo"
        elif isinstance(stmt.value, ast_nodes.BinaryOp):
            source = "Asignación con operación aritmética"
        else:
            source = "Asignación"
        
        return self._line_cost(line, scope, cost_str, explanation, source)

    def _analyze_for_loop(self, stmt: ast_nodes.ForLoop, line: int, scope: str) -> LineCost:
        """Analiza un bucle FOR."""
        # Calcular el costo del bucle según la profundidad
        if self._current_loop_depth == 1:
            cost_str = "O(n)"
            explanation = "Bucle FOR externo (n iteraciones)"
        elif self._current_loop_depth == 2:
            cost_str = "O(n²)"
            explanation = "Bucle FOR anidado (n² iteraciones totales)"
        else:
            cost_str = f"O(n^{self._current_loop_depth})"
            explanation = f"Bucle FOR anidado a profundidad {self._current_loop_depth}"
        
        try:
            start_val = getattr(stmt, 'start', None)
            end_val = getattr(stmt, 'end', None)
            explanation += f" (rango: {start_val} a {end_val})"
        except:
            pass
        
        return self._line_cost(line, scope, cost_str, explanation, "Bucle FOR")

    def _analyze_while_loop(self, stmt: ast_nodes.WhileLoop, line: int, scope: str) -> LineCost:
        """Analiza un bucle WHILE."""
        return self._line_cost(
            line, scope, "O(n)", "Bucle WHILE con condición (puede iterar hasta n veces)", "Bucle WHILE"
        )

    def _analyze_repeat_loop(self, stmt: ast_nodes.RepeatUntilLoop, line: int, scope: str) -> LineCost:
        """Analiza un bucle REPEAT."""
        return self._line_cost(
            line, scope, "O(n)", "Bucle REPEAT-UNTIL (puede iterar hasta n veces)", "Bucle REPEAT"
        )

    def _analyze_if_statement(self, stmt: ast_nodes.IfStatement, line: int, scope: str) -> LineCost:
        """Analiza una sentencia IF."""
        return self._line_cost(
            line, scope, "O(1)", "Evaluación de condición", "Condicional IF"
        )

    def _analyze_call(self, stmt: ast_nodes.CallStatement, line: int, scope: str) -> LineCost:
        """Analiza una llamada a procedimiento."""
        proc_name = getattr(stmt, 'procedure_name', 'procedimiento')
        # Si es recursivo, el costo puede ser mayor, pero por ahora O(1) para la llamada
        return self._line_cost(
            line, scope, "O(1)", f"Llamada a procedimiento {proc_name}", "CALL"
        )

    def _analyze_return(self, stmt: ast_nodes.ReturnStatement, line: int, scope: str) -> LineCost:
        """Analiza un RETURN."""
        return self._line_cost(
            line, scope, "O(1)", "Retorno de valor", "RETURN"
        )

    def _analyze_print(self, stmt: ast_nodes.PrintStatement, line: int, scope: str) -> LineCost:
        """Analiza un PRINT."""
        return self._line_cost(
            line, scope, "O(1)", "Impresión de valor", "PRINT"
        )

    def _calculate_total_cost(self, line_costs: List[LineCost]) -> str:
        """Calcula el costo total combinado."""
        if not line_costs:
            return "O(1)"
        
        # Encontrar la complejidad máxima
        complexities = [cost.cost for cost in line_costs]
        
        # Prioridad: n² > n log n > n > log n > 1
        if any("n²" in c or "n^2" in c for c in complexities):
            return "O(n²)"
        elif any("n log n" in c or "nlgn" in c.lower() for c in complexities):
            return "O(n log n)"
        elif any("log n" in c.lower() for c in complexities):
            return "O(log n)"
        elif any("O(n)" in c for c in complexities):
            return "O(n)"
        else:
            return "O(1)"

    def _build_complexity_breakdown(self, line_costs: List[LineCost]) -> Dict[str, int]:
        """Construye un desglose de complejidades."""
        breakdown: Dict[str, int] = {}
        for cost in line_costs:
            complexity = cost.cost
            breakdown[complexity] = breakdown.get(complexity, 0) + 1
        return breakdown

