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


WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for up-to-date information on a query. Use this "
            "when the user asks for current events, news, or factual details not "
            "known to the model."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web.",
                }
            },
            "required": ["query"],
        },
    },
}


def execute_tool_call(tool_call: Any) -> dict[str, str]:
    """
    Execute one OpenAI tool call and return a tool message payload.
    """
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if function_name == "calculator":
        result = calculator(**arguments)
    elif function_name == "web_search":
        try:
            from backend.app.tools.search import web_search
            search_results = web_search(**arguments)
            result = json.dumps(search_results)
        except Exception as e:
            result = f"Error executing search: {e}"
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
