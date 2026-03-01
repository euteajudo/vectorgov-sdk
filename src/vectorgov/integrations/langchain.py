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


def _check_langchain():
    """Verifica se LangChain está instalado."""
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain não está instalado. Instale com:\n"
            "pip install langchain langchain-core\n\n"
            "Ou instale o VectorGov com extras:\n"
            "pip install 'vectorgov[langchain]'"
        )


class VectorGovRetriever(BaseRetriever):
    """Retriever LangChain para busca em legislação brasileira.

    Este retriever implementa a interface BaseRetriever do LangChain,
    permitindo uso direto em chains e agentes.

    Attributes:
        api_key: Chave de API do VectorGov
        top_k: Quantidade de documentos a retornar (default: 5)
        mode: Modo de busca (fast, balanced, precise)
        filters: Filtros padrão para todas as buscas

    Exemplo:
        >>> from vectorgov.integrations.langchain import VectorGovRetriever
        >>> retriever = VectorGovRetriever(api_key="vg_xxx", top_k=3)
        >>> docs = retriever.invoke("O que é ETP?")
        >>> for doc in docs:
        ...     print(doc.page_content[:100])
    """

    api_key: Optional[str] = Field(default=None, description="VectorGov API key")
    top_k: int = Field(default=5, description="Quantidade de documentos")
    mode: str = Field(default="balanced", description="Modo de busca")
    filters: Optional[dict] = Field(default=None, description="Filtros padrão")

    # Cliente privado (não serializado)
    _client: Any = PrivateAttr(default=None)

    def __init__(
        self,
        api_key: Optional[str] = None,
        top_k: int = 5,
        mode: str = "balanced",
        filters: Optional[dict] = None,
        **kwargs,
    ):
        """Inicializa o retriever.

        Args:
            api_key: Chave de API. Se não fornecida, usa VECTORGOV_API_KEY
            top_k: Quantidade de documentos (1-50)
            mode: Modo de busca (fast, balanced, precise)
            filters: Filtros padrão (tipo, ano, orgao)
        """
        _check_langchain()

        super().__init__(
            api_key=api_key or os.environ.get("VECTORGOV_API_KEY"),
            top_k=top_k,
            mode=mode,
            filters=filters,
            **kwargs,
        )

        # Inicializa cliente VectorGov
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
        """Busca documentos relevantes.

        Args:
            query: Texto da consulta
            run_manager: Gerenciador de callbacks (opcional)

        Returns:
            Lista de Documents do LangChain
        """
        # Executa busca
        result = self._client.search(
            query=query,
            top_k=self.top_k,
            mode=self.mode,
            filters=self.filters,
        )

        # Converte para Documents
        documents = []
        for hit in result.hits:
            doc = Document(
                page_content=hit.text,
                metadata={
                    "source": hit.source,
                    "score": hit.score,
                    "document_type": hit.metadata.document_type,
                    "document_number": hit.metadata.document_number,
                    "year": hit.metadata.year,
                    "article": hit.metadata.article,
                    "paragraph": hit.metadata.paragraph,
                    "item": hit.metadata.item,
                    "chunk_id": hit.chunk_id,
                    "query_id": result.query_id,
                },
            )
            documents.append(doc)

        return documents


class VectorGovTool(BaseTool):
    """Ferramenta LangChain para busca em legislação brasileira.

    Use esta ferramenta em agentes LangChain para permitir que o agente
    consulte legislação quando necessário.

    Exemplo:
        >>> from langchain.agents import AgentExecutor, create_openai_tools_agent
        >>> from langchain_openai import ChatOpenAI
        >>> from vectorgov.integrations.langchain import VectorGovTool
        >>>
        >>> tool = VectorGovTool(api_key="vg_xxx")
        >>> llm = ChatOpenAI(model="gpt-4o")
        >>> agent = create_openai_tools_agent(llm, [tool], prompt)
        >>> executor = AgentExecutor(agent=agent, tools=[tool])
    """

    name: str = "search_brazilian_legislation"
    description: str = """Busca informações em legislação brasileira (leis, decretos, instruções normativas).
Use quando precisar de informações sobre leis, regulamentos, licitações, contratos públicos, ETP, etc.
Input: pergunta ou termo de busca sobre legislação."""

    api_key: Optional[str] = Field(default=None)
    top_k: int = Field(default=5)
    mode: str = Field(default="balanced")

    _client: Any = PrivateAttr(default=None)

    def __init__(
        self,
        api_key: Optional[str] = None,
        top_k: int = 5,
        mode: str = "balanced",
        **kwargs,
    ):
        _check_langchain()

        super().__init__(
            api_key=api_key or os.environ.get("VECTORGOV_API_KEY"),
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
        """Executa a busca."""
        result = self._client.search(query=query)

        if not result.hits:
            return "Nenhum resultado encontrado na legislação."

        # Formata resposta
        parts = []
        for i, hit in enumerate(result.hits, 1):
            parts.append(f"[{i}] {hit.source}")
            parts.append(f"{hit.text}")
            parts.append("")

        return "\n".join(parts)

    async def _arun(self, query: str) -> str:
        """Versão assíncrona (usa síncrona por ora)."""
        return self._run(query)


# Funções utilitárias para conversão


def to_langchain_documents(search_result: "SearchResult") -> List[Document]:
    """Converte SearchResult para lista de Documents do LangChain.

    Args:
        search_result: Resultado de uma busca VectorGov

    Returns:
        Lista de Documents compatíveis com LangChain

    Exemplo:
        >>> from vectorgov import VectorGov
        >>> from vectorgov.integrations.langchain import to_langchain_documents
        >>>
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> result = vg.search("O que é ETP?")
        >>> docs = to_langchain_documents(result)
    """
    _check_langchain()

    documents = []
    for hit in search_result.hits:
        doc = Document(
            page_content=hit.text,
            metadata={
                "source": hit.source,
                "score": hit.score,
                "document_type": hit.metadata.document_type,
                "document_number": hit.metadata.document_number,
                "year": hit.metadata.year,
                "article": hit.metadata.article,
            },
        )
        documents.append(doc)

    return documents
