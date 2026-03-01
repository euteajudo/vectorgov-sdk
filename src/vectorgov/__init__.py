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

Com Function Calling:
    >>> tools = [vg.to_openai_tool()]
    >>> response = openai.chat.completions.create(
    ...     model="gpt-4o",
    ...     messages=[{"role": "user", "content": "O que é ETP?"}],
    ...     tools=tools,
    ... )
    >>> if response.choices[0].message.tool_calls:
    ...     result = vg.execute_tool_call(response.choices[0].message.tool_calls[0])

Com LangChain:
    >>> from vectorgov.integrations.langchain import VectorGovRetriever
    >>> retriever = VectorGovRetriever(api_key="vg_xxx")
    >>> docs = retriever.invoke("O que é ETP?")

Com MCP (Claude Desktop, Cursor, etc.):
    Execute `vectorgov-mcp` ou configure no claude_desktop_config.json:
    {
        "mcpServers": {
            "vectorgov": {
                "command": "uvx",
                "args": ["vectorgov-mcp"],
                "env": {"VECTORGOV_API_KEY": "vg_xxx"}
            }
        }
    }
"""

from vectorgov._async import AsyncVectorGov
from vectorgov.client import VectorGov
from vectorgov.config import SYSTEM_PROMPTS, SearchMode
from vectorgov.exceptions import (
    AuthError,
    ConnectionError,
    RateLimitError,
    ServerError,
    TierError,
    TimeoutError,
    ValidationError,
    VectorGovError,
)
from vectorgov.formatters import (
    create_rag_prompt,
    format_citations,
    to_langchain_docs,
    to_llamaindex_nodes,
)
from vectorgov.models import (
    # Audit Models
    AuditLog,
    AuditLogsResponse,
    AuditStats,
    BaseResult,
    DeleteResponse,
    DocumentsResponse,
    DocumentSummary,
    EnrichStatus,
    Hit,
    # Hybrid & Lookup Models
    HybridResult,
    IngestStatus,
    LookupCandidate,
    LookupMatch,
    LookupParent,
    LookupResolved,
    LookupResult,
    LookupSibling,
    Metadata,
    SearchResult,
    SmartSearchResult,
    StoreResponseResult,
    TokenStats,
    UploadResponse,
)

__version__ = "0.15.1"
__all__ = [
    # Clientes
    "VectorGov",
    "AsyncVectorGov",
    # Modelos
    "BaseResult",
    "SearchResult",
    "SmartSearchResult",
    "Hit",
    "Metadata",
    "TokenStats",
    # Document Models
    "DocumentSummary",
    "DocumentsResponse",
    "UploadResponse",
    "IngestStatus",
    "EnrichStatus",
    "DeleteResponse",
    "StoreResponseResult",
    # Audit Models
    "AuditLog",
    "AuditLogsResponse",
    "AuditStats",
    # Hybrid & Lookup Models
    "HybridResult",
    "LookupResult",
    "LookupMatch",
    "LookupParent",
    "LookupSibling",
    "LookupResolved",
    "LookupCandidate",
    # Configuração
    "SearchMode",
    "SYSTEM_PROMPTS",
    # Exceções
    "VectorGovError",
    "AuthError",
    "TierError",
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
