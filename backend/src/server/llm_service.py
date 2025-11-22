"""Servicio de integración con LLM para generar pseudocódigo y análisis detallado."""

from __future__ import annotations

import json
import os
from typing import List

from llm.chat_service import LLMChatService
from server import models

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - dependencia opcional
    OpenAI = None  # type: ignore


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()


def llm_analyze(query: str, provider: str | None = None) -> models.LLMChatResponse:
    """Invoca el LLM o retorna una respuesta simulada si no hay API key."""
    provider = provider or DEFAULT_PROVIDER
    
    try:
        chat_service = LLMChatService(provider=provider)
        result = chat_service.generate_algorithm_with_analysis(query)
        
        # Convertir steps al formato esperado
        steps = [
            models.LLMAnalysisStep(
                title=step.get("title", "Paso"),
                detail=step.get("detail", ""),
                cost=step.get("cost"),
                recurrence=step.get("recurrence"),
                line=step.get("line_code") or step.get("line"),
            )
            for step in result.get("steps", [])
        ]
        
        # Construir summary mejorado
        summary_parts = [result.get("summary", "Análisis generado por LLM.")]
        if result.get("method"):
            summary_parts.append(f"Método: {result['method']}")
        if result.get("complexity_analysis"):
            comp = result["complexity_analysis"]
            summary_parts.append(
                f"Complejidad - Mejor: {comp.get('best_case', 'N/A')}, "
                f"Peor: {comp.get('worst_case', 'N/A')}, "
                f"Promedio: {comp.get('average_case', 'N/A')}"
            )
        
        summary = " | ".join(summary_parts)
        
        return models.LLMChatResponse(
            pseudocode=result.get("pseudocode", "").strip(),
            summary=summary,
            steps=steps,
            raw_text=json.dumps(result, indent=2),
        )
    except Exception as exc:  # pragma: no cover - errores de red/LLM
        return _stub_response(query, error=str(exc))


def _stub_response(query: str, error: str | None = None) -> models.LLMChatResponse:
    """Respuesta simulada cuando no hay API key o falla la llamada."""
    pseudocode = """begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + A[i]
    end
    return suma
end"""
    steps: List[models.LLMAnalysisStep] = [
        models.LLMAnalysisStep(
            title="Inicializacion",
            detail="Se prepara el acumulador.",
            cost="O(1)",
            line="suma 🡨 0",
        ),
        models.LLMAnalysisStep(
            title="Bucle principal",
            detail="Recorrido lineal del arreglo.",
            cost="O(n)",
            line="for i 🡨 1 to n do",
            recurrence=None,
        ),
        models.LLMAnalysisStep(
            title="Asignacion de retorno",
            detail="Se entrega la suma acumulada.",
            cost="O(1)",
            line="return suma",
        ),
    ]
    summary = "Complejidad estimada: O(n) en peor/promedio, Ω(n) en mejor caso."
    if error:
        summary += f" (Respuesta simulada por error: {error})"
    else:
        summary += " (Respuesta simulada - configura OPENAI_API_KEY o GEMINI_API_KEY)"
    return models.LLMChatResponse(pseudocode=pseudocode, summary=summary, steps=steps, raw_text=None)
