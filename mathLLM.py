import math
from typing import Annotated, Sequence

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from sympy import cos, diff, exp, integrate, log, sin
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
from typing_extensions import TypedDict

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


# Initialize LLM and bind tools
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
tools = [sympy_calculator]
llm_with_tools = llm.bind_tools(tools, tool_choice="any")


def classify_query(text: str, config: RunnableConfig) -> bool:
    prompt = [
        SystemMessage(
            content="You are a classifier that answers 'YES' if the user question is about math or calculations, otherwise 'NO'."
        ),
        HumanMessage(content=text),
    ]
    resp = llm.invoke(prompt, config)
    answer = str(resp.text).strip().lower()
    return answer.startswith("yes")


class ChainState(TypedDict):
    """LangGraph state."""

    messages: Annotated[Sequence[BaseMessage], add_messages]


def call_tool_or_model(state: ChainState, config: RunnableConfig):
    last = state["messages"][-1]
    if isinstance(last, HumanMessage) and classify_query(last.content, config):
        # Math-related: use calculator tool
        resp = llm_with_tools.invoke(state["messages"], config)
    else:
        # Non-math: direct model reply
        resp = HumanMessage(
            content="I'm sorry, but as a Math AI Assistant, I can only respond to mathematics-related questions. Please ask a math-related question, and I'll be happy to assist!"
        )
    return {"messages": [resp]}


# Build the graph
graph_builder = StateGraph(ChainState)
graph_builder.add_node("route", call_tool_or_model)
graph_builder.set_entry_point("route")
graph_builder.add_edge("route", END)

chain = graph_builder.compile()

# Example usage
example_query = [
    "What is the capital of France?",
    "what is the output for 2+3*4?",
    "can you calculate thsi sin(pi/4)+cos(pi/4)??",
    "bro solve this pleasediff(sin(x)*cos(x), x).",
    "what is the result of integrate(x**2 + 3*x, x)",
    "solve integrate(sin(x), x, 0, pi)",
]


for event in chain.stream(
    {"messages": [("user", example_query[0])]},
    stream_mode="values",
):
    event["messages"][-1].pretty_print()
