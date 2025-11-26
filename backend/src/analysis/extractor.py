# funcion que conecta a el parser (arbol), con el solver (matematico)

from dataclasses import dataclass
from typing import Any
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
                    for item in val:
                        self.visit(item, current_func_name)
                else:
                    self.visit(val, current_func_name)

    def visit_ForLoop(self, node, current_func_name):
        """Al entrar a un bucle, sumamos profundidad"""
        self.loop_depth += 1
        if self.loop_depth > self.max_loop_depth:
            self.max_loop_depth = self.loop_depth
            
        # Visitamos los hijos dentro del bucle
        self.generic_visit(node, current_func_name)
        
        self.loop_depth -= 1 # Al salir, restamos

    def visit_WhileLoop(self, node, current_func_name):
        """Igual que ForLoop"""
        self.visit_ForLoop(node, current_func_name)

    def visit_CallStatement(self, node, current_func_name):
        """Detecta si llamamos a la misma función (Recursión)"""
        # Asumimos que node.name tiene el nombre de la función llamada
        # En tu AST vi que usas 'self' para recursión a veces
        callee = getattr(node, 'name', '')
        
        if callee == current_func_name or callee == 'self':
            self.recursive_calls += 1
            # Si la llamada ocurre dentro de un bucle, lo registramos
            if self.loop_depth > 0:
                self.recursive_calls_in_loop += 1
            # Aquí podríamos analizar argumentos para ver si es n-1 o n/2
            # Por ahora lo dejamos a la heurística general
        # Registrar cualquier llamada (no solo recursiva) que ocurra dentro de un bucle
        if self.loop_depth > 0 and callee:
            key = callee.lower()
            self.calls_in_loops[key] = self.calls_in_loops.get(key, 0) + 1

def extract_generic_recurrence(ast_root, func_name="self") -> ExtractionResult:
    """
    Función principal que usa el Visitor para generar la ecuación.
    """
    visitor = GenericASTVisitor()
    visitor.visit(ast_root, func_name)
    
    # 1. Construir f(n) (Costo local)
    if visitor.max_loop_depth == 0:
        fn = "1"  # Constante (sin bucles)
    elif visitor.max_loop_depth == 1:
        fn = "n"  # Lineal (1 bucle)
    else:
        fn = f"n^{visitor.max_loop_depth}" # Polinómico (bucles anidados)

    # 2. Construir T(n) (Parte recursiva)
    a = visitor.recursive_calls
    a_in_loop = visitor.recursive_calls_in_loop
    
    recurrence_str = ""
    explanation = ""

    if a == 0:
        # Iterativo
        recurrence_str = f"T(n) = {fn}"
        explanation = f"Algoritmo iterativo con anidamiento {visitor.max_loop_depth}."
    else:
        # Recursivo
        # HEURÍSTICA:
        # - Si a >= 2: Asumimos Divide y Vencerás (n/2) -> MergeSort, QuickSort
        # - Si a == 1 y f(n) == 1: Asumimos Búsqueda Binaria (T(n/2))
        # - Si a == 1 y f(n) >= n: Asumimos Lineal (n-1) -> Factorial
        
        if a >= 2:
            b = 2 # Asunción estándar para D&C
            recurrence_str = f"T(n) = {a}*T(n/{b}) + {fn}"
            explanation = f"Divide y Vencerás: {a} llamadas recursivas y costo local O({fn})."
        
        elif a == 1 and fn == "1":
             recurrence_str = f"T(n) = T(n/2) + {fn}"
             explanation = "Recursión simple con costo constante (tipo Búsqueda Binaria)."
        
        else: # a == 1
             recurrence_str = f"T(n) = T(n-1) + {fn}"
             explanation = "Recursión lineal simple."

    # Construir el objeto de recurrencia
    relation = RecurrenceRelation(
        identifier=func_name,
        recurrence=recurrence_str,
        base_case="T(0) = 1",
        notes=explanation,
    )

    # Además de la recurrencia, generamos la estimación estructural
    # reutilizando el ComplexityEngine para no perder heurísticas existentes.
    try:
        engine = ComplexityEngine()
        structural = engine.analyze(ast_root)
    except Exception:
        # En caso de fallo en el engine, devolvemos una estructura por defecto
        structural = ComplexityResult(
            best_case="Ω(1)", worst_case="O(1)", average_case="Θ(1)", annotations={}
        )

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
            # Combinar con la profundidad del bucle
            combined_deg = visitor.max_loop_depth + max_deg
            combined_log = max_log

            def format_theta(deg: int, logp: int) -> str:
                parts = []
                if deg > 0:
                    parts.append("n" if deg == 1 else f"n^{deg}")
                if logp > 0:
                    parts.append("log n" if logp == 1 else f"(log n)^{logp}")
                expr = " ".join(parts) if parts else "1"
                return f"Θ({expr})"

            structural.annotations = dict(structural.annotations)
            structural.annotations["calls_in_loops_max_called"] = \
                f"Max llamada: n^{max_deg} (log^{max_log}), combinada con bucle depth {visitor.max_loop_depth}"
            structural.average_case = format_theta(combined_deg, combined_log)
            # Ajustar best/worst conservadoramente si están vacíos
            if not structural.best_case:
                structural.best_case = f"Ω(n^{combined_deg})"
            if not structural.worst_case:
                structural.worst_case = f"O(n^{combined_deg})"

    return ExtractionResult(relation=relation, structural=structural)