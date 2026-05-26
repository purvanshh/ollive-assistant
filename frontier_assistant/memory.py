"""
Short-term conversational memory for the frontier assistant.
Mirrors the OSS assistant's message shape for apples-to-apples evaluation.
"""

from __future__ import annotations

from collections import deque


class ConversationMemory:
    """
    Rolling context window with a hard cap at the last 10 turns.

    We store two messages per turn in the common case, so the deque is sized
    to `max_turns * 2` to preserve up to 10 user/assistant exchanges.
    """

    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self._history: deque[dict[str, str]] = deque(maxlen=max_turns * 2)

    def add_turn(self, role: str, content: str) -> None:
        """
        Append a single message to the rolling history.

        Args:
            role: Either ``"user"`` or ``"assistant"``.
            content: The message text.
        """
        if role not in {"user", "assistant"}:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'.")
        self._history.append({"role": role, "content": content})

    def get_history(self) -> list[dict[str, str]]:
        """
        Return the current conversation history in chronological order.
        """
        return list(self._history)

    def clear(self) -> None:
        """Reset the conversation history."""
        self._history.clear()


# Compatibility alias so older imports keep working without touching Phase 1 code.
ChatMemory = ConversationMemory
