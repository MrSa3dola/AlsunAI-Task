from typing import Annotated, Any, Dict, Sequence

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from typing_extensions import TypedDict

from tools.calculator import sympy_calculator
from translation import translate_text

load_dotenv()


class ChainState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def initialize_llm(
    model_name: str = "gpt-3.5-turbo", temperature: float = 0.0
) -> ChatOpenAI:
    """
    Create and return a ChatOpenAI instance.
    """
    return ChatOpenAI(model=model_name, temperature=temperature)


def bind_tools_to_llm(llm: ChatOpenAI, tools: list) -> Any:
    """
    Bind tools to the LLM with 'any' choice.
    """
    return llm.bind_tools(tools, tool_choice="any")


def call_chain(
    state: ChainState, config: RunnableConfig, llm_with_tools: Any
) -> Dict[str, Any]:
    """
    Invoke the LLM with tools and return response messages.
    """
    response = llm_with_tools.invoke(state["messages"], config)
    return {"messages": [response]}


def call_model(
    state: ChainState, config: RunnableConfig, llm: ChatOpenAI
) -> Dict[str, Any]:
    """
    Invoke the plain LLM and return response messages.
    """
    response = llm.invoke(state["messages"], config)
    return {"messages": [response]}


def build_chain(llm: ChatOpenAI, llm_with_tools: Any, tools: list) -> Any:
    """
    Construct and compile the StateGraph chain for tool usage.
    """
    graph_builder = StateGraph(ChainState)
    # Nodes
    graph_builder.add_node(
        "call_tool", lambda state, config: call_chain(state, config, llm_with_tools)
    )
    graph_builder.add_node("execute_tool", ToolNode(tools))
    graph_builder.add_node(
        "call_model", lambda state, config: call_model(state, config, llm)
    )

    # Flow
    graph_builder.set_entry_point("call_tool")
    graph_builder.add_edge("call_tool", "execute_tool")
    graph_builder.add_edge("execute_tool", "call_model")
    graph_builder.add_edge("call_model", END)

    return graph_builder.compile()


def get_agent_result(example_query: str) -> str:
    """
    Runs the chain on an English math query and returns the assistant's answer.
    """
    load_dotenv()
    llm = initialize_llm()
    tools = [sympy_calculator]
    llm_with_tools = bind_tools_to_llm(llm, tools)
    chain = build_chain(llm, llm_with_tools, tools)
    state = {"messages": [("user", example_query)]}
    result = chain.invoke(state)
    return result["messages"][-1].content


def is_math_related(text: str) -> bool:
    """
    Determine if a message is math-related using an LLM classifier.
    """
    llm = initialize_llm()
    messages = [
        SystemMessage(
            content="""
            Your role is to classify whether a message is math-related or not.
            Respond only with 'yes' if the message contains mathematical questions,
            calculations, equations, or any math-related content. Otherwise, respond
            with 'no'. Do not explain your reasoning.
        """
        ),
        HumanMessage(content=f"Is this message math-related? '{text}'"),
    ]
    response = llm.invoke(messages)
    answer = response.content.strip().lower()
    return "yes" in answer


def detect_language(text: str) -> str:
    """
    Detect the language of the input text using an LLM.
    Returns 'ar' for Arabic, 'en' for English, else defaults to 'en'.
    """
    llm = initialize_llm()
    messages = [
        SystemMessage(
            content="""
            Identify the language of the given text:
            If primarily Arabic, respond with 'ar'.
            If primarily English, respond with 'en'.
            Otherwise respond with 'unknown'.
            Do not explain your reasoning.
        """
        ),
        HumanMessage(content=f"What language is this text? '{text}'"),
    ]
    response = llm.invoke(messages)
    lang = response.content.strip().lower()
    if lang not in ["ar", "en"]:
        return "en"
    return lang


def handle_query(user_query: str) -> str:
    """
    Process the user query: detect language, math check, tool call or fallback response.
    """
    lang = detect_language(user_query)
    if lang == "ar":
        english_query = translate_text(user_query, target="en")
        if is_math_related(english_query):
            result_en = get_agent_result(english_query)
            print(result_en)
            return translate_text(result_en, target="ar")
        else:
            return "رحباً! أنا مساعد ذكاء اصطناعي متخصص في الرياضيات فقط. يسعدني مساعدتك في أي استفسار رياضي."
    else:
        if is_math_related(user_query):
            return get_agent_result(user_query)
        else:
            return "Hello! I'm here to assist with math-related questions only. Please let me know how I can help you with mathematics."
