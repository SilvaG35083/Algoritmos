"""Prompt templates for LLM assisted workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PromptBuilder:
    """Centralizes prompt templates and formatting."""

    project_name: str = "Analizador de Complejidades"

    def build_translation_prompt(self, description: str) -> str:
        return (
            f"Proyecto: {self.project_name}\n"
            "Tarea: Convertir la siguiente descripcion en pseudocodigo estructurado.\n"
            "Salida requerida: pseudocodigo que respeta la gramatica del proyecto.\n"
            "Comentarios permitidos: solo con el prefijo '► ' (no usar // ni #).\n"
            "REGLAS DE SINTAXIS (obligatorio):\n"
            "- Asignacion solo con '🡨' o ':=' (NO uses '⯺', '<-', '=')\n"
            "- Comparadores: '=', '<', '>', '<=', '>=', '<>' (no uses '==').\n"
            "- Llamadas a subrutinas: usa 'CALL Nombre(...)'.\n"
            "- Bloques con begin/end. if/for/while siempre con begin/end internos.\n"
            "- Booleanos: 't' o 'f'; null como 'null'.\n"
            "- No uses frases en asignaciones (ej. 'an empty list'); inicializa con valores simples o llama a una subrutina para construirlos.\n"
            f"Descripcion:\n{description}\n"
        )

    def build_review_prompt(self, pseudocode: str, estimation: str) -> str:
        return (
            f"Proyecto: {self.project_name}\n"
            "Tarea: Revisar el analisis de complejidad generado por el sistema.\n"
            "Entradas: pseudocodigo y resumen de complejidad propuesto.\n"
            "Indique si las cotas O, Omega y Theta son coherentes y aporte observaciones.\n"
            "Pseudocodigo:\n"
            f"{pseudocode}\n"
            "Estimacion actual:\n"
            f"{estimation}\n"
        )
    
    # Metodo para simulacion "step by step" y Analisis Matematico
    def build_simulation_system_instruction(self) -> str:
        """Define el comportamiento del LLM como motor de ejecución y analista matemático."""
        return (
            "Eres un Motor de Ejecución y Analista Matemático de Algoritmos Avanzado.\n"
            "Tu tarea es doble: 1) Simular la ejecución paso a paso y 2) Realizar un análisis teórico formal.\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. NO expliques nada en texto plano. Tu única salida debe ser un objeto JSON válido.\n"
            "2. El análisis de complejidad debe identificar la técnica matemática adecuada (Teorema Maestro, etc).\n"
            "3. Simula la ejecución completa para generar el árbol.\n"
            "4. Usa la siguiente estructura EXACTA para el JSON:\n"
            "{\n"
            '  "algorithm_type": "recursivo | iterativo | divide_y_venceras | programacion_dinamica | grafos | backtracking | voraz",\n'
            '  "algorithm_name": "Nombre detectado",\n'
            # --- SECCIÓN 1: ANÁLISIS MATEMÁTICO ---
            '  "theoretical_analysis": {\n'
            '     "recurrence_relation": "T(n) = aT(n/b) + f(n) (ej: T(n) = 2T(n/2) + n)",\n'
            '     "technique_used": "Teorema Maestro | Método del Árbol | Sustitución | Ecuación Característica | Conteo de Bucles",\n'
            '     "technique_explanation": "Breve justificación (ej: a=2, b=2, d=1. log_b(a) = d. Caso 2 del Teorema Maestro)",\n'
            '     "complexity": {\n'
            '        "best_case": "Ω(...)",\n'
            '        "average_case": "Θ(...)",\n'
            '        "worst_case": "O(...)"\n'
            '     },\n'
            '     "complexity_explanation": {\n'
            '        "best_case": "Explicación del mejor caso (cuando el algoritmo es más rápido)",\n'
            '        "average_case": "Explicación del caso promedio (comportamiento típico)",\n'
            '        "worst_case": "Explicación del peor caso (cuando el algoritmo es más lento)"\n'
            '     }\n'
            '  },\n'
            # --- SECCIÓN 2: ÁRBOL DE EJECUCIÓN (No borrar esto, es vital para el gráfico) ---
            '  "execution_tree": {\n'
            '    "id": "root",\n'
            '    "call": "fib(3)",\n'
            '    "result": "2",\n'
            '    "children": [\n'
            '       { "id": "child_1", "call": "fib(2)", "result": "1", "children": [...] }\n'
            '    ]\n'
            '  },\n'
            '  "total_steps": 5\n'
            "}"
        )

    def build_simulation_user_prompt(self, pseudocode: str, input_data: str) -> str:
        """Construye la petición con el código y la entrada específica."""
        return (
            f"Proyecto: {self.project_name} - Módulo de Simulación\n"
            f"Código a ejecutar:\n{pseudocode}\n\n"
            f"Entrada (Inputs): {input_data}\n\n"
            "Genera el JSON completo con el análisis matemático y el árbol de ejecución ahora."
        )
