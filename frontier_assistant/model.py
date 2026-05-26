"""
Frontier model wrapper using the OpenAI API.
Implements the same generate() contract as the OSS model wrapper.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class FrontierModel:
    """
    Wrapper around OpenAI's chat completions API for the frontier assistant.
    """

    def __init__(
        self,
        model_name: str = "gpt-4.1",
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt or (
            "You are a helpful, harmless, and honest AI personal assistant. "
            "Answer concisely and accurately. If you do not know something, say so."
        )

    def generate(
        self,
        prompt: str,
        history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response for the latest user prompt.

        Args:
            prompt: The newest user message.
            history: Prior turns formatted as ``{"role": ..., "content": ...}``.

        Returns:
            The assistant's text response, or an inline error marker if the API
            call fails so the eval harness can keep running.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception as exc:  # noqa: BLE001 - keep the eval loop alive.
            return f"[ERROR: {exc}]"


# Compatibility alias so the existing scaffold can import the new implementation.
FrontierAssistantModel = FrontierModel


if __name__ == "__main__":
    model = FrontierModel(model_name="gpt-4o-mini")
    print(model.generate("What is 2 + 2?", []))
