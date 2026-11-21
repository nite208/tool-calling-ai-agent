import ast
import logging
import operator
from typing import Any

from src.exceptions import CalculatorError

logger = logging.getLogger(__name__)

_SAFE_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise CalculatorError(f"Unsupported literal type: {type(node.value).__name__}")
        return float(node.value)

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise CalculatorError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op_type is ast.Div and right == 0:
            raise CalculatorError("Division by zero.")
        if op_type is ast.FloorDiv and right == 0:
            raise CalculatorError("Division by zero.")
        if op_type is ast.Mod and right == 0:
            raise CalculatorError("Modulo by zero.")
        if op_type is ast.Pow and right > 10000:
            raise CalculatorError("Exponent too large (limit: 10000).")
        try:
            return _SAFE_OPS[op_type](left, right)
        except OverflowError as exc:
            raise CalculatorError(f"Result overflow: {exc}") from exc

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise CalculatorError(f"Unsupported unary operator: {op_type.__name__}")
        return _SAFE_OPS[op_type](_eval_node(node.operand))

    raise CalculatorError(f"Unsupported expression node: {type(node).__name__}")


def evaluate(expression: str) -> str:
    logger.info("Calculator evaluating expression=%r", expression)
    if not expression or not expression.strip():
        raise CalculatorError("Empty expression.")
    if len(expression) > 200:
        raise CalculatorError("Expression too long (limit: 200 characters).")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise CalculatorError(f"Syntax error: {exc}") from exc
    result = _eval_node(tree.body)
    logger.info("Calculator result=%s", result)
    if result == int(result):
        return str(int(result))
    return str(result)


SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate a safe arithmetic expression. "
            "Supports +, -, *, /, //, %, ** and parentheses. "
            "Use this for any numeric calculation the user asks for."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid arithmetic expression, e.g. '(3 + 5) * 2'.",
                }
            },
            "required": ["expression"],
        },
    },
}


def handle(arguments: dict[str, Any]) -> str:
    expression = arguments.get("expression", "")
    try:
        return evaluate(expression)
    except CalculatorError as exc:
        return f"error: {exc}"
