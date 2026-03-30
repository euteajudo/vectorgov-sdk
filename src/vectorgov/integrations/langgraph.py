"""
Integração do VectorGov SDK com LangGraph.

Fornece componentes para construir grafos de estado com busca em legislação brasileira:
- create_vectorgov_tool: Cria ferramenta configurada para uso em grafos
- create_retrieval_node: Cria nó de busca para grafos LangGraph
- VectorGovState: Estado base com contexto de legislação

Requisitos:
    pip install langgraph langchain-core

Exemplo básico com ReAct Agent:
    >>> from langgraph.prebuilt import create_react_agent
    >>> from langchain_openai import ChatOpenAI
    >>> from vectorgov.integrations.langgraph import create_vectorgov_tool
    >>>
    >>> tool = create_vectorgov_tool(api_key="vg_xxx")
    >>> llm = ChatOpenAI(model="gpt-4o")
    >>> agent = create_react_agent(llm, tools=[tool])
    >>> result = agent.invoke({"messages": [("user", "O que é ETP?")]})

Exemplo com grafo customizado:
    >>> from langgraph.graph import StateGraph, START, END
    >>> from vectorgov.integrations.langgraph import (
    ...     create_retrieval_node,
    ...     VectorGovState,
    ... )
    >>>
    >>> def process_query(state: VectorGovState) -> VectorGovState:
    ...     # Processa a query do usuário
    ...     return {"query": state["messages"][-1].content}
    >>>
    >>> retrieval_node = create_retrieval_node(api_key="vg_xxx")
    >>>
    >>> builder = StateGraph(VectorGovState)
    >>> builder.add_node("process", process_query)
    >>> builder.add_node("retrieve", retrieval_node)
    >>> builder.add_edge(START, "process")
    >>> builder.add_edge("process", "retrieve")
    >>> builder.add_edge("retrieve", END)
    >>> graph = builder.compile()
"""

import operator
import os
from typing import Annotated, Any, Callable, List, Optional, Sequence, TypedDict

# Imports condicionais para LangGraph
try:
    from langchain_core.documents import Document
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
    from langchain_core.tools import BaseTool, tool
    from pydantic import Field, PrivateAttr

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    BaseTool = object
    Document = dict
    BaseMessage = object
    HumanMessage = object
    AIMessage = object
    tool = lambda *a, **kw: (lambda f: f)  # noqa: E731
    Field = lambda **kw: kw.get("default")  # noqa: E731
    PrivateAttr = lambda **kw: kw.get("default")  # noqa: E731


def _check_langgraph():
    """Verifica se LangGraph está instalado."""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph/LangChain não está instalado. Instale com:\n"
            "pip install langgraph langchain-core\n\n"
            "Ou instale o VectorGov com extras:\n"
            "pip install 'vectorgov[langgraph]'"
        )


# ============================================================================
# Estado para grafos LangGraph
# ============================================================================


class VectorGovState(TypedDict, total=False):
    """Estado base para grafos com busca em legislação.

    Campos:
        messages: Lista de mensagens da conversa
        query: Query atual para busca
        documents: Documentos recuperados
        context: Contexto formatado para LLM
        sources: Fontes citadas

    Exemplo:
        >>> from langgraph.graph import StateGraph
        >>> from vectorgov.integrations.langgraph import VectorGovState
        >>>
        >>> builder = StateGraph(VectorGovState)
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    documents: List[Document]
    context: str
    sources: List[str]


# ============================================================================
# Ferramenta para uso em grafos
# ============================================================================


_VALID_METHODS = ("search", "hybrid", "merged", "grep")


def _execute_method(client: Any, method: str, query: str, top_k: int) -> str:
    """Executa o método de busca e formata resultado como string."""
    if method == "hybrid":
        result = client.hybrid(query=query, top_k=top_k)
        hits = list(result.hits or []) + list(result.graph_nodes or [])
    elif method == "merged":
        result = client.merged(query=query, top_k=top_k)
        hits = result.results
    elif method == "grep":
        result = client.grep(query=query, max_results=top_k)
        hits = result.matches
    else:
        result = client.search(query=query)
        hits = result.hits

    if not hits:
        return "Nenhum resultado encontrado na legislação brasileira."

    total = getattr(result, "total", len(hits))
    parts = [f"Encontrados {total} resultados:\n"]
    for i, hit in enumerate(hits, 1):
        source = getattr(hit, "source", "") or getattr(hit, "document_id", "")
        text = getattr(hit, "text", "") or getattr(hit, "matched_line", "")
        parts.append(f"[{i}] {source}")
        parts.append(f"{text}")
        parts.append("")

    return "\n".join(parts)


def create_vectorgov_tool(
    api_key: Optional[str] = None,
    method: str = "search",
    top_k: int = 5,
    mode: str = "balanced",
    name: str = "search_legislation",
    description: Optional[str] = None,
) -> BaseTool:
    """Cria uma ferramenta VectorGov para uso em grafos LangGraph.

    Suporta múltiplos métodos: search, hybrid, merged, grep.

    Args:
        api_key: Chave de API. Se não fornecida, usa VECTORGOV_API_KEY
        method: Método de busca — "search" (default), "hybrid", "merged", "grep"
        top_k: Quantidade de resultados (1-50)
        mode: Modo de busca (fast, balanced, precise) — usado por search()
        name: Nome da ferramenta
        description: Descrição customizada

    Returns:
        Ferramenta LangChain configurada

    Exemplo com ReAct:
        >>> from langgraph.prebuilt import create_react_agent
        >>> from langchain_openai import ChatOpenAI
        >>>
        >>> tool = create_vectorgov_tool(api_key="vg_xxx", method="hybrid")
        >>> agent = create_react_agent(ChatOpenAI(), tools=[tool])
        >>> result = agent.invoke({"messages": [("user", "O que é ETP?")]})
    """
    _check_langgraph()

    if method not in _VALID_METHODS:
        raise ValueError(f"method deve ser um de {_VALID_METHODS}")

    from vectorgov import VectorGov

    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    client = VectorGov(api_key=api_key, default_top_k=top_k, default_mode=mode)

    default_description = """Busca informações em legislação brasileira.

Use para consultar:
- Leis federais (Lei 14.133/2021, etc.)
- Decretos
- Instruções Normativas (INs)
- Informações sobre licitações, contratos, ETP, etc.

Input: pergunta ou termo de busca sobre legislação brasileira."""

    @tool(name, description=description or default_description)
    def search_legislation(query: str) -> str:
        """Busca em legislação brasileira."""
        return _execute_method(client, method, query, top_k)

    return search_legislation


# ============================================================================
# Nó de retrieval para grafos customizados
# ============================================================================


def create_retrieval_node(
    api_key: Optional[str] = None,
    method: str = "search",
    top_k: int = 5,
    mode: str = "balanced",
    query_key: str = "query",
    output_key: str = "documents",
    context_key: str = "context",
) -> Callable[[VectorGovState], dict]:
    """Cria um nó de retrieval para grafos LangGraph customizados.

    Suporta múltiplos métodos: search, hybrid, merged, grep.

    Args:
        api_key: Chave de API
        method: Método de busca — "search" (default), "hybrid", "merged", "grep"
        top_k: Quantidade de documentos
        mode: Modo de busca (search only)
        query_key: Chave do estado com a query
        output_key: Chave para salvar documentos
        context_key: Chave para salvar contexto formatado

    Returns:
        Função nó para usar em StateGraph

    Exemplo:
        >>> retrieval_node = create_retrieval_node(api_key="vg_xxx", method="hybrid")
        >>> builder = StateGraph(VectorGovState)
        >>> builder.add_node("retrieve", retrieval_node)
    """
    _check_langgraph()

    if method not in _VALID_METHODS:
        raise ValueError(f"method deve ser um de {_VALID_METHODS}")

    from vectorgov import VectorGov
    from vectorgov.integrations.langchain import _hits_to_documents

    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    client = VectorGov(api_key=api_key, default_top_k=top_k, default_mode=mode)

    def retrieval_node(state: dict) -> dict:
        """Nó de retrieval que busca documentos relevantes."""
        query = state.get(query_key, "")

        if not query:
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                query = (
                    last_msg.content
                    if hasattr(last_msg, "content")
                    else str(last_msg)
                )

        if not query:
            return {
                output_key: [],
                context_key: "Nenhuma query fornecida.",
                "sources": [],
            }

        # Busca usando o método configurado
        if method == "hybrid":
            result = client.hybrid(query=query, top_k=top_k)
            hits = list(result.hits or []) + list(result.graph_nodes or [])
            context = result.to_context() if hasattr(result, "to_context") else ""
        elif method == "merged":
            result = client.merged(query=query, top_k=top_k)
            hits = result.results
            context = "\n\n".join(getattr(h, "text", "") for h in hits)
        elif method == "grep":
            result = client.grep(query=query, max_results=top_k)
            hits = result.matches
            context = "\n\n".join(getattr(h, "text", "") for h in hits)
        else:
            result = client.search(query=query)
            hits = result.hits
            context = result.to_context()

        documents = _hits_to_documents(hits)
        sources = [
            getattr(h, "source", "") or getattr(h, "document_id", "")
            for h in hits
        ]

        return {
            output_key: documents,
            context_key: context,
            "sources": sources,
        }

    return retrieval_node


# ============================================================================
# Helpers para construção de grafos
# ============================================================================


def create_legal_rag_graph(
    llm: Any,
    api_key: Optional[str] = None,
    method: str = "search",
    top_k: int = 5,
    mode: str = "balanced",
    system_prompt: Optional[str] = None,
) -> Any:
    """Cria um grafo RAG completo para perguntas sobre legislação.

    Este helper cria um grafo pré-configurado com:
    1. Nó de retrieval (busca em VectorGov)
    2. Nó de geração (resposta com LLM)

    Args:
        llm: Modelo de linguagem (ChatOpenAI, ChatAnthropic, etc.)
        api_key: Chave de API VectorGov
        top_k: Quantidade de documentos
        mode: Modo de busca
        system_prompt: Prompt de sistema customizado

    Returns:
        Grafo LangGraph compilado

    Exemplo:
        >>> from langchain_openai import ChatOpenAI
        >>> from vectorgov.integrations.langgraph import create_legal_rag_graph
        >>>
        >>> llm = ChatOpenAI(model="gpt-4o-mini")
        >>> graph = create_legal_rag_graph(llm, api_key="vg_xxx")
        >>>
        >>> result = graph.invoke({"query": "O que é ETP?"})
        >>> print(result["response"])
    """
    _check_langgraph()

    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        raise ImportError(
            "LangGraph não está instalado. Instale com:\n"
            "pip install langgraph"
        )

    from vectorgov import VectorGov

    # Estado do grafo RAG
    class RAGState(TypedDict, total=False):
        query: str
        documents: List[Document]
        context: str
        sources: List[str]
        response: str

    # Cliente VectorGov
    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    client = VectorGov(api_key=api_key, default_top_k=top_k, default_mode=mode)

    # Prompt padrão
    default_prompt = """Você é um especialista em legislação brasileira.
Responda à pergunta com base no contexto fornecido.
Sempre cite as fontes usando [número] ou o nome completo do documento.

Contexto:
{context}

Pergunta: {query}

Resposta:"""

    prompt_template = system_prompt or default_prompt

    # Nó de retrieval (usa o método configurado)
    from vectorgov.integrations.langchain import _hits_to_documents

    def retrieve(state: RAGState) -> RAGState:
        query = state["query"]

        if method == "hybrid":
            result = client.hybrid(query=query, top_k=top_k)
            hits = list(result.hits or []) + list(result.graph_nodes or [])
            context = result.to_context() if hasattr(result, "to_context") else ""
        elif method == "merged":
            result = client.merged(query=query, top_k=top_k)
            hits = result.results
            context = "\n\n".join(getattr(h, "text", "") for h in hits)
        elif method == "grep":
            result = client.grep(query=query, max_results=top_k)
            hits = result.matches
            context = "\n\n".join(getattr(h, "text", "") for h in hits)
        else:
            result = client.search(query=query)
            hits = result.hits
            context = result.to_context()

        documents = _hits_to_documents(hits)
        sources = [
            getattr(h, "source", "") or getattr(h, "document_id", "")
            for h in hits
        ]

        return {
            "documents": documents,
            "context": context,
            "sources": sources,
        }

    # Nó de geração
    def generate(state: RAGState) -> RAGState:
        prompt = prompt_template.format(
            context=state["context"],
            query=state["query"],
        )

        response = llm.invoke(prompt)
        response_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        return {"response": response_text}

    # Constrói grafo
    builder = StateGraph(RAGState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("generate", generate)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "VectorGovState",
    "create_vectorgov_tool",
    "create_retrieval_node",
    "create_legal_rag_graph",
]
