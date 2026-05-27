"""Transformers-backed inference wrapper for the OSS assistant."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import torch
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.observability import Observability

load_dotenv()


class OSSAssistantModel:
    """Thin wrapper around Qwen2.5-0.5B-Instruct for chat-style generation."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        max_new_tokens: int = 256,
        temperature: float = 0.7,
    ) -> None:
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.obs = Observability()
        self.last_generation_info: dict[str, float | int | str] = {}

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
        )
        self.model.to(self.device)
        self.model.eval()

    def generate(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate a response conditioned on the rolling conversation history."""
        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a concise, helpful personal assistant. "
                    "Be honest about uncertainty and avoid fabricating facts."
                ),
            }
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        rendered_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(rendered_prompt, return_tensors="pt").to(self.device)
        generation_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "pad_token_id": self.tokenizer.pad_token_id,
            "do_sample": self.temperature > 0,
        }
        if generation_kwargs["do_sample"]:
            generation_kwargs["temperature"] = self.temperature

        start_time = time.perf_counter()
        with torch.no_grad():
            output_ids = self.model.generate(**inputs, **generation_kwargs)
        latency = round(time.perf_counter() - start_time, 3)

        new_tokens = output_ids[0][inputs["input_ids"].shape[1] :]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        input_tokens = int(inputs["input_ids"].shape[1])
        output_tokens = int(new_tokens.shape[0])
        total_tokens = input_tokens + output_tokens
        response_time_ms = round(latency * 1000, 2)
        self.last_generation_info = {
            "model": self.model_name,
            "response_time_ms": response_time_ms,
            "latency_sec": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "token_count": total_tokens,
        }

        self.obs.log(
            name="oss_inference",
            input_data=prompt,
            output_data=response,
            metadata={
                "model": self.model_name,
                "latency_sec": latency,
                "response_time_ms": response_time_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "token_count": total_tokens,
                "temperature": self.temperature,
                "timestamp": time.time(),
            },
        )
        return response


# Compatibility alias for code that expects the Phase 2 naming.
OSSModel = OSSAssistantModel
