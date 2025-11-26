"""Constructor de árboles de recursión para visualización."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from parsing import ast_nodes
from .extractor import extract_generic_recurrence
from .recurrence_solver import RecurrenceRelation


@dataclass(slots=True)
class RecursionTreeNode:
    """Nodo del árbol de recursión."""

    label: str  # T(n), T(n/2), etc.
    level: int
    cost: str  # Costo en este nivel
    children: List["RecursionTreeNode"] = field(default_factory=list)
    total_cost: str = ""  # Costo acumulado desde este nodo


@dataclass(slots=True)
class RecursionTree:
    """Árbol de recursión completo."""

    root: RecursionTreeNode
    max_level: int
    total_cost: str
    description: str
    levels: List[Dict] = field(default_factory=list)  # Para serialización
    structure: Dict[str, any] = field(default_factory=dict)


class RecursionTreeBuilder:
    """Construye árboles de recursión a partir de algoritmos recursivos."""

    def build(self, program: ast_nodes.Program) -> Optional[RecursionTree]:
        """Construye un árbol de recursión si el algoritmo es recursivo."""
        # Extraer relación de recurrencia
        try:
            relation = extract_generic_recurrence(program)
        except Exception as e:
            print(f"Error extrayendo recurrencia: {e}")
            return None

        # Verificar si es recursivo - buscar llamadas recursivas en el código
        has_recursion = self._has_recursive_calls(program)
        
        if not has_recursion:
            return None

        # Verificar si la ecuación tiene recursión
        if "T(" not in relation.recurrence:
            return None
            
        recurrence_part = relation.recurrence.split("=")[1] if "=" in relation.recurrence else ""
        if "T(" not in recurrence_part:
            return None

        # Parsear la relación de recurrencia
        params = self._parse_recurrence(relation.recurrence)
        if not params:
            return None

        a, b, fn = params

        # Construir el árbol con más profundidad
        root = self._build_tree_recursive("T(n)", 0, a, b, fn, max_depth=5)

        # Calcular costo total
        total_cost = self._calculate_total_cost(root, a, b, fn)

        # Construir niveles para visualización
        levels = self._build_levels(root)
        structure = self._serialize_tree(root)

        # Calcular altura del árbol
        height = self._calculate_tree_height(root)

        return RecursionTree(
            root=root,
            max_level=height,
            total_cost=total_cost,
            description=f"Árbol de recursión para {relation.recurrence}. Altura: {height} niveles.",
            levels=levels,
            structure=structure,
        )

    def _has_recursive_calls(self, program: ast_nodes.Program) -> bool:
        """Verifica si el programa tiene llamadas recursivas."""
        program_name = (getattr(program, 'name', '') or 'main').lower()
        
        def check_node(node, current_func: str):
            if node is None:
                return False
            
            # Verificar CallStatement
            if isinstance(node, ast_nodes.CallStatement):
                callee = getattr(node, 'procedure_name', '').lower()
                if callee == program_name or callee == 'self' or callee == current_func:
                    return True
            
            # Verificar CallExpression
            if isinstance(node, ast_nodes.CallExpression):
                callee = getattr(node, 'name', '').lower()
                if callee == program_name or callee == 'self' or callee == current_func:
                    return True
            
            # Recorrer hijos
            if hasattr(node, '__dict__'):
                for attr_name, attr_value in vars(node).items():
                    if isinstance(attr_value, ast_nodes.Node):
                        if check_node(attr_value, current_func):
                            return True
                    elif isinstance(attr_value, list):
                        for item in attr_value:
                            if isinstance(item, ast_nodes.Node):
                                if check_node(item, current_func):
                                    return True
            
            return False
        
        return check_node(program, program_name)

    def _parse_recurrence(self, recurrence: str) -> Optional[tuple[int, int, str]]:
        """Parsea una recurrencia T(n) = a*T(n/b) + f(n) y retorna (a, b, f(n))."""
        import re
        
        # Limpiar espacios
        s = recurrence.replace(" ", "")
        
        # Patrón: T(n) = a*T(n/b) + f(n)
        pattern = r"T\(n\)=(\d*\*?)?T\(n/(\d+)\)\+(.*)"
        match = re.search(pattern, s, re.IGNORECASE)
        
        if not match:
            return None
        
        a_str, b_str, fn_str = match.groups()
        
        # Procesar 'a'
        if not a_str:
            a = 1
        else:
            a = int(a_str.replace("*", ""))
        
        # Procesar 'b'
        b = int(b_str)
        if b <= 1:
            return None
        
        # Procesar 'f(n)' - simplificado
        fn = fn_str.strip()
        
        return (a, b, fn)

    def _build_tree_recursive(
        self, label: str, level: int, a: int, b: int, fn: str, max_depth: int = 5
    ) -> RecursionTreeNode:
        """Construye el árbol recursivamente."""
        if level >= max_depth:
            # Caso base: hojas del árbol
            return RecursionTreeNode(
                label=label,
                level=level,
                cost="O(1)",
                children=[],
                total_cost="O(1)"
            )
        
        # Crear nodo actual
        node = RecursionTreeNode(
            label=label,
            level=level,
            cost=fn,
            children=[],
            total_cost=""
        )
        
        # Crear hijos
        children: List[RecursionTreeNode] = []
        for i in range(a):
            # Calcular tamaño del subproblema
            if "n/" in label:
                # Extraer n actual
                current_n = label.split("(")[1].split(")")[0]
                if "/" in current_n:
                    parts = current_n.split("/")
                    if len(parts) == 2:
                        try:
                            divisor = int(parts[1])
                            new_divisor = divisor * b
                            child_label = f"T(n/{new_divisor})"
                        except:
                            child_label = f"T(n/{b})"
                    else:
                        child_label = f"T(n/{b})"
                else:
                    child_label = f"T(n/{b})"
            else:
                child_label = f"T(n/{b})"
            
            child = self._build_tree_recursive(child_label, level + 1, a, b, fn, max_depth)
            children.append(child)
        
        node.children = children
        
        # Calcular costo total de este nodo
        node.total_cost = self._calculate_node_cost(node, a, b, fn)
        
        return node

    def _calculate_node_cost(self, node: RecursionTreeNode, a: int, b: int, fn: str) -> str:
        """Calcula el costo de un nodo y sus hijos."""
        # El costo en este nivel es f(n) multiplicado por el número de nodos en este nivel
        num_nodes = a ** node.level if node.level > 0 else 1
        return f"{num_nodes} * {fn}"

    def _calculate_total_cost(self, root: RecursionTreeNode, a: int, b: int, fn: str) -> str:
        """Calcula el costo total del árbol."""
        # Para T(n) = a*T(n/b) + f(n) con f(n) = n
        # Si a = b (caso balanceado), el costo es O(n log n)
        if a == b and fn == "n":
            return "O(n log n)"
        # Si a < b, el costo es O(n)
        elif a < b:
            return "O(n)"
        # Si a > b, el costo es O(n^log_b(a))
        else:
            import math
            exponent = math.log(a, b)
            if exponent == int(exponent):
                return f"O(n^{int(exponent)})"
            else:
                return f"O(n^{round(exponent, 2)})"

    def _build_levels(self, root: RecursionTreeNode) -> List[Dict]:
        """Construye una lista de niveles para visualización."""
        levels_dict: Dict[int, Dict] = {}
        
        def traverse(node: RecursionTreeNode):
            level = node.level
            if level not in levels_dict:
                levels_dict[level] = {
                    "level": level,
                    "nodes": [],
                    "cost": node.cost,
                    "total_cost": node.total_cost
                }
            levels_dict[level]["nodes"].append(node.label)
            
            for child in node.children:
                traverse(child)
        
        traverse(root)
        
        # Convertir a lista ordenada
        levels = [levels_dict[i] for i in sorted(levels_dict.keys())]
        return levels

    def _serialize_tree(self, root: RecursionTreeNode) -> Dict:
        """Serializa el árbol en un diccionario para JSON."""
        return {
            "label": root.label,
            "level": root.level,
            "cost": root.cost,
            "total_cost": root.total_cost,
            "children": [self._serialize_tree(child) for child in root.children]
        }

    def _calculate_tree_height(self, root: RecursionTreeNode) -> int:
        """Calcula la altura del árbol."""
        if not root.children:
            return root.level
        
        max_child_height = max(self._calculate_tree_height(child) for child in root.children)
        return max(root.level, max_child_height)

    def _get_all_nodes(self, root: RecursionTreeNode) -> List[RecursionTreeNode]:
        """Obtiene todos los nodos del árbol."""
        nodes = [root]
        for child in root.children:
            nodes.extend(self._get_all_nodes(child))
        return nodes

    def _get_all_nodes_at_level(self, root: RecursionTreeNode, target_level: int) -> List[RecursionTreeNode]:
        """Obtiene todos los nodos en un nivel específico."""
        nodes = []
        if root.level == target_level:
            nodes.append(root)
        for child in root.children:
            nodes.extend(self._get_all_nodes_at_level(child, target_level))
        return nodes

