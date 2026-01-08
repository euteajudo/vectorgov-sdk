"""
VectorGov SDK - Acesse bases de conhecimento jurídico em Python.

Exemplo básico:
    >>> from vectorgov import VectorGov
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> results = vg.search("O que é ETP?")
    >>> print(results.to_context())

Com OpenAI:
    >>> from openai import OpenAI
    >>> openai = OpenAI()
    >>> response = openai.chat.completions.create(
    ...     model="gpt-4o",
    ...     messages=results.to_messages("O que é ETP?")
    ... )
"""

from vectorgov.client import VectorGov
from vectorgov.models import SearchResult, Hit, Metadata
from vectorgov.config import SearchMode, SYSTEM_PROMPTS
from vectorgov.exceptions import (
    VectorGovError,
    AuthError,
    RateLimitError,
    ValidationError,
    ServerError,
    ConnectionError,
    TimeoutError,
)
from vectorgov.formatters import (
    to_langchain_docs,
    to_llamaindex_nodes,
    format_citations,
    create_rag_prompt,
)

__version__ = "0.1.2"
__all__ = [
    # Cliente principal
    "VectorGov",
    # Modelos
    "SearchResult",
    "Hit",
    "Metadata",
    # Configuração
    "SearchMode",
    "SYSTEM_PROMPTS",
    # Exceções
    "VectorGovError",
    "AuthError",
    "RateLimitError",
    "ValidationError",
    "ServerError",
    "ConnectionError",
    "TimeoutError",
    # Formatters
    "to_langchain_docs",
    "to_llamaindex_nodes",
    "format_citations",
    "create_rag_prompt",
]
