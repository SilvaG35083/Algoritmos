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
