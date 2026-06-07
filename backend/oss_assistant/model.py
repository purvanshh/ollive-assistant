"""Ollama-backed inference wrapper for the OSS assistant."""

from __future__ import annotations

import os
import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.shared.observability import Observability

def map_hf_to_ollama(model_name: str) -> str:
    """Maps Hugging Face style model name to local Ollama tag."""
    model_lower = model_name.lower()
    if "qwen2.5-0.5b" in model_lower:
        return "qwen2.5:0.5b"
    if "qwen2.5-7b" in model_lower:
        return "qwen2.5:7b"
    if "llama-3.2-3b" in model_lower or "llama-3.2" in model_lower:
        return "llama3.2"
    # Fallback clean up
    parts = model_name.split('/')
    name = parts[-1] if len(parts) > 1 else parts[0]
    name = name.lower().replace("-instruct", "").replace("-chat", "")
    return name

class OSSAssistantModel:
    """Client wrapper for Ollama generate endpoint."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
    ) -> None:
        self.raw_model_name = model_name or os.getenv("OSS_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
        self.model_name = map_hf_to_ollama(self.raw_model_name)
        self.temperature = temperature
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip('/')
        self.obs = Observability()
        self.last_generation_info: dict[str, float | int | str] = {}

    def generate(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate a response conditioned on conversation history."""
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

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }

        start_time = time.perf_counter()
        try:
            resp = httpx.post(f"{self.ollama_url}/api/chat", json=payload, timeout=10.0)
            latency = round(time.perf_counter() - start_time, 3)
            
            if resp.status_code != 200:
                raise httpx.HTTPStatusError(f"HTTP {resp.status_code}", request=resp.request, response=resp)
                
            data = resp.json()
            response = data.get("message", {}).get("content", "").strip()
            
            input_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)
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
            
        except Exception as e:
            # Fallback error messaging
            error_response = (
                "I'm sorry, the local open-source assistant is currently offline or unreachable. "
                f"Please ensure Ollama is running at {self.ollama_url}. (Error: {str(e)})"
            )
            latency = round(time.perf_counter() - start_time, 3)
            self.last_generation_info = {
                "model": self.model_name,
                "response_time_ms": round(latency * 1000, 2),
                "latency_sec": latency,
                "input_tokens": 0,
                "output_tokens": 0,
                "token_count": 0,
                "error": str(e)
            }
            return error_response

    def generate_stream(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Generator[str, None, None]:
        """Stream response chunks from Ollama."""
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

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature
            }
        }

        try:
            with httpx.stream("POST", f"{self.ollama_url}/api/chat", json=payload, timeout=10.0) as resp:
                if resp.status_code != 200:
                    yield f"[Error: Ollama returned status {resp.status_code}]"
                    return
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue
        except Exception as e:
            yield f"[Error connecting to Ollama: {str(e)}]"

# Compatibility aliases
OSSModel = OSSAssistantModel
