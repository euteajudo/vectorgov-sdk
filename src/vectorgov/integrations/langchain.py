"""
Integração do VectorGov SDK com LangChain.

Fornece:
- VectorGovRetriever: Retriever compatível com LangChain
- VectorGovTool: Ferramenta LangChain para agentes

Requisitos:
    pip install langchain langchain-core

Exemplo com RetrievalQA:
    >>> from langchain.chains import RetrievalQA
    >>> from langchain_openai import ChatOpenAI
    >>> from vectorgov.integrations.langchain import VectorGovRetriever
    >>>
    >>> retriever = VectorGovRetriever(api_key="vg_xxx")
    >>> qa = RetrievalQA.from_chain_type(
    ...     llm=ChatOpenAI(model="gpt-4o-mini"),
    ...     retriever=retriever,
    ... )
    >>> answer = qa.invoke("O que é ETP?")

Exemplo com LCEL:
    >>> from langchain_core.prompts import ChatPromptTemplate
    >>> from langchain_core.output_parsers import StrOutputParser
    >>> from langchain_openai import ChatOpenAI
    >>> from vectorgov.integrations.langchain import VectorGovRetriever
    >>>
    >>> retriever = VectorGovRetriever(api_key="vg_xxx")
    >>> prompt = ChatPromptTemplate.from_template(
    ...     "Contexto: {context}\\n\\nPergunta: {question}"
    ... )
    >>> llm = ChatOpenAI(model="gpt-4o-mini")
    >>>
    >>> chain = (
    ...     {"context": retriever, "question": lambda x: x}
    ...     | prompt
    ...     | llm
    ...     | StrOutputParser()
    ... )
    >>> answer = chain.invoke("O que é ETP?")
"""

import os
from typing import Any, List, Optional, Union

# Imports condicionais para LangChain
try:
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.tools import BaseTool
    from pydantic import Field, PrivateAttr

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseRetriever = object  # Fallback para type hints
    Document = dict
    BaseTool = object
    Field = lambda **kw: kw.get("default")  # noqa: E731
    PrivateAttr = lambda **kw: kw.get("default")  # noqa: E731
    CallbackManagerForRetrieverRun = object


def _check_langchain():
    """Verifica se LangChain está instalado."""
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain não está instalado. Instale com:\n"
            "pip install langchain langchain-core\n\n"
            "Ou instale o VectorGov com extras:\n"
            "pip install 'vectorgov[langchain]'"
        )


_VALID_METHODS = ("search", "hybrid", "merged", "grep")


def _hits_to_documents(hits: list, query_id: str = "") -> List["Document"]:
    """Converte lista de hits VectorGov para LangChain Documents."""
    documents = []
    for hit in hits:
        meta: dict[str, Any] = {"score": getattr(hit, "score", 0.0)}
        if hasattr(hit, "source"):
            meta["source"] = hit.source
        if hasattr(hit, "metadata") and hit.metadata:
            meta["document_type"] = hit.metadata.document_type
            meta["document_number"] = hit.metadata.document_number
            meta["year"] = hit.metadata.year
            meta["article"] = hit.metadata.article
            meta["paragraph"] = getattr(hit.metadata, "paragraph", None)
            meta["item"] = getattr(hit.metadata, "item", None)
        if hasattr(hit, "chunk_id"):
            meta["chunk_id"] = hit.chunk_id
        if hasattr(hit, "document_id"):
            meta["document_id"] = hit.document_id
        if hasattr(hit, "span_id"):
            meta["span_id"] = hit.span_id
        if hasattr(hit, "is_graph_expanded"):
            meta["is_graph_expanded"] = hit.is_graph_expanded
        # Campos de grep
        if hasattr(hit, "matched_line"):
            meta["matched_line"] = hit.matched_line
        if hasattr(hit, "line_number"):
            meta["line_number"] = hit.line_number
        # Campos de merged
        if hasattr(hit, "sources"):
            meta["sources"] = hit.sources
        if hasattr(hit, "breadcrumb"):
            meta["breadcrumb"] = hit.breadcrumb
        if query_id:
            meta["query_id"] = query_id
        text = getattr(hit, "text", "") or getattr(hit, "page_content", "")
        documents.append(Document(page_content=text, metadata=meta))
    return documents


class VectorGovRetriever(BaseRetriever):
    """Retriever LangChain para busca em legislação brasileira.

    Este retriever implementa a interface BaseRetriever do LangChain,
    permitindo uso direto em chains e agentes.

    Attributes:
        api_key: Chave de API do VectorGov
        method: Método de busca — "search", "hybrid", "merged", "grep"
        top_k: Quantidade de documentos a retornar (default: 5)
        mode: Modo de busca (fast, balanced, precise) — usado por search()
        filters: Filtros padrão para todas as buscas

    Exemplos:
        >>> # Busca semântica (padrão)
        >>> retriever = VectorGovRetriever(api_key="vg_xxx")
        >>> docs = retriever.invoke("O que é ETP?")
        >>>
        >>> # Busca híbrida (semântica + grafo)
        >>> retriever = VectorGovRetriever(api_key="vg_xxx", method="hybrid")
        >>> docs = retriever.invoke("critérios de julgamento")
        >>>
        >>> # Busca dual-path (semântica + filesystem)
        >>> retriever = VectorGovRetriever(api_key="vg_xxx", method="merged")
        >>>
        >>> # Busca textual exata
        >>> retriever = VectorGovRetriever(api_key="vg_xxx", method="grep")
    """

    api_key: Optional[str] = Field(default=None, description="VectorGov API key")
    method: str = Field(default="search", description="Método: search, hybrid, merged, grep")
    top_k: int = Field(default=5, description="Quantidade de documentos")
    mode: str = Field(default="balanced", description="Modo de busca (search only)")
    filters: Optional[dict] = Field(default=None, description="Filtros padrão")
    document_id: Optional[str] = Field(default=None, description="Filtro por documento")

    # Cliente privado (não serializado)
    _client: Any = PrivateAttr(default=None)

    def __init__(
        self,
        api_key: Optional[str] = None,
        method: str = "search",
        top_k: int = 5,
        mode: str = "balanced",
        filters: Optional[dict] = None,
        document_id: Optional[str] = None,
        **kwargs,
    ):
        """Inicializa o retriever.

        Args:
            api_key: Chave de API. Se não fornecida, usa VECTORGOV_API_KEY
            method: Método de busca — "search" (default), "hybrid", "merged", "grep"
            top_k: Quantidade de documentos (1-50)
            mode: Modo de busca (fast, balanced, precise) — usado por search()
            filters: Filtros padrão (tipo, ano, orgao)
            document_id: Filtro por documento (ex: "LEI-14133-2021")
        """
        _check_langchain()

        if method not in _VALID_METHODS:
            raise ValueError(f"method deve ser um de {_VALID_METHODS}, recebido: {method!r}")

        super().__init__(
            api_key=api_key or os.environ.get("VECTORGOV_API_KEY"),
            method=method,
            top_k=top_k,
            mode=mode,
            filters=filters,
            document_id=document_id,
            **kwargs,
        )

        from vectorgov import VectorGov

        self._client = VectorGov(
            api_key=self.api_key,
            default_top_k=self.top_k,
            default_mode=self.mode,
        )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        """Busca documentos relevantes usando o método configurado.

        Args:
            query: Texto da consulta
            run_manager: Gerenciador de callbacks (opcional)

        Returns:
            Lista de Documents do LangChain
        """
        if self.method == "hybrid":
            result = self._client.hybrid(query=query, top_k=self.top_k)
            hits = list(result.hits or []) + list(result.graph_nodes or [])
            return _hits_to_documents(hits)

        if self.method == "merged":
            result = self._client.merged(
                query=query, top_k=self.top_k, document_id=self.document_id,
            )
            return _hits_to_documents(result.results)

        if self.method == "grep":
            result = self._client.grep(
                query=query, max_results=self.top_k, document_id=self.document_id,
            )
            return _hits_to_documents(result.matches)

        # Default: search
        result = self._client.search(
            query=query, top_k=self.top_k, mode=self.mode, filters=self.filters,
        )
        return _hits_to_documents(result.hits, query_id=result.query_id)


class VectorGovTool(BaseTool):
    """Ferramenta LangChain para busca em legislação brasileira.

    Suporta múltiplos métodos: search, hybrid, merged, grep.

    Exemplo:
        >>> from vectorgov.integrations.langchain import VectorGovTool
        >>> tool = VectorGovTool(api_key="vg_xxx")
        >>> # Em um agente:
        >>> from langchain.agents import AgentExecutor, create_openai_tools_agent
        >>> agent = create_openai_tools_agent(llm, [tool], prompt)
    """

    name: str = "search_brazilian_legislation"
    description: str = """Busca informações em legislação brasileira (leis, decretos, instruções normativas).
Use quando precisar de informações sobre leis, regulamentos, licitações, contratos públicos, ETP, etc.
Input: pergunta ou termo de busca sobre legislação."""

    api_key: Optional[str] = Field(default=None)
    method: str = Field(default="search")
    top_k: int = Field(default=5)
    mode: str = Field(default="balanced")

    _client: Any = PrivateAttr(default=None)

    def __init__(
        self,
        api_key: Optional[str] = None,
        method: str = "search",
        top_k: int = 5,
        mode: str = "balanced",
        **kwargs,
    ):
        _check_langchain()

        if method not in _VALID_METHODS:
            raise ValueError(f"method deve ser um de {_VALID_METHODS}")

        super().__init__(
            api_key=api_key or os.environ.get("VECTORGOV_API_KEY"),
            method=method,
            top_k=top_k,
            mode=mode,
            **kwargs,
        )

        from vectorgov import VectorGov

        self._client = VectorGov(
            api_key=self.api_key,
            default_top_k=self.top_k,
            default_mode=self.mode,
        )

    def _run(self, query: str) -> str:
        """Executa a busca usando o método configurado."""
        if self.method == "hybrid":
            result = self._client.hybrid(query=query, top_k=self.top_k)
            hits = list(result.hits or []) + list(result.graph_nodes or [])
        elif self.method == "merged":
            result = self._client.merged(query=query, top_k=self.top_k)
            hits = result.results
        elif self.method == "grep":
            result = self._client.grep(query=query, max_results=self.top_k)
            hits = result.matches
        else:
            result = self._client.search(query=query)
            hits = result.hits

        if not hits:
            return "Nenhum resultado encontrado na legislação."

        parts = []
        for i, hit in enumerate(hits, 1):
            source = getattr(hit, "source", "") or getattr(hit, "document_id", "")
            text = getattr(hit, "text", "") or getattr(hit, "matched_line", "")
            parts.append(f"[{i}] {source}")
            parts.append(f"{text}")
            parts.append("")

        return "\n".join(parts)

    async def _arun(self, query: str) -> str:
        """Versão assíncrona (usa síncrona por ora)."""
        return self._run(query)


# Funções utilitárias para conversão


def to_langchain_documents(result: Any) -> List[Document]:
    """Converte qualquer resultado VectorGov para Documents LangChain.

    Suporta: SearchResult, HybridResult, MergedResult, GrepResult.

    Args:
        result: Resultado de qualquer método de busca VectorGov

    Returns:
        Lista de Documents compatíveis com LangChain

    Exemplo:
        >>> from vectorgov.integrations.langchain import to_langchain_documents
        >>>
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> docs = to_langchain_documents(vg.search("O que é ETP?"))
        >>> docs = to_langchain_documents(vg.hybrid("critérios"))
        >>> docs = to_langchain_documents(vg.merged("prazo"))
        >>> docs = to_langchain_documents(vg.grep("dispensa"))
    """
    _check_langchain()

    # HybridResult: hits + graph_nodes
    if hasattr(result, "graph_nodes"):
        hits = list(result.hits or []) + list(result.graph_nodes or [])
        return _hits_to_documents(hits)

    # MergedResult: results
    if hasattr(result, "results") and hasattr(result, "mutual_count"):
        return _hits_to_documents(result.results)

    # GrepResult: matches
    if hasattr(result, "matches"):
        return _hits_to_documents(result.matches)

    # SearchResult / SmartSearchResult: hits
    if hasattr(result, "hits"):
        query_id = getattr(result, "query_id", "")
        return _hits_to_documents(result.hits, query_id=query_id)

    return []
