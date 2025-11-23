"""Esquemas Pydantic para el API REST."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    source: str = Field(..., min_length=1, description="Pseudocodigo de entrada.")


class ComplexitySummary(BaseModel):
    best_case: str
    worst_case: str
    average_case: str


class AnalyzeResponse(BaseModel):
    summary: ComplexitySummary
    annotations: dict[str, str]


class SampleAlgorithmOut(BaseModel):
    name: str
    category: str
    description: str
    pseudocode: str
    expected_complexity: str


class HealthResponse(BaseModel):
    status: str
    version: str
    notes: Optional[str] = None


# LLM request/response schemas
class LLMChatRequest(BaseModel):
    """Peticion para el asistente LLM (texto en lenguaje natural)."""

    query: str = Field(..., min_length=3, description="Descripcion del algoritmo o peticion al asistente.")


class LLMAnalysisStep(BaseModel):
    title: str
    detail: str
    cost: Optional[str] = None
    recurrence: Optional[str] = None
    line: Optional[str] = None
    line_number: Optional[int] = None
    method_used: Optional[str] = None
    explanation: Optional[str] = None


class RecursionTreeLevel(BaseModel):
    level: int
    nodes: List[str]
    cost: str


class RecursionTree(BaseModel):
    description: str
    levels: List[RecursionTreeLevel]
    total_cost: str


class Equation(BaseModel):
    type: str
    equation: str
    explanation: str
    solution: Optional[str] = None


class ComplexityAnalysis(BaseModel):
    best_case: str
    worst_case: str
    average_case: str
    space_complexity: Optional[str] = None


class LLMChatResponse(BaseModel):
    pseudocode: str
    summary: str
    steps: List[LLMAnalysisStep]
    raw_text: Optional[str] = None
    method: Optional[str] = None
    equations: Optional[List[Equation]] = None
    recursion_tree: Optional[RecursionTree] = None
    complexity_analysis: Optional[ComplexityAnalysis] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    conversation_history: Optional[List[ChatMessage]] = None
    provider: Optional[str] = Field(None, description="Proveedor LLM: 'openai' o 'gemini'")
