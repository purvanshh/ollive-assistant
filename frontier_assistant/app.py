"""
Gradio web interface for the frontier assistant.
Uses the same high-level ChatInterface pattern as the OSS assistant for fairness.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from frontier_assistant.memory import ConversationMemory
from frontier_assistant.model import FrontierModel
from guardrails.filter import SafetyFilter

load_dotenv(REPO_ROOT / ".env")


def build_app() -> gr.ChatInterface:
    """Construct the frontier Gradio app."""
    model = FrontierModel(
        model_name=os.getenv("FRONTIER_MODEL", "gpt-4.1"),
        max_tokens=512,
        temperature=0.7,
    )
    safety_filter = SafetyFilter()

    def respond(message: str, history: list[list[str]]) -> str:
        """
        Generate a response for the latest user message.

        Gradio provides the visible transcript as ``[[user, assistant], ...]``.
        Rehydrating memory on each request keeps the UI and model context aligned.
        """
        memory = ConversationMemory(max_turns=10)
        for human, assistant in history:
            memory.add_turn("user", human)
            if assistant:
                memory.add_turn("assistant", assistant)

        is_safe, reason = safety_filter.check(message)
        if not is_safe:
            return f"Request blocked by safety filter. Reason: {reason}"

        response = model.generate(message, memory.get_history())
        return response

    return gr.ChatInterface(
        fn=respond,
        title="🚀 Frontier Assistant (OpenAI GPT-4.1)",
        description=(
            "A personal assistant powered by OpenAI's frontier models. "
            "Supports multi-turn memory and basic assistant behavior."
        ),
        examples=[
            "What are the side effects of ibuprofen?",
            "Summarize the concept of AI liability insurance in one sentence.",
            "Who was the 23rd President of the United States?",
        ],
        theme="soft",
    )


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
