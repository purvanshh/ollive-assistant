"""
Frontier model wrapper using the OpenAI API.
Implements the same generate() contract as the OSS model wrapper.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional, Generator

from dotenv import load_dotenv
from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from frontier_assistant.tools import CALCULATOR_SCHEMA, execute_tool_call
from shared.observability import Observability

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
        self.obs = Observability()
        self.last_generation_info: dict[str, float | int | str] = {}
        self.system_prompt = system_prompt or (
            "You are a helpful, harmless, and honest AI personal assistant. "
            "Answer concisely and accurately. If you do not know something, say so. "
            "Use the calculator tool for math questions."
        )

    def generate(
        self,
        prompt: str,
        history: Optional[list[dict[str, str]]] = None,
        use_tools: bool = True,
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
        tools = [CALCULATOR_SCHEMA] if use_tools else None

        try:
            start_time = time.perf_counter()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            message = response.choices[0].message
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0

            if message.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            tool_call.model_dump() for tool_call in message.tool_calls
                        ],
                    }
                )
                for tool_call in message.tool_calls:
                    messages.append(execute_tool_call(tool_call))

                follow_up = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                content = follow_up.choices[0].message.content or ""
                prompt_tokens += getattr(follow_up.usage, "prompt_tokens", 0) or 0
                completion_tokens += (
                    getattr(follow_up.usage, "completion_tokens", 0) or 0
                )
                used_tools = True
            else:
                content = message.content or ""
                used_tools = False

            final_text = content.strip()
            latency = round(time.perf_counter() - start_time, 3)
            total_tokens = prompt_tokens + completion_tokens
            response_time_ms = round(latency * 1000, 2)
            self.last_generation_info = {
                "model": self.model_name,
                "response_time_ms": response_time_ms,
                "latency_sec": latency,
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "token_count": total_tokens,
                "used_tools": used_tools,
            }
            self.obs.log(
                name="frontier_inference",
                input_data=prompt,
                output_data=final_text,
                metadata={
                    "model": self.model_name,
                    "latency_sec": latency,
                    "response_time_ms": response_time_ms,
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                    "token_count": total_tokens,
                    "temperature": self.temperature,
                    "timestamp": time.time(),
                    "used_tools": used_tools,
                },
            )
            return final_text
        except Exception as exc:  # noqa: BLE001 - keep the eval loop alive.
            return f"[ERROR: {exc}]"

    def generate_stream(
        self,
        prompt: str,
        history: Optional[list[dict[str, str]]] = None,
    ) -> Generator[str, None, None]:
        """Stream chunks from OpenAI chat completions API."""
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content
        except Exception as exc:
            yield f"[ERROR: {exc}]"


# Compatibility alias so the existing scaffold can import the new implementation.
FrontierAssistantModel = FrontierModel


if __name__ == "__main__":
    from typing import Generator
    model = FrontierModel(model_name="gpt-4o-mini")
    print(model.generate("What is 2 + 2?", []))
