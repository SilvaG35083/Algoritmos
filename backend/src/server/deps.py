"""Dependencias compartidas para el API."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from analyzer import AnalysisPipeline
from analyzer.pipeline import PipelineConfig
from analyzer.samples import SampleAlgorithm, load_samples
from llm.grammar_corrector import GrammarCorrector


@lru_cache(maxsize=1)
def get_pipeline() -> AnalysisPipeline:
    """Crea y retorna el pipeline de análisis con corrección gramatical habilitada."""
    config = PipelineConfig(
        enable_grammar_correction=True,
        llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
    )
    grammar_corrector = None
    try:
        grammar_corrector = GrammarCorrector(provider=config.llm_provider)
    except (ImportError, ValueError):
        # Si no hay API key o el proveedor no está disponible, continuar sin corrección
        pass
    return AnalysisPipeline(config=config, grammar_corrector=grammar_corrector)


@lru_cache(maxsize=1)
def get_samples() -> List[SampleAlgorithm]:
    return load_samples()
