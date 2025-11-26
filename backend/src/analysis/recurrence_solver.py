"""Utilities for recurrence relations."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Callable, Dict, List, Optional


@dataclass(slots=True)
class RecurrenceRelation:
    """Simple representation of a recurrence T(n) = sum(a_i * T(n/b_i)) + f(n)."""

    identifier: str
    recurrence: str
    base_case: str
    notes: str = ""


@dataclass(slots=True)
class RecurrenceSolution:
    """Stores the symbolic solution for a recurrence."""

    theta: str
    upper: str
    lower: str
    justification: str
    math_steps: List[Dict[str, str]] = field(default_factory=list)
    cases: Dict[str, str] = field(default_factory=dict)  # best, worst, average


class RecurrenceSolver:
    """Registry of solvers that can be composed."""

    def __init__(self) -> None:
        self._solvers: Dict[str, Callable[[RecurrenceRelation], Optional[RecurrenceSolution]]] = {}

    def register(self, name: str, handler: Callable[[RecurrenceRelation], Optional[RecurrenceSolution]]) -> None:
        self._solvers[name] = handler

    def solve(self, relation: RecurrenceRelation) -> Optional[RecurrenceSolution]:
        """Try each registered solver until one returns a result."""
        for handler in self._solvers.values():
            result = handler(relation)
            if result is not None:
                return result
        return None

    @classmethod
    def default(cls) -> "RecurrenceSolver":
        solver = cls()
        solver.register("master", solve_with_master_theorem)
        solver.register("substitution", solve_with_substitution)
        return solver


def solve_with_master_theorem(relation: RecurrenceRelation) -> Optional[RecurrenceSolution]:
    # 1. Parsing (Igual que antes)
    params = _parse_master_params(relation.recurrence)
    if not params: return None
    a, b, d = params
    
    # 2. Detectar si es QuickSort (T(n) = 2T(n/2) + n o similar)
    is_quicksort = (a == 2 and b == 2 and d == 1.0) or "quicksort" in relation.identifier.lower()
    
    # 3. Cálculos
    critical_exponent = math.log(a, b)
    epsilon = 1e-9
    
    # Preparamos los pasos para el Frontend
    steps = [
        {"label": "1. Identificar coeficientes", "value": f"a = {a}, b = {b}, f(n) ~ n^{d}"},
        {"label": "2. Calcular exponente crítico", "value": f"log_{b}({a}) ≈ {round(critical_exponent, 2)}"},
        {"label": "3. Comparar exponentes", "value": f"n^{d} (fuerza local) vs n^{round(critical_exponent, 2)} (fuerza recursiva)"}
    ]

    # 4. Evaluación de Casos - ESPECIAL PARA QUICKSORT
    if is_quicksort:
        steps.append({"label": "4. Algoritmo detectado", "value": "QuickSort - análisis de mejor/peor/promedio caso"})
        steps.append({"label": "5. Mejor caso", "value": "Partición balanceada: T(n) = 2T(n/2) + n → Θ(n log n)"})
        steps.append({"label": "6. Peor caso", "value": "Partición desbalanceada: T(n) = T(n-1) + n → Θ(n²)"})
        steps.append({"label": "7. Caso promedio", "value": "Análisis probabilístico: en promedio la partición es balanceada → Θ(n log n)"})
        
        return RecurrenceSolution(
            theta="Theta(n log n)",
            upper="O(n²)",
            lower="Omega(n log n)",
            justification="QuickSort: mejor/promedio Θ(n log n), peor O(n²) cuando la partición es desbalanceada.",
            math_steps=steps,
            cases={
                "best": "Ω(n log n)",
                "average": "Θ(n log n)",
                "worst": "O(n²)"
            }
        )

    # 5. Evaluación de Casos (Teorema Maestro estándar)
    
    # CASO 1
    if d < critical_exponent - epsilon:
        n_crit = f"n^{round(critical_exponent, 2)}" if critical_exponent % 1 else f"n^{int(critical_exponent)}"
        steps.append({"label": "4. Conclusión", "value": f"El costo de las hojas domina (Caso 1)."})
        
        result = RecurrenceSolution(
            theta=f"Theta({n_crit})",
            upper=f"O({n_crit})",
            lower=f"Omega({n_crit})",
            justification="Caso 1: f(n) es polinómicamente menor.",
            math_steps=steps,
            cases={
                "best": f"Ω({n_crit})",
                "average": f"Θ({n_crit})",
                "worst": f"O({n_crit})"
            }
        )
        return result

    # CASO 2
    elif abs(d - critical_exponent) < epsilon:
        n_crit = f"n^{int(d)}" if d % 1 == 0 else f"n^{d}"
        steps.append({"label": "4. Conclusión", "value": f"Equilibrio de fuerzas (Caso 2). Multiplicamos por log n."})
        
        result = RecurrenceSolution(
            theta=f"Theta({n_crit} log n)",
            upper=f"O({n_crit} log n)",
            lower=f"Omega({n_crit} log n)",
            justification="Caso 2: f(n) y n^log_b(a) crecen igual.",
            math_steps=steps,
            cases={
                "best": f"Ω({n_crit} log n)",
                "average": f"Θ({n_crit} log n)",
                "worst": f"O({n_crit} log n)"
            }
        )
        return result

    # CASO 3
    elif d > critical_exponent + epsilon:
        steps.append({"label": "4. Conclusión", "value": f"El costo de la raíz domina (Caso 3)."})
        
        # Check de regularidad simplificado
        if a < (b ** d):
            steps.append({"label": "5. Condición de regularidad", "value": f"Se cumple: {a} < {b}^{d}"})
            result = RecurrenceSolution(
                theta=f"Theta(n^{d})",
                upper=f"O(n^{d})",
                lower=f"Omega(n^{d})",
                justification="Caso 3: f(n) domina y es regular.",
                math_steps=steps,
                cases={
                    "best": f"Ω(n^{d})",
                    "average": f"Θ(n^{d})",
                    "worst": f"O(n^{d})"
                }
            )
            return result
    
    return None

def _parse_master_params(recurrence: str) -> Optional[tuple[float, float, float]]:
    """
    Analiza un string de recurrencia y extrae (a, b, d).
    
    Soporta formatos:
      - "T(n) = 2T(n/2) + n"
      - "T(n) = T(n/2) + 1"
      - "T(n) = 4*T(n/2) + n^2"
    
    Retorna:
      (a, b, d) donde:
        a: Coeficiente de llamadas recursivas (default 1)
        b: Divisor del tamaño del problema
        d: Grado del polinomio f(n) = n^d
    """
    
    # 1. Limpiar espacios en blanco para facilitar el regex
    # "T(n) = 2 T(n/2) + n" -> "T(n)=2T(n/2)+n"
    s = recurrence.replace(" ", "")
    
    # 2. Regex principal para separar las partes
    # Explicación del patrón:
    # T\(n\)=       -> Busca literalmente "T(n)="
    # (\d*\*?)?     -> Grupo 1 (a): Busca un número opcional seguido de un * opcional (ej: "2*" o "2" o nada)
    # T\(n/(\d+)\)  -> Grupo 2 (b): Busca "T(n/" seguido de un número y ")"
    # \+            -> Busca el signo "+"
    # (.*)          -> Grupo 3 (f(n)): Captura todo lo que sobra
    pattern = r"T\(n\)=(\d*\*?)?T\(n/(\d+)\)\+(.*)"
    
    match = re.search(pattern, s, re.IGNORECASE)
    
    if not match:
        return None # No coincide con el formato del Teorema Maestro
    
    a_str, b_str, fn_str = match.groups()
    
    # --- 3. Procesar 'a' (Multiplicador) ---
    if not a_str:
        a = 1.0 # Si no hay número antes de T, es 1 (ej: T(n) = T(n/2)...)
    else:
        # Quitamos el asterisco si existe ("2*" -> "2")
        a = float(a_str.replace("*", ""))
        
    # --- 4. Procesar 'b' (Divisor) ---
    b = float(b_str)
    if b <= 1:
        return None # El Teorema Maestro requiere b > 1 para reducir el problema
        
    # --- 5. Procesar 'd' (Grado de f(n)) ---
    # Analizamos la parte derecha (fn_str) buscando n^k, n, o constantes.
    
    # Caso: O(n^k) o n^k
    if "n^" in fn_str:
        # Buscamos el número después de n^
        d_match = re.search(r"n\^([\d\.]+)", fn_str)
        if d_match:
            d = float(d_match.group(1))
        else:
            d = 1.0 # Fallback raro
            
    # Caso: O(n) o n (Lineal)
    elif "n" in fn_str:
        d = 1.0
        
    # Caso: Constante (ej: "+ 1" o "+ O(1)")
    else:
        d = 0.0

    return a, b, d

def solve_with_substitution(relation: RecurrenceRelation) -> Optional[RecurrenceSolution]:
    """Placeholder substitution solver."""
    if relation.recurrence.endswith("+ n"):
        return RecurrenceSolution(
            theta="Theta(n)",
            upper="O(n)",
            lower="Omega(n)",
            justification="Linear recurrence solved by telescoping.",
            math_steps=[
                {"label": "1. Método", "value": "Sustitución iterativa"},
                {"label": "2. Resultado", "value": "T(n) = O(n)"},
            ],
            cases={
                "best": "Ω(n)",
                "average": "Θ(n)",
                "worst": "O(n)"
            }
        )
    return None
