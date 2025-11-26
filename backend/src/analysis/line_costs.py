from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from parsing import ast_nodes
from .complexity_engine import ComplexityMeasure


@dataclass(slots=True)
class _Ctx:
    depth: int = 0
    log_depth: int = 0


class LineCostAnalyzer:
    """Produces a simple per-line cost estimation based on loop depth.

    Heuristics:
    - Base statements (assignment, print, call, return): O(n^depth)
    - Conditions (if/while): O(n^depth) attributed to the line with the condition
    - Loop headers: shown as O(1); body statements reflect multiplicative depth
    - Nested loops increase depth multiplicatively (degree += 1 per loop)
    - Binary search style loops are treated as logarítmicos (factor log n)
    """

    def analyze(self, program: ast_nodes.Program, source: str) -> List[Dict[str, Any]]:
        self._ctx = _Ctx(depth=0)
        self._entries: Dict[int, ComplexityMeasure] = {}
        # Visitar primero el cuerpo principal del programa
        self._visit_block(program.body)

        # Además, recorrer los cuerpos de todas las subrutinas definidas
        for proc in program.procedures:
            self._visit_block(proc.body)

        lines = source.splitlines()
        results: List[Dict[str, Any]] = []
        for line_no in sorted(self._entries.keys()):
            measure = self._entries[line_no]
            text = lines[line_no - 1] if 1 <= line_no <= len(lines) else ""
            results.append(
                {
                    "line": line_no,
                    "code": text,
                    # Mostrar la forma simplificada sin el prefijo O(...)
                    "cost": self._format_expr(measure),
                }
            )
        return results

    def _format_expr(self, m: ComplexityMeasure) -> str:
        parts: List[str] = []
        if m.degree == 0 and m.log_power == 0:
            return "1"
        if m.degree > 0:
            parts.append("n" if m.degree == 1 else f"n^{m.degree}")
        if m.log_power > 0:
            log_part = "log n" if m.log_power == 1 else f"(log n)^{m.log_power}"
            parts.append(log_part)
        return " ".join(parts) if parts else "1"

    # -------------------- visitors --------------------

    def _record(self, line: int, degree_inc: int = 0) -> None:
        base = ComplexityMeasure(degree=self._ctx.depth + degree_inc, log_power=self._ctx.log_depth)
        current = self._entries.get(line)
        if current is None or base.dominates(current):
            self._entries[line] = base

    def _visit_block(self, statements: List[ast_nodes.Statement]) -> None:
        for stmt in statements:
            self._visit(stmt)

    def _visit(self, node: ast_nodes.Node | None) -> None:
        if node is None:
            return
        if isinstance(node, ast_nodes.ForLoop):
            # Header cost (comparisons/increments) attributed as O(1) at loop line
            self._record(node.line, degree_inc=0)
            self._ctx.depth += 1
            self._visit(node.start)
            self._visit(node.stop)
            self._visit_block(node.body)
            self._ctx.depth -= 1
            return
        if isinstance(node, ast_nodes.WhileLoop):
            # Attribute condition cost to condition line
            self._record(node.line, degree_inc=0)

            is_binary = self._is_binary_search_while(node)
            is_log = self._is_log_while(node)

            # Para búsqueda binaria o whiles logarítmicos, usamos solo log_depth
            if is_binary or is_log:
                self._ctx.log_depth += 1
                self._visit(node.condition)
                self._visit_block(node.body)
                self._ctx.log_depth -= 1
            else:
                self._ctx.depth += 1
                self._visit(node.condition)
                self._visit_block(node.body)
                self._ctx.depth -= 1
            return
        if isinstance(node, ast_nodes.RepeatUntilLoop):
            # Repeat header line cost
            self._record(node.line, degree_inc=0)
            self._ctx.depth += 1
            self._visit_block(node.body)
            if node.condition:
                self._visit(node.condition)
            self._ctx.depth -= 1
            return
        if isinstance(node, ast_nodes.IfStatement):
            # Attribute condition cost to 'if' line
            self._record(node.line, degree_inc=0)
            self._visit(node.condition)
            self._visit_block(node.then_branch)
            self._visit_block(node.else_branch)
            return
        if isinstance(node, (ast_nodes.Assignment, ast_nodes.CallStatement, ast_nodes.ReturnStatement, ast_nodes.PrintStatement)):
            self._record(node.line, degree_inc=0)
            # visit expressions to catch nested structures if any
            if isinstance(node, ast_nodes.Assignment):
                self._visit(node.target)
                self._visit(node.value)
            elif isinstance(node, ast_nodes.CallStatement):
                for arg in node.arguments:
                    self._visit(arg)
            elif isinstance(node, ast_nodes.ReturnStatement):
                if node.value is not None:
                    self._visit(node.value)
            elif isinstance(node, ast_nodes.PrintStatement):
                self._visit(node.expression)
            return
        # Expressions: traverse to find anything nested, but do not record line cost
        if isinstance(node, ast_nodes.BinaryOperation):
            self._visit(node.left)
            self._visit(node.right)
            return
        if isinstance(node, ast_nodes.UnaryOperation):
            self._visit(node.operand)
            return
        if isinstance(node, ast_nodes.ArrayAccess):
            self._visit(node.base)
            self._visit(node.index)
            return
        if isinstance(node, ast_nodes.FieldAccess):
            self._visit(node.base)
            return
        if isinstance(node, ast_nodes.RangeExpression):
            self._visit(node.start)
            self._visit(node.end)
            return
        # Leaf nodes: Identifier, Number, BooleanLiteral, NullLiteral, StringLiteral, LengthCall → nothing to do
        return

    # -------------------- heuristics --------------------

    def _is_log_while(self, node: ast_nodes.WhileLoop) -> bool:
        var = self._extract_loop_variable(node.condition)
        if not var:
            return False
        return self._body_reduces_var_by_factor(node.body, var)

    def _extract_loop_variable(self, expr: ast_nodes.Expression | None) -> str | None:
        if expr is None:
            return None
        if isinstance(expr, ast_nodes.BinaryOperation) and expr.operator in {"<", "<=", ">", ">=", "="}:
            if isinstance(expr.left, ast_nodes.Identifier):
                return expr.left.name
            if isinstance(expr.right, ast_nodes.Identifier):
                return expr.right.name
        return None

    def _body_reduces_var_by_factor(self, statements: List[ast_nodes.Statement], var_name: str) -> bool:
        for st in statements:
            if isinstance(st, ast_nodes.Assignment):
                if isinstance(st.target, ast_nodes.Identifier) and st.target.name == var_name:
                    val = st.value
                    if isinstance(val, ast_nodes.BinaryOperation):
                        # i := i / c  OR  i := i div c
                        if isinstance(val.left, ast_nodes.Identifier) and val.left.name == var_name:
                            if val.operator in {"/", "div"}:
                                if isinstance(val.right, ast_nodes.Number) and val.right.value > 1:
                                    return True
            elif isinstance(st, ast_nodes.IfStatement):
                if self._body_reduces_var_by_factor(st.then_branch, var_name):
                    return True
                if self._body_reduces_var_by_factor(st.else_branch, var_name):
                    return True
            elif isinstance(st, ast_nodes.WhileLoop):
                if self._body_reduces_var_by_factor(st.body, var_name):
                    return True
            elif isinstance(st, ast_nodes.ForLoop):
                if self._body_reduces_var_by_factor(st.body, var_name):
                    return True
        return False

    def _is_binary_search_while(self, node: ast_nodes.WhileLoop) -> bool:
        """Detecta heurísticamente un while de búsqueda binaria.

        Patrón aproximado que buscamos:
        - Condición combina variables que representan un rango (ej. inicio, fin)
          con una comparación (<=, <, >=, >) y algún flag de encontrado.
        - Dentro del cuerpo se calcula un "medio" como (inicio + fin) / 2 ó div 2.
        - Luego se actualizan inicio o fin usando medio ± 1.

        No intentamos ser perfectos; si encontramos el patrón, tratamos el bucle
        como logarítmico en el análisis por línea.
        """
        # 1. Necesitamos poder hallar identificadores para los extremos e índice medio
        # Buscamos asignaciones del tipo: medio := (inicio + fin) div 2
        if not isinstance(node.body, list):
            return False

        medio_name: str | None = None
        lower_name: str | None = None
        upper_name: str | None = None

        for st in node.body:
            if isinstance(st, ast_nodes.Assignment):
                # medio := (inicio + fin) op 2
                if isinstance(st.target, ast_nodes.Identifier) and isinstance(st.value, ast_nodes.BinaryOperation):
                    # (inicio + fin) div 2   ó   (inicio + fin) / 2
                    val = st.value
                    if val.operator in {"div", "/"} and isinstance(val.left, ast_nodes.BinaryOperation):
                        sum_expr = val.left
                        if sum_expr.operator == "+" and isinstance(sum_expr.left, ast_nodes.Identifier) and isinstance(sum_expr.right, ast_nodes.Identifier):
                            if isinstance(val.right, ast_nodes.Number) and val.right.value == 2:
                                medio_name = st.target.name
                                lower_name = sum_expr.left.name
                                upper_name = sum_expr.right.name
                                break

        if not (medio_name and lower_name and upper_name):
            return False

        # 2. Verificar que en el cuerpo se actualizan los extremos usando medio ± 1
        def updates_bounds(statements: list[ast_nodes.Statement]) -> bool:
            saw_update_lower = False
            saw_update_upper = False
            for st in statements:
                if isinstance(st, ast_nodes.Assignment):
                    if isinstance(st.target, ast_nodes.Identifier):
                        # fin := medio - 1
                        if st.target.name == upper_name and isinstance(st.value, ast_nodes.BinaryOperation):
                            v = st.value
                            if v.operator == "-" and isinstance(v.left, ast_nodes.Identifier) and v.left.name == medio_name:
                                saw_update_upper = True
                        # inicio := medio + 1
                        if st.target.name == lower_name and isinstance(st.value, ast_nodes.BinaryOperation):
                            v = st.value
                            if v.operator == "+" and isinstance(v.left, ast_nodes.Identifier) and v.left.name == medio_name:
                                saw_update_lower = True
                elif isinstance(st, ast_nodes.IfStatement):
                    if updates_bounds(st.then_branch):
                        saw_update_lower = True or saw_update_lower
                        saw_update_upper = True or saw_update_upper
                    if updates_bounds(st.else_branch):
                        saw_update_lower = True or saw_update_lower
                        saw_update_upper = True or saw_update_upper
            return saw_update_lower and saw_update_upper

        return updates_bounds(node.body)
