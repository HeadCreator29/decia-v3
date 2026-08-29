import ast
import operator


SAFE_OPERATORS = {
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


def _eval_node(node):

    if isinstance(node, ast.Constant):

        if isinstance(node.value, (int, float)):

            return node.value

        raise ValueError(
            f"Constante no soportada: {node.value}"
        )

    if isinstance(node, ast.BinOp):

        op = SAFE_OPERATORS.get(type(node.op))

        if op is None:

            raise ValueError(
                f"Operador no soportado: "
                f"{type(node.op).__name__}"
            )

        left = _eval_node(node.left)
        right = _eval_node(node.right)

        return op(left, right)

    if isinstance(node, ast.UnaryOp):

        op = SAFE_OPERATORS.get(type(node.op))

        if op is None:

            raise ValueError(
                f"Operador unario no soportado: "
                f"{type(node.op).__name__}"
            )

        operand = _eval_node(node.operand)

        return op(operand)

    raise ValueError(
        f"Expresión no soportada: "
        f"{type(node).__name__}"
    )


def safe_eval(expression):

    try:

        tree = ast.parse(
            expression, mode="eval"
        )

        result = _eval_node(tree.body)

        if isinstance(result, float):

            if result == int(result):

                return int(result)

        return result

    except (ValueError, SyntaxError, ZeroDivisionError):

        return None
