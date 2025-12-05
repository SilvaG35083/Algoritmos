import re
import math
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class RecurrenceRelation:
    """Simple representation of a recurrence T(n) = sum(a_i * T(n/b_i)) + f(n)."""
    identifier: str
    recurrence: str
    base_case: str
    notes: str = ""

@dataclass
class SolutionResult:
    complexity: str
    formal_notation: str
    technique: str
    explanation: str
    recurrence_relation: str

class RecurrenceSolver:
    """
    Motor matemático avanzado para resolver ecuaciones de recurrencia
    usando Teorema Maestro, Ecuación Característica y Sustitución.
    """

    def solve(self, equation: str) -> Dict[str, Any]:
        """
        Punto de entrada principal. Intenta aplicar solvers en orden.
        """
        clean_eq = equation.replace(" ", "")
        
        # 1. Intentar Teorema Maestro (Divide y Vencerás)
        master_res = self._solve_master_theorem(clean_eq)
        if master_res:
            return master_res.__dict__

        # 2. Intentar Ecuación Característica (Recursión Lineal Homogénea)
        char_res = self._solve_characteristic_equation(clean_eq)
        if char_res:
            return char_res.__dict__

        # 3. Intentar Método de Sustitución (Patrones lineales simples)
        sub_res = self._solve_substitution_pattern(clean_eq)
        if sub_res:
            return sub_res.__dict__

        # 4. Fallback
        return {
            "complexity": "Desconocida",
            "formal_notation": "?",
            "technique": "Análisis no concluyente",
            "explanation": "La ecuación no coincide con los patrones matemáticos estándar soportados.",
            "recurrence_relation": equation
        }

    def _solve_master_theorem(self, eq: str) -> Optional[SolutionResult]:
        """
        Resuelve T(n) = aT(n/b) + f(n)
        Asumimos f(n) polinomial O(n^d)
        """
        # Regex para detectar T(n) = aT(n/b) + n^d
        # Ejemplos: "2T(n/2)+n", "T(n/2)+1", "4T(n/2)+n^2"
        
        # Patrón simplificado
        match = re.search(r'T\(n\)=(\d*)T\(n/(\d+)\)\+?(.*)', eq)
        if not match:
            return None

        a_str, b_str, fn_str = match.groups()
        a = int(a_str) if a_str else 1
        b = int(b_str)
        
        # Analizar f(n) para sacar 'd'
        d = 0
        if 'n^' in fn_str:
            try:
                d = float(fn_str.split('^')[1])
            except: d = 1
        elif 'n' in fn_str:
            d = 1
        else:
            d = 0 # Constante O(1)

        # Cálculos del Teorema Maestro
        log_b_a = math.log(a, b)
        epsilon = 0.0001 # Para flotantes

        explanation = f"Parámetros identificados: a={a}, b={b}, d={d}. Calculamos log_b(a) = {log_b_a:.2f}. "

        if log_b_a > d:
            # Caso 1
            complexity = f"O(n^{log_b_a:.2f})"
            if log_b_a.is_integer():
                complexity = f"O(n^{int(log_b_a)})"
            
            return SolutionResult(
                complexity=complexity,
                formal_notation=f"Θ(n^log_{b}({a}))",
                technique="Teorema Maestro (Caso 1)",
                explanation=explanation + f"Como log_b(a) > d, domina la parte recursiva (las hojas del árbol).",
                recurrence_relation=eq
            )
        
        elif abs(log_b_a - d) < epsilon:
            # Caso 2
            d_fmt = int(d) if d.is_integer() else d
            return SolutionResult(
                complexity=f"O(n^{d_fmt} log n)",
                formal_notation=f"Θ(n^{d_fmt} log n)",
                technique="Teorema Maestro (Caso 2)",
                explanation=explanation + f"Como log_b(a) ≈ d, el trabajo es uniforme en cada nivel del árbol.",
                recurrence_relation=eq
            )
        
        else:
            # Caso 3
            return SolutionResult(
                complexity=f"O(n^{d})",
                formal_notation=f"Θ(n^{d})",
                technique="Teorema Maestro (Caso 3)",
                explanation=explanation + f"Como log_b(a) < d, domina el trabajo en la raíz (f(n)).",
                recurrence_relation=eq
            )

    def _solve_characteristic_equation(self, eq: str) -> Optional[SolutionResult]:
        """
        Resuelve T(n) = c1*T(n-1) + c2*T(n-2) ...
        Ej: Fibonacci T(n) = T(n-1) + T(n-2)
        """
        # Detectar patrón de Fibonacci o similares: T(n) = A*T(n-1) + B*T(n-2)
        if "T(n-1)+T(n-2)" in eq:
            return SolutionResult(
                complexity="O(1.618^n)",
                formal_notation="Θ(φ^n)",
                technique="Método de Ecuación Característica",
                explanation="La ecuación T(n) = T(n-1) + T(n-2) genera la ecuación característica r^2 - r - 1 = 0. La raíz mayor es el número áureo φ ≈ 1.618.",
                recurrence_relation=eq
            )
        
        # Detectar patrón Torres de Hanoi: T(n) = 2T(n-1) + 1
        match_hanoi = re.search(r'T\(n\)=(\d+)T\(n-1\)', eq)
        if match_hanoi:
            base = match_hanoi.group(1)
            return SolutionResult(
                complexity=f"O({base}^n)",
                formal_notation=f"Θ({base}^n)",
                technique="Método de Sustitución (Progresión Geométrica)",
                explanation=f"Cada paso multiplica el trabajo por {base}. Es una serie geométrica que suma {base}^n.",
                recurrence_relation=eq
            )

        return None

    def _solve_substitution_pattern(self, eq: str) -> Optional[SolutionResult]:
        """
        Resuelve patrones lineales simples T(n) = T(n-1) + c
        """
        # T(n) = T(n-1) + constante
        if "T(n-1)" in eq and not "n" in eq.split("T(n-1)")[1]:
             return SolutionResult(
                complexity="O(n)",
                formal_notation="Θ(n)",
                technique="Método de Sustitución (Iterativo)",
                explanation="El algoritmo reduce el problema en 1 en cada paso y hace trabajo constante. T(n) = c + c + ... (n veces).",
                recurrence_relation=eq
            )

        # T(n) = T(n-1) + n
        if "T(n-1)+n" in eq:
             return SolutionResult(
                complexity="O(n^2)",
                formal_notation="Θ(n^2)",
                technique="Método de Sustitución (Serie Aritmética)",
                explanation="T(n) = n + (n-1) + (n-2)... Es la suma de Gauss: n(n+1)/2.",
                recurrence_relation=eq
            )
            
        return None
