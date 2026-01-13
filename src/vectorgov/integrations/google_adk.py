"""
Integração do VectorGov SDK com Google Agent Development Kit (ADK).

Fornece ferramentas para uso com agentes Google ADK:
- create_search_tool: Cria função de busca para ADK
- VectorGovToolset: Toolset completo para ADK

Requisitos:
    pip install google-adk

Exemplo básico:
    >>> from google.adk.agents import Agent
    >>> from vectorgov.integrations.google_adk import create_search_tool
    >>>
    >>> search_tool = create_search_tool(api_key="vg_xxx")
    >>>
    >>> agent = Agent(
    ...     name="legal_assistant",
    ...     model="gemini-2.0-flash",
    ...     instruction="Você é um assistente jurídico especializado em legislação brasileira.",
    ...     tools=[search_tool],
    ... )

Exemplo com Toolset:
    >>> from vectorgov.integrations.google_adk import VectorGovToolset
    >>>
    >>> toolset = VectorGovToolset(api_key="vg_xxx")
    >>>
    >>> agent = Agent(
    ...     name="legal_expert",
    ...     model="gemini-2.0-flash",
    ...     tools=toolset.get_tools(),
    ... )
"""

from typing import Optional, List, Dict, Any, Callable
import os

# Verificação de disponibilidade do Google ADK
try:
    from google.adk.tools import FunctionTool
    from google.genai.types import FunctionDeclaration, Schema, Type

    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    FunctionTool = None
    FunctionDeclaration = None


def _check_google_adk():
    """Verifica se Google ADK está instalado."""
    if not GOOGLE_ADK_AVAILABLE:
        raise ImportError(
            "Google ADK não está instalado. Instale com:\n"
            "pip install google-adk\n\n"
            "Ou instale o VectorGov com extras:\n"
            "pip install 'vectorgov[google-adk]'"
        )


# ============================================================================
# Função de busca para ADK
# ============================================================================


def create_search_tool(
    api_key: Optional[str] = None,
    top_k: int = 5,
    mode: str = "balanced",
    name: str = "search_brazilian_legislation",
    description: Optional[str] = None,
) -> Callable:
    """Cria uma função de busca para uso com Google ADK.

    Esta função pode ser usada diretamente como tool em agentes ADK.

    Args:
        api_key: Chave de API VectorGov
        top_k: Quantidade de resultados (1-50)
        mode: Modo de busca (fast, balanced, precise)
        name: Nome da função
        description: Descrição customizada

    Returns:
        Função callable para uso como tool ADK

    Exemplo:
        >>> from google.adk.agents import Agent
        >>> from vectorgov.integrations.google_adk import create_search_tool
        >>>
        >>> tool = create_search_tool(api_key="vg_xxx")
        >>> agent = Agent(
        ...     name="assistant",
        ...     model="gemini-2.0-flash",
        ...     tools=[tool],
        ... )
    """
    from vectorgov import VectorGov

    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    client = VectorGov(api_key=api_key, default_top_k=top_k, default_mode=mode)

    def search_brazilian_legislation(
        query: str,
        document_type: Optional[str] = None,
        year: Optional[int] = None,
    ) -> str:
        """Busca informações em legislação brasileira.

        Use para consultar leis, decretos, instruções normativas
        e outras normas jurídicas brasileiras.

        Args:
            query: Pergunta ou termo de busca sobre legislação.
            document_type: Filtrar por tipo (lei, decreto, in).
            year: Filtrar por ano do documento.

        Returns:
            Trechos relevantes da legislação com fontes.
        """
        # Monta filtros
        filters = {}
        if document_type:
            filters["tipo"] = document_type.lower()
        if year:
            filters["ano"] = year

        # Executa busca
        result = client.search(
            query=query,
            filters=filters if filters else None,
        )

        if not result.hits:
            return "Nenhum resultado encontrado na legislação brasileira para esta consulta."

        # Formata resposta
        parts = [f"Encontrados {result.total} resultados na legislação brasileira:\n"]

        for i, hit in enumerate(result.hits, 1):
            parts.append(f"[{i}] {hit.source}")
            parts.append(f"Relevância: {hit.score:.0%}")
            parts.append(f"{hit.text}")
            parts.append("")

        parts.append("---")
        parts.append(
            "Cite as fontes ao responder usando [número] ou o nome do documento."
        )

        return "\n".join(parts)

    # Adiciona metadados para ADK
    search_brazilian_legislation.__name__ = name
    if description:
        search_brazilian_legislation.__doc__ = description

    return search_brazilian_legislation


def create_list_documents_tool(api_key: Optional[str] = None) -> Callable:
    """Cria função para listar documentos disponíveis.

    Args:
        api_key: Chave de API VectorGov

    Returns:
        Função callable para uso como tool ADK
    """

    def list_available_documents() -> str:
        """Lista os documentos disponíveis na base de legislação.

        Use para saber quais leis, decretos e instruções normativas
        estão disponíveis para consulta.

        Returns:
            Lista de documentos disponíveis.
        """
        # Lista hardcoded por enquanto
        documents = [
            {"tipo": "LEI", "numero": "14.133", "ano": 2021, "nome": "Nova Lei de Licitações"},
            {"tipo": "IN", "numero": "58", "ano": 2022, "nome": "ETP - Estudo Técnico Preliminar"},
            {"tipo": "IN", "numero": "65", "ano": 2021, "nome": "Pesquisa de Preços"},
            {"tipo": "IN", "numero": "81", "ano": 2022, "nome": "Plano de Contratações Anual"},
        ]

        parts = ["Documentos disponíveis na base VectorGov:\n"]

        for doc in documents:
            parts.append(f"- {doc['tipo']} {doc['numero']}/{doc['ano']} - {doc['nome']}")

        parts.append("\n---")
        parts.append("Use search_brazilian_legislation para buscar informações específicas.")

        return "\n".join(parts)

    return list_available_documents


def create_get_article_tool(
    api_key: Optional[str] = None,
    mode: str = "precise",
) -> Callable:
    """Cria função para obter texto de artigo específico.

    Args:
        api_key: Chave de API VectorGov
        mode: Modo de busca (recomendado: precise)

    Returns:
        Função callable para uso como tool ADK
    """
    from vectorgov import VectorGov

    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    client = VectorGov(api_key=api_key, default_mode=mode)

    def get_article_text(
        document_type: str,
        document_number: str,
        year: int,
        article_number: str,
    ) -> str:
        """Obtém o texto completo de um artigo específico.

        Use quando precisar do texto exato de um artigo de lei.

        Args:
            document_type: Tipo do documento (lei, decreto, in).
            document_number: Número do documento (ex: "14133", "58").
            year: Ano do documento (ex: 2021, 2022).
            article_number: Número do artigo (ex: "1", "33", "75").

        Returns:
            Texto completo do artigo com parágrafos e incisos.
        """
        query = f"Art. {article_number} {document_type} {document_number}"
        filters = {
            "tipo": document_type.lower(),
            "ano": year,
        }

        result = client.search(query=query, top_k=5, filters=filters)

        if not result.hits:
            return (
                f"Artigo {article_number} não encontrado na "
                f"{document_type} {document_number}/{year}."
            )

        # Filtra pelo artigo específico
        relevant_hits = [
            hit for hit in result.hits
            if hit.metadata.article == article_number
        ]

        if not relevant_hits:
            relevant_hits = result.hits[:1]

        parts = [
            f"**{document_type.upper()} {document_number}/{year} - Art. {article_number}**\n"
        ]

        for hit in relevant_hits:
            parts.append(hit.text)
            parts.append("")

        return "\n".join(parts)

    return get_article_text


# ============================================================================
# Toolset para ADK
# ============================================================================


class VectorGovToolset:
    """Conjunto de ferramentas VectorGov para Google ADK.

    Fornece múltiplas ferramentas para consulta de legislação brasileira.

    Attributes:
        api_key: Chave de API VectorGov
        top_k: Quantidade de resultados padrão
        mode: Modo de busca padrão

    Exemplo:
        >>> from google.adk.agents import Agent
        >>> from vectorgov.integrations.google_adk import VectorGovToolset
        >>>
        >>> toolset = VectorGovToolset(api_key="vg_xxx")
        >>>
        >>> agent = Agent(
        ...     name="legal_expert",
        ...     model="gemini-2.0-flash",
        ...     instruction="Você é um especialista em legislação brasileira.",
        ...     tools=toolset.get_tools(),
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        top_k: int = 5,
        mode: str = "balanced",
    ):
        """Inicializa o toolset.

        Args:
            api_key: Chave de API VectorGov
            top_k: Quantidade de resultados (1-50)
            mode: Modo de busca (fast, balanced, precise)
        """
        self.api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
        self.top_k = top_k
        self.mode = mode

        # Cria ferramentas
        self._search_tool = create_search_tool(
            api_key=self.api_key,
            top_k=self.top_k,
            mode=self.mode,
        )
        self._list_tool = create_list_documents_tool(api_key=self.api_key)
        self._article_tool = create_get_article_tool(
            api_key=self.api_key,
            mode="precise",
        )

    def get_tools(self) -> List[Callable]:
        """Retorna lista de todas as ferramentas.

        Returns:
            Lista de funções para usar como tools no ADK
        """
        return [
            self._search_tool,
            self._list_tool,
            self._article_tool,
        ]

    def get_search_tool(self) -> Callable:
        """Retorna apenas a ferramenta de busca."""
        return self._search_tool

    def get_list_tool(self) -> Callable:
        """Retorna apenas a ferramenta de listagem."""
        return self._list_tool

    def get_article_tool(self) -> Callable:
        """Retorna apenas a ferramenta de artigo."""
        return self._article_tool


# ============================================================================
# Helper para criar agente completo
# ============================================================================


def create_legal_agent(
    api_key: Optional[str] = None,
    model: str = "gemini-2.0-flash",
    name: str = "legal_assistant",
    instruction: Optional[str] = None,
) -> Any:
    """Cria um agente ADK pré-configurado para consulta de legislação.

    Helper para criar rapidamente um agente especializado em
    legislação brasileira.

    Args:
        api_key: Chave de API VectorGov
        model: Modelo Gemini a usar
        name: Nome do agente
        instruction: Instrução customizada

    Returns:
        Agente ADK configurado

    Exemplo:
        >>> from vectorgov.integrations.google_adk import create_legal_agent
        >>>
        >>> agent = create_legal_agent(api_key="vg_xxx")
        >>> response = agent.run("O que é ETP?")
    """
    _check_google_adk()

    try:
        from google.adk.agents import Agent
    except ImportError:
        raise ImportError(
            "Google ADK não está instalado. Instale com:\n"
            "pip install google-adk"
        )

    default_instruction = """Você é um assistente jurídico especializado em legislação brasileira.

Você tem acesso a ferramentas para consultar:
- Lei 14.133/2021 (Nova Lei de Licitações)
- Instruções Normativas (INs) do Ministério da Gestão

Ao responder:
1. Use as ferramentas disponíveis para buscar informações atualizadas
2. Sempre cite as fontes (artigos, parágrafos, incisos)
3. Seja preciso e técnico nas respostas
4. Se não encontrar informação, diga claramente"""

    toolset = VectorGovToolset(api_key=api_key)

    agent = Agent(
        name=name,
        model=model,
        instruction=instruction or default_instruction,
        tools=toolset.get_tools(),
    )

    return agent


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "create_search_tool",
    "create_list_documents_tool",
    "create_get_article_tool",
    "VectorGovToolset",
    "create_legal_agent",
]
