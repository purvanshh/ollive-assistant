"""Safety filter used to screen prompts before model generation."""

from __future__ import annotations

import os
from typing import Tuple

import requests
from dotenv import load_dotenv

load_dotenv()


class SafetyFilter:
    """Two-stage safety filter with keyword screening and Llama Guard."""

    LLAMA_GUARD_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-Guard-3-8B"

    def __init__(self) -> None:
        self.hf_token = os.getenv("HF_TOKEN")
        self.blocklist = {
            "build a bomb",
            "make a bomb",
            "bypass the law",
            "credit card fraud",
            "ddos",
            "disable security cameras",
            "exploit zero day",
            "how to kill",
            "human trafficking",
            "meth recipe",
            "racial cleansing",
            "self-harm instructions",
            "write malware",
        }

    def check(self, text: str) -> Tuple[bool, str]:
        """Return whether text is safe along with the decision reason."""
        lowered = text.lower()
        for keyword in self.blocklist:
            if keyword in lowered:
                return False, f"Blocked by keyword filter: '{keyword}'."

        if not self.hf_token:
            return False, "HF_TOKEN is required for the Llama Guard safety check."

        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": (
                "Task: Decide if the following user request is safe or unsafe.\n"
                f"User request: {text}\n"
                "Answer with SAFE or UNSAFE and a brief reason."
            )
        }

        try:
            response = requests.post(
                self.LLAMA_GUARD_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            # Fail closed so the application does not silently skip a safety gate.
            return False, f"Llama Guard request failed: {exc}"

        if isinstance(result, dict) and "error" in result:
            return False, f"Llama Guard error: {result['error']}"

        generated_text = self._extract_generated_text(result).lower()
        if not generated_text.strip():
            return False, "Llama Guard returned an empty classification."
        if "unsafe" in generated_text:
            return False, "Blocked by Llama Guard classification."

        return True, "Passed keyword and Llama Guard checks."

    @staticmethod
    def _extract_generated_text(result: object) -> str:
        """Normalize the common Hugging Face inference response formats."""
        if isinstance(result, list) and result:
            first_item = result[0]
            if isinstance(first_item, dict):
                return str(first_item.get("generated_text", ""))
            return str(first_item)
        if isinstance(result, dict):
            if "generated_text" in result:
                return str(result["generated_text"])
            if "error" in result:
                return str(result["error"])
        return str(result)
