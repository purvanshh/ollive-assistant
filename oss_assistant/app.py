"""Gradio application for the OSS assistant."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

import gradio as gr
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from guardrails.filter import SafetyFilter
from oss_assistant.memory import ChatMemory
from oss_assistant.model import OSSAssistantModel

load_dotenv(REPO_ROOT / ".env")

MODEL = OSSAssistantModel()
FILTER = SafetyFilter()


def _rehydrate_memory(history: List[Tuple[str, str]]) -> ChatMemory:
    """Convert Gradio's transcript format into the shared memory format."""
    memory = ChatMemory()
    for user_message, assistant_message in history:
        memory.add_turn("user", user_message)
        if assistant_message:
            memory.add_turn("assistant", assistant_message)
    return memory


def respond(message: str, history: List[Tuple[str, str]]) -> str:
    """Generate a safe model response for the latest user message."""
    is_safe, reason = FILTER.check(message)
    if not is_safe:
        return f"Request blocked by safety filter. Reason: {reason}"

    memory = _rehydrate_memory(history)
    response = MODEL.generate(message, memory.get_history())
    memory.add_turn("user", message)
    memory.add_turn("assistant", response)
    return response


demo = gr.ChatInterface(
    fn=respond,
    title="OSS Personal Assistant",
    description="Qwen2.5-0.5B-Instruct with short-term memory and shared guardrails.",
    chatbot=gr.Chatbot(height=500),
    textbox=gr.Textbox(placeholder="Ask the assistant anything...", scale=7),
    type="tuples",
)


if __name__ == "__main__":
    demo.launch()
