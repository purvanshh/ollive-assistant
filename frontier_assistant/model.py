"""Anthropic-backed inference wrapper for the frontier assistant."""

from __future__ import annotations

import os
from typing import Dict, List

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class FrontierAssistantModel:
    """Thin wrapper around an Anthropic Claude Sonnet model."""

    def __init__(
        self,
        model_name: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in the environment.")

        self.model_name = model_name or os.getenv(
            "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"
        )
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a response conditioned on the rolling conversation history."""
        messages = list(history)
        messages.append({"role": "user", "content": prompt})

        response = self.client.messages.create(
            model=self.model_name,
            system=(
                "You are a concise, helpful personal assistant. "
                "Be honest about uncertainty and avoid fabricating facts."
            ),
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
