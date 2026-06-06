"""
Fail-silent observability wrapper using Langfuse.

If Langfuse keys are missing or the dependency is not installed, logging turns
into a no-op so local development and grading do not break.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class Observability:
    """
    Thin wrapper around Langfuse with fail-silent behavior.
    """

    def __init__(self) -> None:
        self._client = None
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

        if public_key and secret_key:
            try:
                from langfuse import Langfuse

                self._client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=base_url,
                )
            except Exception:
                self._client = None

    def log(
        self,
        name: str,
        input_data: Any,
        output_data: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a single inference trace if Langfuse is configured.
        """
        if self._client is None:
            return

        try:
            trace = self._client.trace(
                name=name,
                input=input_data,
                metadata=metadata or {},
            )
            trace.update(output=output_data)
        except Exception:
            # Observability must never take down inference paths.
            pass

    @property
    def enabled(self) -> bool:
        """Whether a real Langfuse client is available."""
        return self._client is not None


if __name__ == "__main__":
    obs = Observability()
    obs.log("test", "hello", "world", {"model": "test"})
    print("Observability initialized:", obs._client is not None)
