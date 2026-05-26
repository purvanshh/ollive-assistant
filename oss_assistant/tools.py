"""
Tool-use layer for the OSS assistant.

The 0.5B OSS model is not reliable enough for structured function calling, so
we detect calculator requests directly from the user prompt.
"""

from __future__ import annotations

import ast
import operator
import re

_CALCULATOR_PATTERNS = [
    r"(?:calculate|compute|evaluate|what is|what's)\s+([0-9\s\+\-\*\/%\(\)\.\,]+)",
    r"^[0-9\s\+\-\*\/%\(\)\.\,]{3,}$",
]

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def maybe_use_tools(prompt: str) -> tuple[bool, str]:
    """
    Detect calculator intent in a raw user message.
    """
    normalized = prompt.replace(",", "")
    for pattern in _CALCULATOR_PATTERNS:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if not match:
            continue

        expression = match.group(1).strip() if match.lastindex else match.group(0).strip()
        result = _safe_calculate(expression)
        if result is not None:
            return True, f"🔧 Tool result: {result}"

    return False, ""


def _safe_calculate(expression: str) -> str | None:
    """
    Evaluate a limited arithmetic expression without exposing Python eval.
    """
    try:
        node = ast.parse(expression, mode="eval")
        result = _evaluate_node(node.body)
    except Exception:
        return None
    return str(result)


def _evaluate_node(node: ast.AST) -> float:
    """Recursively evaluate an allowed arithmetic AST."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        operand = _evaluate_node(node.operand)
        return _UNARY_OPERATORS[type(node.op)](operand)
    raise ValueError("Unsupported expression.")


if __name__ == "__main__":
    for example in [
        "calculate 5 + 3",
        "what is 10 * 2",
        "compute (4 + 5) * 6",
        "who is the president",
    ]:
        print(example, "->", maybe_use_tools(example))
