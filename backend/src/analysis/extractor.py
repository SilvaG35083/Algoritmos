# funcion que conecta a el parser (arbol), con el solver (matematico)

from dataclasses import dataclass, fields
from typing import Any

from parsing import ast_nodes
from .recurrence_solver import RecurrenceRelation

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
        self.program_name = "main"  # Nombre del programa principal
        
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
        """Recorre todos los atributos del nodo buscando hijos."""
        if not hasattr(node, "__slots__") and not hasattr(node, "__dict__"):
            return

        # dataclasses con slots no tienen __dict__, pero podemos usar fields()
        try:
            node_fields = fields(node)
        except TypeError:
            node_fields = ()

        if node_fields:
            iterable = ((f.name, getattr(node, f.name, None)) for f in node_fields)
        else:
            iterable = vars(node).items() if hasattr(node, "__dict__") else ()

        for _, val in iterable:
            if isinstance(val, ast_nodes.Node):
                self.visit(val, current_func_name)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, ast_nodes.Node):
                        self.visit(item, current_func_name)

    def visit_Program(self, node: ast_nodes.Program, current_func_name):
        new_name = (node.name or current_func_name).lower() if (node.name or current_func_name) else "main"
        # Guardar el nombre del programa para detectar recursión
        self.program_name = new_name
        self.generic_visit(node, new_name)

    def visit_Procedure(self, node: ast_nodes.Procedure, current_func_name):
        proc_name = (node.name or current_func_name).lower()
        self.generic_visit(node, proc_name)

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
        # Obtener el nombre del procedimiento llamado
        callee = getattr(node, 'procedure_name', '')
        if not callee:
            callee = getattr(node, 'name', '')
        callee = callee.lower() if isinstance(callee, str) else callee
        
        # Verificar si es recursión: mismo nombre o 'self' o nombre del programa
        if callee == current_func_name or callee == 'self' or callee == self.program_name:
            self.recursive_calls += 1
            # Aquí podríamos analizar argumentos para ver si es n-1 o n/2
            # Por ahora lo dejamos a la heurística general
        
        # Visitar argumentos
        for arg in getattr(node, "arguments", []):
            self.visit(arg, current_func_name)

    def visit_CallExpression(self, node, current_func_name):
        callee = getattr(node, "name", "")
        callee = callee.lower() if isinstance(callee, str) else callee
        if callee == current_func_name or callee == "self":
            self.recursive_calls += 1
        for arg in getattr(node, "arguments", []):
            self.visit(arg, current_func_name)

    def visit_Assignment(self, node: ast_nodes.Assignment, current_func_name):
        self.visit(node.target, current_func_name)
        self.visit(node.value, current_func_name)

    def visit_ReturnStatement(self, node: ast_nodes.ReturnStatement, current_func_name):
        if node.value:
            self.visit(node.value, current_func_name)

def extract_generic_recurrence(ast_root, func_name="self") -> RecurrenceRelation:
    """
    Función principal que usa el Visitor para generar la ecuación.
    """
    visitor = GenericASTVisitor()
    root_name = (getattr(ast_root, "name", "") or func_name or "self").lower()
    visitor.visit(ast_root, root_name)
    
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

    # Retornamos el objeto listo para el Solver
    return RecurrenceRelation(
        identifier=func_name,
        recurrence=recurrence_str,
        base_case="T(0) = 1",
        notes=explanation
    )