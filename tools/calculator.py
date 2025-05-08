import math

from dotenv import load_dotenv
from langchain_core.tools import tool
from sympy import cos, diff, exp, integrate, log, sin
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

load_dotenv()


@tool
def sympy_calculator(command: str) -> str:
    """
    A tool to evaluate or simplify Python-style math expressions,
    perform symbolic differentiation and integration, and handle
    basic arithmetic and common functions (sin, cos, exp, log, etc.).

    Supported usage examples:
      - "integrate(x**2 + 3*x, x)"
      - "integrate(sin(x), x, 0, pi)"
      - "diff(exp(x) * x, x)"
      - "2+3*4"
      - "sin(pi/4) + cos(pi/4)"
    """
    # Restrict parsing to mathematical syntax
    transformations = standard_transformations + (implicit_multiplication_application,)
    local_dict = {
        "pi": math.pi,
        "E": math.e,
        "sin": sin,
        "cos": cos,
        "exp": exp,
        "log": log,
    }
    try:
        expr = parse_expr(
            command, transformations=transformations, local_dict=local_dict
        )
    except (SympifyError, SyntaxError) as e:
        return f"❌ Could not parse expression: {e}"

    # Determine operation: diff or integrate
    func = expr.func.__name__.lower()
    args = expr.args
    if func == "diff" and len(args) >= 2:
        try:
            return str(diff(args[0], *args[1:]))
        except Exception as e:
            return f"❌ Differentiation error: {e}"
    if func == "integrate" and len(args) >= 2:
        try:
            return str(integrate(*args))
        except Exception as e:
            return f"❌ Integration error: {e}"

    # Basic arithmetic or simplify / evaluate
    if expr.free_symbols:
        try:
            return str(expr.simplify())
        except Exception:
            return str(expr)
    else:
        try:
            # Numeric result
            return str(expr.evalf())
        except Exception:
            return str(expr)


# print(sympy_calculator.invoke("5**2"))
