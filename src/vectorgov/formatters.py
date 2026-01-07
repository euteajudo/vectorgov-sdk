"""
Formatadores para integração com LLMs.

Este módulo contém funções auxiliares para formatar resultados
de busca para diferentes LLMs e frameworks.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vectorgov.models import SearchResult


def to_langchain_docs(results: "SearchResult") -> list:
    """Converte resultados para documentos LangChain.

    Requer: pip install langchain-core

    Args:
        results: Resultado da busca VectorGov

    Returns:
        Lista de Document do LangChain

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> from langchain.chains import create_retrieval_chain
        >>> docs = to_langchain_docs(results)
    """
    try:
        from langchain_core.documents import Document
    except ImportError:
        raise ImportError(
            "LangChain não está instalado. "
            "Execute: pip install langchain-core"
        )

    documents = []
    for hit in results.hits:
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


def to_llamaindex_nodes(results: "SearchResult") -> list:
    """Converte resultados para nodes do LlamaIndex.

    Requer: pip install llama-index-core

    Args:
        results: Resultado da busca VectorGov

    Returns:
        Lista de TextNode do LlamaIndex

    Example:
        >>> from llama_index.core import VectorStoreIndex
        >>> nodes = to_llamaindex_nodes(results)
        >>> index = VectorStoreIndex(nodes)
    """
    try:
        from llama_index.core.schema import TextNode
    except ImportError:
        raise ImportError(
            "LlamaIndex não está instalado. "
            "Execute: pip install llama-index-core"
        )

    nodes = []
    for hit in results.hits:
        node = TextNode(
            text=hit.text,
            metadata={
                "source": hit.source,
                "score": hit.score,
                "document_type": hit.metadata.document_type,
                "document_number": hit.metadata.document_number,
                "year": hit.metadata.year,
                "article": hit.metadata.article,
            },
        )
        nodes.append(node)

    return nodes


def format_citations(results: "SearchResult", style: str = "inline") -> str:
    """Formata citações dos resultados.

    Args:
        results: Resultado da busca VectorGov
        style: Estilo de citação ("inline", "footnote", "academic")

    Returns:
        String com citações formatadas

    Example:
        >>> citations = format_citations(results, style="academic")
        >>> print(citations)
        [1] BRASIL. Lei nº 14.133/2021, Art. 33.
        [2] BRASIL. IN SEGES nº 58/2022, Art. 6.
    """
    citations = []

    for i, hit in enumerate(results.hits, 1):
        if style == "inline":
            citations.append(f"[{i}] {hit.source}")

        elif style == "footnote":
            citations.append(f"{i}. {hit.source}")

        elif style == "academic":
            doc_type = hit.metadata.document_type.upper()
            number = hit.metadata.document_number
            year = hit.metadata.year
            article = hit.metadata.article

            ref = f"[{i}] BRASIL. {doc_type} nº {number}/{year}"
            if article:
                ref += f", Art. {article}"
            ref += "."
            citations.append(ref)

    return "\n".join(citations)


def create_rag_prompt(
    results: "SearchResult",
    query: str,
    template: Optional[str] = None,
) -> str:
    """Cria um prompt RAG customizado.

    Args:
        results: Resultado da busca VectorGov
        query: Pergunta do usuário
        template: Template customizado (usa {context} e {query})

    Returns:
        Prompt formatado

    Example:
        >>> template = '''
        ... Contexto jurídico:
        ... {context}
        ...
        ... Com base no contexto acima, responda:
        ... {query}
        ... '''
        >>> prompt = create_rag_prompt(results, "O que é ETP?", template)
    """
    if template is None:
        template = """Você é um assistente especializado em legislação brasileira.

Contexto:
{context}

Pergunta: {query}

Instruções:
- Use APENAS informações do contexto acima
- Cite as fontes no formato [Fonte: Lei X, Art. Y]
- Se não encontrar a informação, diga claramente

Resposta:"""

    context = results.to_context()
    return template.format(context=context, query=query)
