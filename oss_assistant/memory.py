"""Short-term conversational memory for the OSS assistant."""

from __future__ import annotations

from typing import Dict, List


class ChatMemory:
    """Stores the last N conversation turns in a rolling window."""

    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self._turns: List[Dict[str, str]] = []

    def add_turn(self, role: str, content: str) -> None:
        """Add a conversation turn and keep only the most recent turns."""
        if role not in {"user", "assistant"}:
            raise ValueError("role must be either 'user' or 'assistant'")

        self._turns.append({"role": role, "content": content})
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns :]

    def get_history(self) -> List[Dict[str, str]]:
        """Return a shallow copy of the stored conversation history."""
        return list(self._turns)
