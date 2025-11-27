# funcion que conecta a el parser (arbol), con el solver (matematico)

from dataclasses import dataclass
from typing import Any
from parsing import ast_nodes
from .recurrence_solver import RecurrenceRelation
from .complexity_engine import ComplexityEngine, ComplexityResult


@dataclass(slots=True)
class ExtractionResult:
    """Combined result returned by the extractor.

    - relation: the RecurrenceRelation (string form) built from the AST
    - structural: ComplexityResult produced by the ComplexityEngine (Ω/O/Θ)
    """
    relation: RecurrenceRelation
    structural: ComplexityResult

class GenericASTVisitor:
    """
    Recorre el AST buscando patrones de complejidad:
    - Profundidad de bucles (ForLoop/WhileLoop) -> f(n)
    - Cantidad de llamadas recursivas -> 'a'
    """
    def __init__(self):
        self.loop_depth = 0         #Profundidad actual de bucles
        self.max_loop_depth = 0     #Profundidad máxima encontrada
        self.log_depth = 0          #Profundidad actual de bucles logarítmicos
        self.max_log_depth = 0      #Máxima cantidad de factores log detectados
        self.has_log_loop = False
        self.recursive_calls = 0
        # Contador específico para llamadas recursivas que ocurren dentro de bucles
        self.recursive_calls_in_loop = 0
        # Registro de llamadas que ocurren dentro de bucles: callee -> count
        self.calls_in_loops: dict[str, int] = {}
        
        # Heurística simple: si hay restas (n-1) o divisiones (n/2)
        # Por defecto asumimos desconocido hasta ver argumentos
        self.recursion_type = "unknown" 

    def visit(self, node, current_func_name="main"):
        """Despachador dinámico: llama a visit_NombreClase"""
        if node is None:
            return

        # Obtenemos el nombre de la clase del nodo (ej: 'ForLoop', 'IfStatement')
        method_name = f'visit_{type(node).__name__}'
        
        # Si existe el método específico, úsalo. Si no, usa generic_visit
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, current_func_name)

    def generic_visit(self, node, current_func_name):
        """Recorre ciegamente todos los hijos del nodo"""
        # Lista de atributos comunes donde suelen estar los hijos en un AST
        child_fields = ['body', 'then_branch', 'else_branch', 'declarations', 'procedures']
        
        for field in child_fields:
            if hasattr(node, field):
                val = getattr(node, field)
                if isinstance(val, list):
                    # Detectar bucles secuenciales en listas (body, etc)
                    self._visit_statement_list(val, current_func_name)
                else:
                    self.visit(val, current_func_name)
    
    def _visit_statement_list(self, statements, current_func_name):
        """Visita una lista de statements, detectando bucles secuenciales."""
        i = 0
        while i < len(statements):
            stmt = statements[i]
            
            # Detectar múltiples bucles consecutivos (secuenciales, no anidados)
            if isinstance(stmt, (ast_nodes.ForLoop, ast_nodes.WhileLoop, ast_nodes.RepeatUntilLoop)):
                consecutive_loops = [stmt]
                j = i + 1
                while j < len(statements) and isinstance(statements[j], (ast_nodes.ForLoop, ast_nodes.WhileLoop, ast_nodes.RepeatUntilLoop)):
                    consecutive_loops.append(statements[j])
                    j += 1
                
                # Si hay múltiples bucles consecutivos, son secuenciales
                if len(consecutive_loops) > 1:
                    # Incrementar profundidad UNA vez para todos
                    self.loop_depth += 1
                    if self.loop_depth > self.max_loop_depth:
                        self.max_loop_depth = self.loop_depth
                    
                    # Visitar el cuerpo de cada bucle secuencial
                    for loop in consecutive_loops:
                        if hasattr(loop, 'body'):
                            self._visit_statement_list(loop.body, current_func_name)
                    
                    self.loop_depth -= 1
                    i = j
                else:
                    # Un solo bucle, visitar normalmente
                    self.visit(stmt, current_func_name)
                    i += 1
            else:
                self.visit(stmt, current_func_name)
                i += 1

    def visit_ForLoop(self, node, current_func_name):
        """Al entrar a un bucle, sumamos profundidad"""
        self.loop_depth += 1
        if self.loop_depth > self.max_loop_depth:
            self.max_loop_depth = self.loop_depth
            
        # Visitamos los hijos dentro del bucle
        self.generic_visit(node, current_func_name)
        
        self.loop_depth -= 1 # Al salir, restamos

    def visit_WhileLoop(self, node, current_func_name):
        """Distingue entre bucles lineales, logarítmicos y de desplazamiento."""
        if self._is_binary_search_while(node) or self._is_log_while(node):
            self.has_log_loop = True
            self.log_depth += 1
            if self.log_depth > self.max_log_depth:
                self.max_log_depth = self.log_depth
            self.generic_visit(node, current_func_name)
            self.log_depth -= 1
        elif self._is_array_shift_while(node):
            # Bucles de desplazamiento: no incrementan profundidad, son operaciones auxiliares
            # Se consideran parte del costo lineal del algoritmo padre
            self.generic_visit(node, current_func_name)
        else:
            self.visit_ForLoop(node, current_func_name)

    def visit_CallStatement(self, node, current_func_name):
        """Detecta si llamamos a la misma función (Recursión) y analiza tipo de reducción."""
        # Asumimos que node.name tiene el nombre de la función llamada
        # En tu AST vi que usas 'self' para recursión a veces
        callee = getattr(node, 'name', '')
        
        if callee == current_func_name or callee == 'self':
            self.recursive_calls += 1
            # Si la llamada ocurre dentro de un bucle, lo registramos
            if self.loop_depth > 0:
                self.recursive_calls_in_loop += 1
            
            # Analizar argumentos para determinar tipo de recursión
            reduction_type = self._analyze_recursive_call_arguments(node)
            if reduction_type and self.recursion_type == "unknown":
                self.recursion_type = reduction_type
        
        # Registrar cualquier llamada (no solo recursiva) que ocurra dentro de un bucle
        if self.loop_depth > 0 and callee:
            key = callee.lower()
            self.calls_in_loops[key] = self.calls_in_loops.get(key, 0) + 1
    
    def _analyze_recursive_call_arguments(self, call_node) -> str:
        """Analiza los argumentos de una llamada recursiva para determinar el tipo de reducción.
        
        Retorna:
        - 'linear': n-1, n-k (reducción lineal)
        - 'divide': n/2, n div 2 (divide y conquista)
        - 'unknown': no se pudo determinar
        """
        if not hasattr(call_node, 'arguments') or not call_node.arguments:
            return "unknown"
        
        for arg in call_node.arguments:
            # Buscar patrones de reducción
            if isinstance(arg, ast_nodes.BinaryOperation):
                # n - constante (ej: n-1)
                if arg.operator == "-" and isinstance(arg.right, ast_nodes.Number):
                    return "linear"
                
                # n / constante o n div constante
                if arg.operator in {"/", "div"}:
                    if isinstance(arg.right, ast_nodes.Number) and arg.right.value >= 2:
                        return "divide"
                    
                    # (low+high)/2 o similar - patrón de búsqueda binaria
                    if isinstance(arg.left, ast_nodes.BinaryOperation) and arg.left.operator == "+":
                        return "divide"
        
        return "unknown"

    def _is_log_while(self, node):
        var = self._extract_loop_variable(node.condition)
        if not var:
            return False
        return self._body_reduces_var_by_factor(node.body, var)
    
    def _is_array_shift_while(self, node):
        """Detecta bucles de desplazamiento de arreglo (patrón: arr[i] ← arr[i-1], i--)"""
        var = self._extract_loop_variable(node.condition)
        if not var:
            return False
        # Buscar asignación de arreglo con índice decremental
        for st in node.body:
            if isinstance(st, ast_nodes.Assignment):
                # arr[i] ← arr[i-1] o similar
                if isinstance(st.target, ast_nodes.ArrayAccess) and isinstance(st.value, ast_nodes.ArrayAccess):
                    # Verificar que el índice se decrementa
                    if self._body_decrements_variable(node.body, var):
                        return True
        return False
    
    def _body_decrements_variable(self, statements, var_name: str) -> bool:
        """Verifica si el cuerpo decrementa una variable (i ← i - 1)"""
        for st in statements:
            if isinstance(st, ast_nodes.Assignment):
                if isinstance(st.target, ast_nodes.Identifier) and st.target.name == var_name:
                    val = st.value
                    if isinstance(val, ast_nodes.BinaryOperation):
                        if isinstance(val.left, ast_nodes.Identifier) and val.left.name == var_name:
                            if val.operator == "-" and isinstance(val.right, ast_nodes.Number):
                                return True
        return False

    def _extract_loop_variable(self, expr):
        if expr is None:
            return None
        if isinstance(expr, ast_nodes.BinaryOperation) and expr.operator in {"<", "<=", ">", ">=", "="}:
            if isinstance(expr.left, ast_nodes.Identifier):
                return expr.left.name
            if isinstance(expr.right, ast_nodes.Identifier):
                return expr.right.name
        if isinstance(expr, ast_nodes.BinaryOperation) and expr.operator in {"and", "or"}:
            left = self._extract_loop_variable(expr.left)
            if left:
                return left
            return self._extract_loop_variable(expr.right)
        return None

    def _body_reduces_var_by_factor(self, statements, var_name: str) -> bool:
        for st in statements:
            if isinstance(st, ast_nodes.Assignment):
                if isinstance(st.target, ast_nodes.Identifier) and st.target.name == var_name:
                    val = st.value
                    if isinstance(val, ast_nodes.BinaryOperation):
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
        if not isinstance(node.body, list):
            return False

        medio_name = None
        lower_name = None
        upper_name = None

        for st in node.body:
            if isinstance(st, ast_nodes.Assignment):
                if isinstance(st.target, ast_nodes.Identifier) and isinstance(st.value, ast_nodes.BinaryOperation):
                    val = st.value
                    if val.operator in {"div", "/"} and isinstance(val.left, ast_nodes.BinaryOperation):
                        sum_expr = val.left
                        if (
                            sum_expr.operator == "+"
                            and isinstance(sum_expr.left, ast_nodes.Identifier)
                            and isinstance(sum_expr.right, ast_nodes.Identifier)
                            and isinstance(val.right, ast_nodes.Number)
                            and val.right.value == 2
                        ):
                            medio_name = st.target.name
                            lower_name = sum_expr.left.name
                            upper_name = sum_expr.right.name
                            break

        if not (medio_name and lower_name and upper_name):
            return False

        def updates_bounds(statements):
            saw_lower = False
            saw_upper = False
            for st in statements:
                if isinstance(st, ast_nodes.Assignment) and isinstance(st.target, ast_nodes.Identifier):
                    if (
                        st.target.name == upper_name
                        and isinstance(st.value, ast_nodes.BinaryOperation)
                        and st.value.operator == "-"
                        and isinstance(st.value.left, ast_nodes.Identifier)
                        and st.value.left.name == medio_name
                    ):
                        saw_upper = True
                    if (
                        st.target.name == lower_name
                        and isinstance(st.value, ast_nodes.BinaryOperation)
                        and st.value.operator == "+"
                        and isinstance(st.value.left, ast_nodes.Identifier)
                        and st.value.left.name == medio_name
                    ):
                        saw_lower = True
                elif isinstance(st, ast_nodes.IfStatement):
                    l_then, u_then = updates_bounds(st.then_branch)
                    l_else, u_else = updates_bounds(st.else_branch)
                    saw_lower = saw_lower or l_then or l_else
                    saw_upper = saw_upper or u_then or u_else
            return saw_lower, saw_upper

        lower_ok, upper_ok = updates_bounds(node.body)
        return lower_ok and upper_ok

def extract_generic_recurrence(ast_root, func_name="self") -> ExtractionResult:
    """
    Función principal que usa el Visitor para generar la ecuación.
    Analiza el procedimiento recursivo principal, ignorando subrutinas auxiliares.
    """
    # Si es un Program con procedimientos, encontrar el recursivo principal
    main_proc = None
    if hasattr(ast_root, 'procedures') and ast_root.procedures:
        # Buscar el procedimiento que hace llamadas recursivas
        for proc in ast_root.procedures:
            # Contar llamadas recursivas en este procedimiento
            test_visitor = GenericASTVisitor()
            for stmt in proc.body:
                test_visitor.visit(stmt, proc.name)
            
            if test_visitor.recursive_calls > 0:
                main_proc = proc
                func_name = proc.name
                break
        
        # Si no hay recursivo, tomar el último (probablemente el principal)
        if not main_proc and ast_root.procedures:
            main_proc = ast_root.procedures[-1]
            func_name = main_proc.name
    
    # Analizar solo el procedimiento principal recursivo
    visitor = GenericASTVisitor()
    if main_proc:
        # Analizar solo el cuerpo del procedimiento principal
        for stmt in main_proc.body:
            visitor.visit(stmt, func_name)
    else:
        # Fallback: analizar todo el AST
        visitor.visit(ast_root, func_name)
    
    # 1. Construir f(n) (Costo local del procedimiento principal)
    poly_degree = visitor.max_loop_depth
    log_power = visitor.max_log_depth

    def _format_growth(degree: int, logp: int) -> str:
        parts = []
        if degree > 0:
            parts.append("n" if degree == 1 else f"n^{degree}")
        if logp > 0:
            parts.append("log n" if logp == 1 else f"(log n)^{logp}")
        return " ".join(parts) if parts else "1"

    fn = _format_growth(poly_degree, log_power)

    # 2. Construir T(n) (Parte recursiva)
    a = visitor.recursive_calls
    a_in_loop = visitor.recursive_calls_in_loop
    
    recurrence_str = ""
    explanation = ""

    # PRIORIDAD 1: Recursión detectada
    if a > 0:
        # Algoritmo recursivo - generar recurrencia basada en el tipo
        
        # Determinar b (factor de división) basado en análisis de argumentos
        if visitor.recursion_type == "divide":
            b = 2  # Asumimos división por 2 (común en divide-y-conquista)
        elif visitor.recursion_type == "linear":
            b = 1  # n-1, reducción lineal
        else:
            # Heurística: si hay 2 o más llamadas, probablemente divide-y-conquista
            b = 2 if a >= 2 else 1
        
        # Determinar f(n) (trabajo fuera de la recursión)
        # Si hay bucles locales, usar eso
        if poly_degree > 0:
            work_term = fn
        elif log_power > 0:
            work_term = fn
        # Si hay llamadas a subrutinas (ej: Particion en QuickSort)
        elif visitor.calls_in_loops or any(call for call in getattr(visitor, '_non_recursive_calls', [])):
            # Analizar complejidad de subrutinas llamadas
            # Para QuickSort con Particion, sabemos que Particion es O(n)
            if hasattr(ast_root, 'procedures') and ast_root.procedures:
                # Analizar la primera subrutina (probablemente auxiliar como Particion)
                aux_proc = ast_root.procedures[0]
                aux_visitor = GenericASTVisitor()
                for stmt in aux_proc.body:
                    aux_visitor.visit(stmt, aux_proc.name)
                
                # Usar la complejidad de la subrutina como f(n)
                aux_degree = aux_visitor.max_loop_depth
                if aux_degree > 0:
                    work_term = _format_growth(aux_degree, aux_visitor.max_log_depth)
                else:
                    work_term = "n"  # Por defecto lineal para subrutinas
            else:
                work_term = "n"
        else:
            # Por defecto, trabajo constante o lineal
            work_term = "n" if a >= 2 else "1"
        
        # Construir recurrencia: T(n) = a*T(n/b) + f(n)
        if b == 1:
            recurrence_str = f"T(n) = {a}*T(n-1) + {work_term}"
            explanation = f"Recursión lineal: {a} llamada(s) con reducción n-1 y costo local O({work_term})."
        else:
            recurrence_str = f"T(n) = {a}*T(n/{b}) + {work_term}"
            explanation = f"Divide y Conquista: {a} llamada(s) recursivas, división por {b}, costo local O({work_term})."
    
    # PRIORIDAD 2: Puramente iterativo (sin recursión)
    elif a == 0:
        # Iterativo - verificar si hay llamadas en bucles para ajustar f(n)
        effective_fn = fn
        if visitor.calls_in_loops:
            # Previsualización: si hay llamadas en bucles, el costo real será mayor
            # (lo calculamos más adelante en detalle, pero aquí damos una pista)
            explanation_parts = [f"Algoritmo iterativo con anidamiento {poly_degree}"]
            if poly_degree > 0:
                explanation_parts.append(f"que invoca subrutinas dentro de bucles")
                # Indicar que el costo real será la combinación
                effective_fn = fn + " × f_subrutina(n)"
            explanation = ". ".join(explanation_parts) + "."
        else:
            if poly_degree == 0 and log_power == 0:
                explanation = "Algoritmo iterativo sin bucles relevantes."
            elif poly_degree > 0 and log_power == 0:
                explanation = f"Algoritmo iterativo con anidamiento {poly_degree}."
            elif poly_degree == 0 and log_power > 0:
                explanation = "Algoritmo iterativo logarítmico (p. ej. búsqueda binaria)."
            else:
                explanation = (
                    f"Algoritmo iterativo con anidamiento {poly_degree} y factor log^{log_power}."
                )
        
        recurrence_str = f"T(n) = {effective_fn}"

    # Construir el objeto de recurrencia
    relation = RecurrenceRelation(
        identifier=func_name,
        recurrence=recurrence_str,
        base_case="T(0) = 1",
        notes=explanation,
    )

    # Además de la recurrencia, generamos la estimación estructural
    # reutilizando el ComplexityEngine para no perder heurísticas existentes.
    engine = ComplexityEngine()
    try:
        structural = engine.analyze(ast_root)
    except Exception:
        # En caso de fallo en el engine, devolvemos una estructura por defecto
        structural = ComplexityResult(
            best_case="Ω(1)", worst_case="O(1)", average_case="Θ(1)", annotations={}
        )

    # ESTRATEGIA: Solo enriquecer las anotaciones, NO sobrescribir las complejidades del motor
    # El ComplexityEngine ya hace un análisis sofisticado (salidas tempranas, branches, etc.)
    # El visitor solo aporta información adicional sobre bucles logarítmicos
    
    expr = _format_growth(poly_degree, log_power)
    if expr != "1":
        structural.annotations = dict(structural.annotations)
        structural.annotations["loop_summary"] = (
            f"Bucles polinomiales: {poly_degree}, bucles logarítmicos: {log_power}."
        )
        # NO sobrescribir best/worst/average - dejar que el motor decida

    # Si hay llamadas a funciones dentro de bucles, calcular la complejidad
    # de las funciones llamadas y ajustar la estimación estructural.
    if visitor.calls_in_loops:
        # Analizar las subrutinas definidas en el programa
        procedures = getattr(ast_root, "procedures", []) or []
        func_structures: dict[str, ComplexityResult] = {}
        for proc in procedures:
            try:
                proc_struct = engine.analyze(proc)
                func_structures[proc.name.lower()] = proc_struct
            except Exception:
                pass

        # También considerar 'self' (la función actual)
        try:
            func_structures[func_name.lower()] = engine.analyze(ast_root)
        except Exception:
            pass

        # Helper: parsear notación Θ(...) en (degree, log_power)
        import re
        def parse_theta(s: str) -> tuple[int, int]:
            s = (s or "").lower()
            deg = 0
            logp = 0
            m = re.search(r"n\^([0-9]+)", s)
            if m:
                deg = int(m.group(1))
            elif "n log" in s or "n * log" in s or "nlog" in s:
                deg = 1
                logp = 1
            elif "n" in s and "^" not in s:
                deg = 1
            m2 = re.search(r"\(log n\)\^([0-9]+)", s)
            if m2:
                logp = int(m2.group(1))
            elif "log n" in s and logp == 0 and deg == 0:
                logp = 1
            return deg, logp

        # Encontrar la complejidad máxima entre las funciones llamadas en bucle
        max_deg = 0
        max_log = 0
        for callee in visitor.calls_in_loops.keys():
            struct = func_structures.get(callee)
            if not struct:
                struct = func_structures.get(callee.lower())
            if struct:
                d, lp = parse_theta(struct.average_case)
                if (d > max_deg) or (d == max_deg and lp > max_log):
                    max_deg = d
                    max_log = lp

        if max_deg > 0 or max_log > 0:
            combined_deg = visitor.max_loop_depth + max_deg
            combined_log = visitor.max_log_depth + max_log

            def format_theta(deg: int, logp: int) -> str:
                inner = _format_growth(deg, logp)
                return f"Θ({inner})"

            # Buscar el mejor caso más optimista entre las funciones llamadas
            best_deg = combined_deg
            best_log = combined_log
            for callee in visitor.calls_in_loops.keys():
                struct = func_structures.get(callee) or func_structures.get(callee.lower())
                if struct:
                    b_deg, b_log = parse_theta(struct.best_case)
                    # El mejor caso puede ser menor si la función tiene salida temprana
                    if b_deg < best_deg or (b_deg == best_deg and b_log < best_log):
                        best_deg = visitor.max_loop_depth + b_deg
                        best_log = visitor.max_log_depth + b_log

            structural.annotations = dict(structural.annotations)
            structural.annotations["calls_in_loops_max_called"] = (
                "Max llamada: "
                + _format_growth(max_deg, max_log)
                + f", combinada con bucles propios (deg={visitor.max_loop_depth}, log={visitor.max_log_depth})"
            )
            
            # SOLO sobrescribir si la complejidad combinada es MAYOR que la del motor
            # Esto respeta casos especiales detectados por el motor (salidas tempranas, etc.)
            current_avg_deg, current_avg_log = parse_theta(structural.average_case)
            if combined_deg > current_avg_deg or (combined_deg == current_avg_deg and combined_log > current_avg_log):
                structural.average_case = format_theta(combined_deg, combined_log)
                structural.worst_case = f"O({_format_growth(combined_deg, combined_log)})"
            
            # Para mejor caso: solo actualizar si la nueva complejidad es diferente y mayor que constante
            current_best_deg, current_best_log = parse_theta(structural.best_case)
            if best_deg > 0 or best_log > 0:
                # Solo actualizar si no es salida temprana (Ω(1))
                if current_best_deg > 0 or current_best_log > 0:
                    structural.best_case = f"Ω({_format_growth(best_deg, best_log)})"
            
            # Refinar la recurrencia para reflejar el costo real combinado
            combined_expr = _format_growth(combined_deg, combined_log)
            relation = RecurrenceRelation(
                identifier=func_name,
                recurrence=f"T(n) = {combined_expr}",
                base_case="T(0) = 1",
                notes=f"Algoritmo iterativo con llamadas anidadas. {structural.annotations['calls_in_loops_max_called']}",
            )

    return ExtractionResult(relation=relation, structural=structural)