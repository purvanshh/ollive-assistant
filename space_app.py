"""
Hugging Face Spaces entry point for the OSS assistant.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

import oss_assistant.app as oss_app
from shared.observability import Observability

load_dotenv(REPO_ROOT / ".env")


def _wrap_space_inference() -> None:
    """Add a deployment-focused Langfuse trace wrapper when keys are present."""
    obs = Observability()
    if not obs.enabled or not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return

    original_generate = oss_app.MODEL.generate

    def wrapped_generate(prompt: str, history: list[dict[str, str]] | None = None) -> str:
        start_time = time.perf_counter()
        output = original_generate(prompt, history)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metadata = dict(getattr(oss_app.MODEL, "last_generation_info", {}))
        metadata.update(
            {
                "deployment": "huggingface-spaces",
                "model": getattr(oss_app.MODEL, "model_name", "unknown"),
                "response_time_ms": metadata.get("response_time_ms", latency_ms),
                "token_count": metadata.get("token_count", 0),
            }
        )
        obs.log(
            name="hf_space_oss_inference",
            input_data=prompt,
            output_data=output,
            metadata=metadata,
        )
        return output

    oss_app.MODEL.generate = wrapped_generate


_wrap_space_inference()
app = oss_app.build_app()

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
