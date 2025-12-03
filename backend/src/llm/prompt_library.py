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
    
    #metodo para simulacion "step by step"
    def build_simulation_system_instruction(self) -> str:
        """Define el comportamiento del LLM como motor de ejecución."""
        return (
            "Eres un Motor de Ejecución de Algoritmos (Runtime Engine).\n"
            "Tu objetivo es simular la ejecución paso a paso de un algoritmo recursivo.\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. NO expliques nada. NO uses lenguaje natural.\n"
            "2. Tu única salida debe ser un objeto JSON válido.\n"
            "3. El JSON debe representar el Árbol de Ejecución (Trace Tree).\n"
            "4. Usa la siguiente estructura exacta para el JSON:\n"
            "{\n"
            '  "algorithm_name": "Nombre detectado",\n'
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
            "Genera el JSON del árbol de ejecución ahora."
        )
