"""High level assistants built on top of LLMClient."""

from __future__ import annotations

from dataclasses import dataclass

from .client import LLMClient
from .prompt_library import PromptBuilder


@dataclass(slots=True)
class TranslationAssistant:
    """Translates natural language descriptions into structured pseudocode."""

    client: LLMClient
    prompts: PromptBuilder

    def translate(self, description: str) -> str:
        prompt = self.prompts.build_translation_prompt(description)
        response = self.client.complete(prompt)
        return response.text


@dataclass(slots=True)
class ReviewAssistant:
    """Uses an LLM to review complexity estimations."""

    client: LLMClient
    prompts: PromptBuilder

    def review(self, pseudocode: str, estimation: str) -> str:
        prompt = self.prompts.build_review_prompt(pseudocode, estimation)
        response = self.client.complete(prompt)
        return response.text
