"""
Integrações do VectorGov SDK com frameworks de IA.

Este módulo fornece integrações prontas para usar com:
- OpenAI Function Calling
- Anthropic Claude Tools
- Google Gemini Function Calling
- LangChain
- LangGraph
- Google ADK (Agent Development Kit)
- HuggingFace Transformers (modelos locais)

Exemplo com OpenAI:
    >>> from vectorgov import VectorGov
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> tool = vg.to_openai_tool()

Exemplo com LangChain:
    >>> from vectorgov.integrations.langchain import VectorGovRetriever
    >>> retriever = VectorGovRetriever(api_key="vg_xxx")

Exemplo com LangGraph:
    >>> from vectorgov.integrations.langgraph import create_vectorgov_tool
    >>> from langgraph.prebuilt import create_react_agent
    >>> tool = create_vectorgov_tool(api_key="vg_xxx")
    >>> agent = create_react_agent(llm, tools=[tool])

Exemplo com Google ADK:
    >>> from vectorgov.integrations.google_adk import create_search_tool
    >>> from google.adk.agents import Agent
    >>> tool = create_search_tool(api_key="vg_xxx")
    >>> agent = Agent(model="gemini-2.0-flash", tools=[tool])

Exemplo com Transformers (modelos locais):
    >>> from vectorgov import VectorGov
    >>> from vectorgov.integrations.transformers import create_rag_pipeline
    >>> from transformers import pipeline
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> llm = pipeline("text-generation", model="Qwen/Qwen2.5-3B-Instruct")
    >>> rag = create_rag_pipeline(vg, llm)
    >>> response = rag("O que é ETP?")
"""

from vectorgov.integrations.tools import (
    TOOL_SCHEMA,
    TOOL_NAME,
    TOOL_DESCRIPTION,
    to_openai_tool,
    to_anthropic_tool,
    to_google_tool,
    parse_tool_arguments,
)

__all__ = [
    "TOOL_SCHEMA",
    "TOOL_NAME",
    "TOOL_DESCRIPTION",
    "to_openai_tool",
    "to_anthropic_tool",
    "to_google_tool",
    "parse_tool_arguments",
]
