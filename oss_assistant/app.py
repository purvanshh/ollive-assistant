"""Gradio application for the OSS assistant."""

from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from guardrails.filter import SafetyFilter
from oss_assistant.memory import ChatMemory
from oss_assistant.model import OSSAssistantModel
from oss_assistant.tools import maybe_use_tools

load_dotenv(REPO_ROOT / ".env")

MODEL = OSSAssistantModel()
FILTER = SafetyFilter(use_llama_guard=False)


def build_app() -> gr.ChatInterface:
    """Construct the OSS Gradio app."""

    def respond(message: str, history: list[list[str]]) -> str:
        """Generate a safe model response for the latest user message."""
        is_safe, reason = FILTER.check(message)
        if not is_safe:
            return f"🛡️ Request blocked by safety filter: {reason}"

        used_tool, tool_result = maybe_use_tools(message)
        if used_tool:
            return tool_result

        memory = ChatMemory()
        for user_message, assistant_message in history:
            memory.add_turn("user", user_message)
            if assistant_message:
                memory.add_turn("assistant", assistant_message)

        response = MODEL.generate(message, memory.get_history())
        return response

    return gr.ChatInterface(
        fn=respond,
        title="🫒 OSS Assistant (Qwen2.5-0.5B)",
        description=(
            "A lightweight open-source personal assistant with multi-turn memory, "
            "safety guardrails, and calculator tool support."
        ),
        examples=[
            "What are the side effects of ibuprofen?",
            "Calculate 145 * 32",
            "Who was the 23rd President of the United States?",
        ],
        theme="soft",
    )


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
