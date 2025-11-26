"""Detector y analizador de algoritmos de Programación Dinámica."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import re

from parsing import ast_nodes
from .recursion_tree_builder import RecursionTreeBuilder
from .extractor import extract_generic_recurrence


@dataclass(slots=True)
class DPTable:
    """Representa una tabla de programación dinámica."""

    name: str  # "optimos", "caminos", "soa"
    dimensions: List[str]  # ["n", "m"] para tabla 2D
    data: Dict[str, Any] = field(default_factory=dict)  # Claves como strings "[i, j]"
    description: str = ""


@dataclass(slots=True)
class DPAnalysis:
    """Análisis completo de un algoritmo de Programación Dinámica."""

    is_dp: bool
    approach: str  # "top_down" o "bottom_up"
    model_type: str  # Descripción del modelo (ej: "Knapsack 0/1", "Fibonacci", etc.)
    tables: List[DPTable] = field(default_factory=list)
    space_complexity: str = ""
    explanation: str = ""
    reconstruction_steps: List[str] = field(default_factory=list)


class DPDetector:
    """Detecta y analiza algoritmos de Programación Dinámica."""

    def __init__(self):
        self._dp_patterns = {
            "fibonacci": {
                "indicators": ["fibonacci", "fib", "n-1", "n-2"],
                "model": "Fibonacci",
                "dimensions": ["n"],
                "approach": "top_down",
            },
            "knapsack": {
                "indicators": ["knapsack", "peso", "valor", "capacidad"],
                "model": "Knapsack 0/1",
                "dimensions": ["n", "W"],
                "approach": "bottom_up",
            },
            "lcs": {
                "indicators": ["lcs", "longest", "common", "subsequence", "substring"],
                "model": "Longest Common Subsequence",
                "dimensions": ["m", "n"],
                "approach": "bottom_up",
            },
            "edit_distance": {
                "indicators": ["edit", "distance", "levenshtein", "transform"],
                "model": "Edit Distance",
                "dimensions": ["m", "n"],
                "approach": "bottom_up",
            },
            "coin_change": {
                "indicators": ["coin", "moneda", "cambio", "sum"],
                "model": "Coin Change",
                "dimensions": ["n", "amount"],
                "approach": "bottom_up",
            },
        }

    def detect(self, program: ast_nodes.Program) -> DPAnalysis:
        """Detecta si el algoritmo usa Programación Dinámica."""
        # Verificar si hay recursión con subproblemas superpuestos
        has_recursion = self._has_recursion(program)
        has_memo = self._has_memoization_structures(program)

        if not (has_recursion and has_memo):
            return DPAnalysis(
                is_dp=False,
                approach="",
                model_type="",
                explanation="No se detectaron patrones de Programación Dinámica.",
            )

        # Identificar el tipo de problema DP
        model_type, approach = self._identify_dp_type(program)

        # Generar tablas
        tables = self._generate_tables(program, model_type, approach)

        # Generar pasos de reconstrucción
        reconstruction_steps = self._generate_reconstruction_steps(model_type, tables)

        return DPAnalysis(
            is_dp=True,
            approach=approach,
            model_type=model_type,
            tables=tables,
            reconstruction_steps=reconstruction_steps,
            space_complexity=self._calculate_space_complexity(tables),
            explanation=f"Se detectó un algoritmo de Programación Dinámica tipo {model_type} usando enfoque {approach}.",
        )

    def _has_recursion(self, program: ast_nodes.Program) -> bool:
        """Verifica si el algoritmo tiene recursión."""
        builder = RecursionTreeBuilder()
        return builder._has_recursive_calls(program)

    def _has_memoization_structures(self, program: ast_nodes.Program) -> bool:
        """Verifica si hay estructuras de memoización (arrays con 'new Array')."""
        def check_node(node):
            if node is None:
                return False
            
            # Buscar ArrayCreation (new Array)
            if isinstance(node, ast_nodes.ArrayCreation):
                return True
            
            # Buscar asignaciones a arrays que podrían ser tablas de memoización
            if isinstance(node, ast_nodes.Assignment):
                if isinstance(node.target, ast_nodes.Identifier):
                    target_name = node.target.name.lower()
                    if any(keyword in target_name for keyword in ["memo", "dp", "table", "cache", "optimos", "caminos"]):
                        return True
            
            # Recorrer hijos
            if hasattr(node, '__dict__'):
                for attr_value in vars(node).values():
                    if isinstance(attr_value, ast_nodes.Node):
                        if check_node(attr_value):
                            return True
                    elif isinstance(attr_value, list):
                        for item in attr_value:
                            if isinstance(item, ast_nodes.Node):
                                if check_node(item):
                                    return True
            
            return False
        
        return check_node(program)

    def _identify_dp_type(self, program: ast_nodes.Program) -> Tuple[str, str]:
        """Identifica el tipo de problema DP y el enfoque."""
        program_str = str(program).lower()
        
        # Buscar patrones conocidos
        for pattern_name, pattern_info in self._dp_patterns.items():
            if any(indicator in program_str for indicator in pattern_info["indicators"]):
                return pattern_info["model"], pattern_info["approach"]
        
        # Por defecto, si hay memoización y recursión, es top-down
        if self._has_memoization_structures(program):
            return "Memoization General", "top_down"
        
        return "Desconocido", "top_down"

    def _generate_tables(self, program: ast_nodes.Program, model_type: str, approach: str) -> List[DPTable]:
        """Genera las tablas de DP."""
        tables = []
        
        # Tabla de óptimos
        optimos = DPTable(
            name="optimos",
            dimensions=["n"],
            description="Almacena los valores óptimos de los subproblemas",
            data={}
        )
        tables.append(optimos)
        
        # Tabla de caminos (si aplica)
        if model_type not in ["Fibonacci"]:
            caminos = DPTable(
                name="caminos",
                dimensions=["n"],
                description="Almacena las decisiones para reconstruir la solución",
                data={}
            )
            tables.append(caminos)
        
        return tables

    def _generate_reconstruction_steps(self, model_type: str, tables: List[DPTable]) -> List[str]:
        """Genera los pasos de reconstrucción de la solución."""
        steps = [
            f"1. Identificar el modelo: {model_type}",
            "2. Llenar la tabla de óptimos desde los casos base",
            "3. Usar la tabla de caminos para reconstruir la solución",
            "4. La solución se construye desde el final hacia atrás"
        ]
        return steps

    def _calculate_space_complexity(self, tables: List[DPTable]) -> str:
        """Calcula la complejidad espacial basada en las tablas."""
        total_dims = sum(len(table.dimensions) for table in tables)
        if total_dims == 1:
            return "O(n)"
        elif total_dims == 2:
            return "O(n*m)"
        else:
            return "O(n^k)"

    def build_dp_tables(self, problem_size: int, model_type: str, approach: str) -> Dict[str, Dict]:
        """Construye tablas de ejemplo para visualización."""
        # Tabla de óptimos
        optimos_data = {}
        for i in range(min(problem_size, 10)):
            key = f"[{i}]"
            # Valores de ejemplo
            if model_type == "Fibonacci":
                if i <= 1:
                    optimos_data[key] = i
                else:
                    optimos_data[key] = optimos_data.get(f"[{i-1}]", 0) + optimos_data.get(f"[{i-2}]", 0)
            else:
                optimos_data[key] = -1  # No calculado
        
        # Tabla de caminos
        caminos_data = {}
        for i in range(min(problem_size, 10)):
            key = f"[{i}]"
            caminos_data[key] = "N/A"
        
        # Vector SOA
        soa_data = []
        
        return {
            "optimos": {
                "name": "Tabla de Óptimos",
                "description": "Almacena los valores óptimos",
                "data": optimos_data,
                "dimensions": ["n"],
                "approach": approach,
                "initialization": "Inicializada con -1 (valores no calculados)"
            },
            "caminos": {
                "name": "Tabla de Caminos",
                "description": "Almacena las decisiones",
                "data": caminos_data,
                "dimensions": ["n"]
            },
            "soa": {
                "name": "Vector SOA",
                "description": "Subestructura Óptima",
                "data": soa_data
            }
        }

