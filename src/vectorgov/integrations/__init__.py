"""
Integrações do VectorGov SDK com frameworks de IA.

Este módulo fornece integrações prontas para usar com:
- OpenAI Function Calling
- Anthropic Claude Tools
- Google Gemini Function Calling
- LangChain

Exemplo com OpenAI:
    >>> from vectorgov import VectorGov
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> tool = vg.to_openai_tool()
    >>> # Use 'tool' no parâmetro tools do OpenAI

Exemplo com LangChain:
    >>> from vectorgov.integrations.langchain import VectorGovRetriever
    >>> retriever = VectorGovRetriever(api_key="vg_xxx")
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
