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
