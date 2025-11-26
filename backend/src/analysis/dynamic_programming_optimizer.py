"""Optimizador de Programación Dinámica para análisis de complejidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable


@dataclass(slots=True)
class MemoizationCache:
    """Cache para memoización en algoritmos top-down."""

    hits: int = 0
    misses: int = 0
    total_calls: int = 0
    cache: Dict[str, Any] = field(default_factory=dict)
    total_time: float = 0.0


@dataclass(slots=True)
class OptimizationResult:
    """Resultado de la optimización con programación dinámica."""

    improved_complexity: str
    method_used: str  # "top_down" o "bottom_up"
    cache_stats: Optional[MemoizationCache] = None
    space_complexity: str = ""
    explanation: str = ""


class DynamicProgrammingOptimizer:
    """Optimizador que analiza y optimiza algoritmos usando Programación Dinámica."""

    def __init__(self):
        self._cache = MemoizationCache()

    def optimize_top_down(
        self,
        func: Callable,
        initializer: Optional[Dict] = None,
        problem_size: int = 10
    ) -> OptimizationResult:
        """
        Optimiza un algoritmo recursivo usando memoización (top-down).
        
        Args:
            func: Función recursiva a optimizar
            initializer: Diccionario para inicializar la tabla de memoización
            problem_size: Tamaño del problema para análisis
            
        Returns:
            OptimizationResult con información de la optimización
        """
        if initializer is None:
            initializer = {}
        
        # Simulación de optimización
        # En un caso real, aquí se envolvería la función con memoización
        
        return OptimizationResult(
            improved_complexity="O(n)",
            method_used="top_down",
            cache_stats=self._cache,
            space_complexity="O(n)",
            explanation="Optimización top-down con memoización: se evitan recálculos almacenando resultados en una tabla."
        )

    def optimize_bottom_up(
        self,
        problem_size: int = 10,
        dimensions: List[str] = None
    ) -> OptimizationResult:
        """
        Optimiza un algoritmo usando tabulación (bottom-up).
        
        Args:
            problem_size: Tamaño del problema
            dimensions: Dimensiones de la tabla DP
            
        Returns:
            OptimizationResult con información de la optimización
        """
        if dimensions is None:
            dimensions = ["n"]
        
        # Calcular complejidad espacial
        if len(dimensions) == 1:
            space = "O(n)"
        elif len(dimensions) == 2:
            space = "O(n*m)"
        else:
            space = "O(n^k)"
        
        return OptimizationResult(
            improved_complexity="O(n)",
            method_used="bottom_up",
            space_complexity=space,
            explanation="Optimización bottom-up con tabulación: se llena la tabla de forma iterativa desde los casos base."
        )

    def analyze_improvement(
        self,
        original_complexity: str,
        optimized_complexity: str
    ) -> Dict[str, Any]:
        """
        Analiza la mejora obtenida con la optimización.
        
        Args:
            original_complexity: Complejidad original del algoritmo
            optimized_complexity: Complejidad después de la optimización
            
        Returns:
            Diccionario con métricas de mejora
        """
        return {
            "original": original_complexity,
            "optimized": optimized_complexity,
            "improvement_factor": "Variable según el problema",
            "trade_off": "Mayor uso de memoria para reducir tiempo de ejecución"
        }

    def clear_cache(self) -> None:
        """Limpia el cache de memoización."""
        self._cache = MemoizationCache()

