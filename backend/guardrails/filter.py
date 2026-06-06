"""
Safety guardrails wrapping model calls.
Two-pass filter: fast keyword blocklist, then optional remote Llama Guard.
"""

from __future__ import annotations

import os
import re
from typing import Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

_BLOCKLIST = [
    "kill yourself",
    "suicide method",
    "how to make a bomb",
    "how to build a bomb",
    "manufacture explosives",
    "child porn",
    "cp ",
    "hack into",
    "steal password",
    "credit card number",
    "social security number",
]

_BLOCK_PATTERNS = [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in _BLOCKLIST]
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/LlamaGuard-7b-hf"


class SafetyFilter:
    """
    Two-pass safety filter.
    """

    def __init__(self, use_llama_guard: bool = False) -> None:
        """
        Args:
            use_llama_guard: Whether to invoke Llama Guard after the keyword pass.
        """
        self.use_llama_guard = use_llama_guard
        self.hf_token = os.getenv("HF_TOKEN")

    def _keyword_check(self, text: str) -> Tuple[bool, str]:
        """Screen text against a regex blocklist for obviously unsafe content."""
        for pattern in _BLOCK_PATTERNS:
            if pattern.search(text):
                return False, f"Keyword blocklist hit: '{pattern.pattern}'"
        return True, "Keyword check passed."

    def _llama_guard_check(self, text: str) -> Tuple[bool, str]:
        """Run an optional remote Llama Guard classification via Hugging Face."""
        if not self.hf_token:
            return True, "Llama Guard skipped: HF_TOKEN missing."

        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": text}

        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            if isinstance(result, list) and result:
                first = result[0]
                if isinstance(first, dict):
                    label = str(first.get("generated_text", "")).strip().lower()
                else:
                    label = str(first).strip().lower()

                if label.startswith("safe"):
                    return True, "Llama Guard: safe."
                return False, f"Llama Guard: {label}"

            return True, "Llama Guard: unexpected response format, assumed safe."
        except Exception as exc:  # noqa: BLE001 - explicit fail-open behavior.
            return True, f"Llama Guard API error (fail-open): {exc}"

    def check(self, text: str) -> Tuple[bool, str]:
        """
        Run both safety passes and return a boolean decision with explanation.
        """
        safe, reason = self._keyword_check(text)
        if not safe:
            return safe, reason

        if self.use_llama_guard:
            return self._llama_guard_check(text)

        return True, "All safety checks passed."
