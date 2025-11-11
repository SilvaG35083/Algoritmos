"""Abstract client for interacting with third party LLM providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


class LLMBackend(Protocol):
    """Protocol that concrete provider clients must satisfy."""

    def generate(self, prompt: str, **kwargs: Any) -> str: ...


@dataclass(slots=True)
class LLMResponse:
    """Normalized response returned by the high level client."""

    text: str
    tokens_used: int | None = None
    latency_ms: float | None = None
    metadata: Dict[str, Any] | None = None


class LLMClient:
    """Thin abstraction around a backend implementation."""

    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Produce a completion using the configured backend."""
        text = self._backend.generate(prompt, **kwargs)
        return LLMResponse(text=text, tokens_used=None, latency_ms=None, metadata=None)
