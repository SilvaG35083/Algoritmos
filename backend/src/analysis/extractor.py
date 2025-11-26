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
            # Aquí podríamos analizar argumentos para ver si es n-1 o n/2
            # Por ahora lo dejamos a la heurística general

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

    return ExtractionResult(relation=relation, structural=structural)