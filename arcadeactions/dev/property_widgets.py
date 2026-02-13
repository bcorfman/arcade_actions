"""Parsing/evaluation helpers for property inspector widgets."""

from __future__ import annotations

import ast

_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}


class ExpressionEvaluator:
    """Safe arithmetic evaluator for inspector input expressions."""

    def __init__(self, names: dict[str, float]) -> None:
        self._names = names

    def evaluate(self, expression: str) -> object:
        tree = ast.parse(expression, mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.AST) -> object:
        if type(node) is ast.Constant:
            return node.value

        if type(node) is ast.Name:
            name_node = node
            return self._names[name_node.id]

        if type(node) is ast.Tuple:
            tuple_node = node
            return tuple(self._eval_node(element) for element in tuple_node.elts)

        if type(node) is ast.List:
            list_node = node
            return [self._eval_node(element) for element in list_node.elts]

        if type(node) is ast.UnaryOp:
            unary_node = node
            operator = _ALLOWED_UNARYOPS[type(unary_node.op)]
            return operator(self._eval_node(unary_node.operand))

        if type(node) is ast.BinOp:
            binop_node = node
            operator = _ALLOWED_BINOPS[type(binop_node.op)]
            return operator(self._eval_node(binop_node.left), self._eval_node(binop_node.right))

        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def parse_property_text(property_name: str, text: str, names: dict[str, float]) -> object:
    """Parse user-entered text into the right value type for a property."""
    stripped = text.strip()

    if property_name in ("is_collidable", "mirrored_x", "mirrored_y"):
        lowered = stripped.lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"Invalid boolean text: {text}")

    if property_name == "color":
        if stripped.startswith("#") and len(stripped) == 7:
            return (int(stripped[1:3], 16), int(stripped[3:5], 16), int(stripped[5:7], 16))

    value = ExpressionEvaluator(names).evaluate(stripped)

    if property_name in ("alpha", "opacity"):
        return int(value)

    return value
