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


def _rehydrate_memory(history: list[object]) -> ConversationMemory:
    """
    Rebuild memory from either tuple-style or message-dict Gradio history.
    """
    memory = ConversationMemory(max_turns=10)

    for item in history:
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                memory.add_turn(role, content)
            continue

        if isinstance(item, (list, tuple)) and len(item) == 2:
            human, assistant = item
            if isinstance(human, str):
                memory.add_turn("user", human)
            if isinstance(assistant, str) and assistant:
                memory.add_turn("assistant", assistant)

    return memory


def build_app() -> gr.ChatInterface:
    """Construct the frontier Gradio app."""
    model = FrontierModel(
        model_name=os.getenv("FRONTIER_MODEL", "gpt-4.1"),
        max_tokens=512,
        temperature=0.7,
    )
    safety_filter = SafetyFilter(use_llama_guard=False)

    def respond(message: str, history: list[object]) -> str:
        """
        Generate a response for the latest user message.
        """
        is_safe, reason = safety_filter.check(message)
        if not is_safe:
            return f"🛡️ Request blocked by safety filter: {reason}"

        memory = _rehydrate_memory(history)
        response = model.generate(message, memory.get_history(), use_tools=True)
        return response

    return gr.ChatInterface(
        fn=respond,
        title="🚀 Frontier Assistant (OpenAI GPT-4.1)",
        description=(
            "A personal assistant powered by OpenAI's frontier models. "
            "Supports multi-turn memory, safety guardrails, and native calculator tool use."
        ),
        examples=[
            "What are the side effects of ibuprofen?",
            "Calculate 145 * 32",
            "Summarize the concept of AI liability insurance in one sentence.",
        ],
    )


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
