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

from typing import Optional, List, Any, TypedDict, Annotated, Callable, Sequence
import os
import operator

# Imports condicionais para LangGraph
try:
    from langchain_core.tools import BaseTool, tool
    from langchain_core.documents import Document
    from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
    from pydantic import Field, PrivateAttr

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    BaseTool = object
    Document = dict


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


def create_vectorgov_tool(
    api_key: Optional[str] = None,
    top_k: int = 5,
    mode: str = "balanced",
    name: str = "search_legislation",
    description: Optional[str] = None,
) -> BaseTool:
    """Cria uma ferramenta VectorGov para uso em grafos LangGraph.

    Esta ferramenta pode ser usada com create_react_agent ou em ToolNodes
    customizados.

    Args:
        api_key: Chave de API. Se não fornecida, usa VECTORGOV_API_KEY
        top_k: Quantidade de resultados (1-50)
        mode: Modo de busca (fast, balanced, precise)
        name: Nome da ferramenta
        description: Descrição customizada

    Returns:
        Ferramenta LangChain configurada

    Exemplo com ReAct:
        >>> from langgraph.prebuilt import create_react_agent
        >>> from langchain_openai import ChatOpenAI
        >>>
        >>> tool = create_vectorgov_tool(api_key="vg_xxx")
        >>> agent = create_react_agent(ChatOpenAI(), tools=[tool])
        >>> result = agent.invoke({"messages": [("user", "O que é ETP?")]})

    Exemplo com ToolNode:
        >>> from langgraph.prebuilt import ToolNode
        >>>
        >>> tool = create_vectorgov_tool()
        >>> tool_node = ToolNode(tools=[tool])
    """
    _check_langgraph()

    from vectorgov import VectorGov

    # Inicializa cliente
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
        result = client.search(query=query)

        if not result.hits:
            return "Nenhum resultado encontrado na legislação brasileira."

        parts = [f"Encontrados {result.total} resultados:\n"]
        for i, hit in enumerate(result.hits, 1):
            parts.append(f"[{i}] {hit.source}")
            parts.append(f"{hit.text}")
            parts.append("")

        return "\n".join(parts)

    return search_legislation


# ============================================================================
# Nó de retrieval para grafos customizados
# ============================================================================


def create_retrieval_node(
    api_key: Optional[str] = None,
    top_k: int = 5,
    mode: str = "balanced",
    query_key: str = "query",
    output_key: str = "documents",
    context_key: str = "context",
) -> Callable[[VectorGovState], dict]:
    """Cria um nó de retrieval para grafos LangGraph customizados.

    O nó lê a query do estado, busca documentos relevantes e retorna
    os documentos e contexto formatado.

    Args:
        api_key: Chave de API
        top_k: Quantidade de documentos
        mode: Modo de busca
        query_key: Chave do estado com a query
        output_key: Chave para salvar documentos
        context_key: Chave para salvar contexto formatado

    Returns:
        Função nó para usar em StateGraph

    Exemplo:
        >>> from langgraph.graph import StateGraph, START, END
        >>>
        >>> retrieval_node = create_retrieval_node(api_key="vg_xxx")
        >>>
        >>> builder = StateGraph(VectorGovState)
        >>> builder.add_node("retrieve", retrieval_node)
        >>> builder.add_edge(START, "retrieve")
        >>> builder.add_edge("retrieve", END)
        >>> graph = builder.compile()
        >>>
        >>> result = graph.invoke({"query": "O que é ETP?"})
        >>> print(result["context"])
    """
    _check_langgraph()

    from vectorgov import VectorGov

    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    client = VectorGov(api_key=api_key, default_top_k=top_k, default_mode=mode)

    def retrieval_node(state: dict) -> dict:
        """Nó de retrieval que busca documentos relevantes."""
        query = state.get(query_key, "")

        if not query:
            # Tenta extrair da última mensagem
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

        # Busca documentos
        result = client.search(query=query)

        # Converte para Documents
        documents = []
        sources = []
        for hit in result.hits:
            doc = Document(
                page_content=hit.text,
                metadata={
                    "source": hit.source,
                    "score": hit.score,
                    "document_type": hit.metadata.document_type,
                    "article": hit.metadata.article,
                },
            )
            documents.append(doc)
            sources.append(hit.source)

        # Formata contexto
        context = result.to_context()

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
        from langgraph.graph import StateGraph, START, END
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

    # Nó de retrieval
    def retrieve(state: RAGState) -> RAGState:
        query = state["query"]
        result = client.search(query=query)

        documents = []
        sources = []
        for hit in result.hits:
            doc = Document(
                page_content=hit.text,
                metadata={"source": hit.source, "score": hit.score},
            )
            documents.append(doc)
            sources.append(hit.source)

        return {
            "documents": documents,
            "context": result.to_context(),
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
