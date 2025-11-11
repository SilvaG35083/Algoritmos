"""Dependencias compartidas para el API."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from analyzer import AnalysisPipeline
from analyzer.samples import SampleAlgorithm, load_samples


@lru_cache(maxsize=1)
def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline()


@lru_cache(maxsize=1)
def get_samples() -> List[SampleAlgorithm]:
    return load_samples()
