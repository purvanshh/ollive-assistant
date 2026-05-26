"""
Tool definitions and executors for the frontier assistant.
"""

from __future__ import annotations

import ast
import json
import operator
from typing import Any

CALCULATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate a basic mathematical expression safely. Use this when the "
            "user asks to calculate, compute, or evaluate a numeric expression."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression such as '2 + 2'.",
                }
            },
            "required": ["expression"],
        },
    },
}

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


def calculator(expression: str) -> str:
    """
    Safely evaluate a calculator expression.
    """
    try:
        node = ast.parse(expression.replace(",", ""), mode="eval")
        result = _evaluate_node(node.body)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


def execute_tool_call(tool_call: Any) -> dict[str, str]:
    """
    Execute one OpenAI tool call and return a tool message payload.
    """
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if function_name == "calculator":
        result = calculator(**arguments)
    else:
        result = f"Error: Tool '{function_name}' not found."

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result,
    }


def _evaluate_node(node: ast.AST) -> float:
    """Recursively evaluate an allowed arithmetic AST."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](
            _evaluate_node(node.left),
            _evaluate_node(node.right),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))
    raise ValueError("Unsupported operation in expression.")


if __name__ == "__main__":
    print(calculator("5 + 3"))
    print(calculator("(10 ** 2) / 4"))
