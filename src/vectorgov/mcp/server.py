"""
Servidor MCP do VectorGov.

Este servidor expõe ferramentas para buscar legislação brasileira
via Model Context Protocol (MCP).

Ferramentas disponíveis:
- search_legislation: Busca semântica em legislação
- list_documents: Lista documentos disponíveis
- get_document_info: Informações sobre um documento específico

Uso:
    python -m vectorgov.mcp
    # ou
    vectorgov-mcp
"""

import os
import logging
from typing import Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vectorgov-mcp")

# Verifica se o SDK MCP está instalado
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None


def _check_mcp():
    """Verifica se o SDK MCP está instalado."""
    if not MCP_AVAILABLE:
        raise ImportError(
            "O SDK MCP não está instalado. Instale com:\n"
            "pip install 'vectorgov[mcp]'\n"
            "ou\n"
            "pip install mcp"
        )


def create_server(
    api_key: Optional[str] = None,
    name: str = "VectorGov",
) -> "FastMCP":
    """Cria o servidor MCP do VectorGov.

    Args:
        api_key: Chave de API do VectorGov. Se não fornecida, usa VECTORGOV_API_KEY.
        name: Nome do servidor MCP.

    Returns:
        Instância do servidor FastMCP configurada.

    Raises:
        ImportError: Se o SDK MCP não estiver instalado.
        ValueError: Se a API key não for fornecida.
    """
    _check_mcp()

    # Obtém API key
    api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
    if not api_key:
        raise ValueError(
            "API key não fornecida. Configure VECTORGOV_API_KEY ou passe api_key."
        )

    # Cria cliente VectorGov
    from vectorgov import VectorGov
    client = VectorGov(api_key=api_key)

    # Cria servidor MCP
    mcp = FastMCP(name)

    # =========================================================================
    # TOOL: search_legislation
    # =========================================================================
    @mcp.tool()
    def search_legislation(
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        year: Optional[int] = None,
    ) -> str:
        """Busca informações em legislação brasileira.

        Use esta ferramenta quando precisar de informações sobre:
        - Leis federais (Lei 14.133/2021, Lei 8.666/93, etc.)
        - Decretos
        - Instruções Normativas (INs)
        - Portarias
        - Regulamentos de licitações e contratos públicos
        - Planejamento de contratações (ETP, TR, etc.)

        Args:
            query: Pergunta ou termo de busca sobre legislação brasileira.
            top_k: Quantidade de resultados (1-10). Default: 5.
            document_type: Filtrar por tipo (lei, decreto, in, portaria).
            year: Filtrar por ano do documento.

        Returns:
            Trechos relevantes da legislação com citações.
        """
        logger.info(f"Buscando: {query}")

        # Monta filtros
        filters = {}
        if document_type:
            filters["tipo"] = document_type
        if year:
            filters["ano"] = year

        # Executa busca
        try:
            result = client.search(
                query=query,
                top_k=min(top_k, 10),
                filters=filters if filters else None,
            )
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return f"Erro ao buscar legislação: {str(e)}"

        if not result.hits:
            return "Nenhum resultado encontrado para esta busca na legislação brasileira."

        # Formata resposta
        parts = [
            f"Encontrados {result.total} resultados na legislação brasileira:\n"
        ]

        for i, hit in enumerate(result.hits, 1):
            parts.append(f"[{i}] {hit.source}")
            parts.append(f"Relevância: {hit.score:.0%}")
            parts.append(f"{hit.text}")
            parts.append("")

        parts.append("---")
        parts.append(
            "Cite as fontes ao responder usando [número] ou o nome completo do documento."
        )

        return "\n".join(parts)

    # =========================================================================
    # TOOL: list_available_documents
    # =========================================================================
    @mcp.tool()
    def list_available_documents() -> str:
        """Lista os documentos disponíveis na base de conhecimento.

        Use esta ferramenta para saber quais leis, decretos e instruções
        normativas estão disponíveis para consulta.

        Returns:
            Lista de documentos disponíveis com tipo e ano.
        """
        logger.info("Listando documentos disponíveis")

        # Documentos conhecidos (hardcoded por enquanto)
        # TODO: Implementar endpoint na API para listar documentos
        documents = [
            {"tipo": "LEI", "numero": "14.133", "ano": 2021, "nome": "Nova Lei de Licitações"},
            {"tipo": "IN", "numero": "58", "ano": 2022, "nome": "ETP - Estudo Técnico Preliminar"},
            {"tipo": "IN", "numero": "65", "ano": 2021, "nome": "Pesquisa de Preços"},
            {"tipo": "IN", "numero": "81", "ano": 2022, "nome": "Plano de Contratações Anual"},
        ]

        parts = ["Documentos disponíveis na base VectorGov:\n"]

        for doc in documents:
            parts.append(
                f"- {doc['tipo']} {doc['numero']}/{doc['ano']} - {doc['nome']}"
            )

        parts.append("\n---")
        parts.append(
            "Use search_legislation para buscar informações específicas nesses documentos."
        )

        return "\n".join(parts)

    # =========================================================================
    # TOOL: get_article_text
    # =========================================================================
    @mcp.tool()
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
            Texto completo do artigo com seus parágrafos e incisos.
        """
        logger.info(
            f"Buscando Art. {article_number} da {document_type} {document_number}/{year}"
        )

        # Busca específica pelo artigo
        query = f"Art. {article_number} {document_type} {document_number}"
        filters = {
            "tipo": document_type.lower(),
            "ano": year,
        }

        try:
            result = client.search(
                query=query,
                top_k=5,
                filters=filters,
                mode="precise",
            )
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return f"Erro ao buscar artigo: {str(e)}"

        if not result.hits:
            return (
                f"Artigo {article_number} não encontrado na "
                f"{document_type} {document_number}/{year}."
            )

        # Filtra resultados pelo artigo específico
        relevant_hits = [
            hit for hit in result.hits
            if hit.metadata.article == article_number
        ]

        if not relevant_hits:
            # Retorna o resultado mais relevante mesmo assim
            relevant_hits = result.hits[:1]

        parts = [
            f"**{document_type.upper()} {document_number}/{year} - Art. {article_number}**\n"
        ]

        for hit in relevant_hits:
            parts.append(hit.text)
            parts.append("")

        return "\n".join(parts)

    # =========================================================================
    # RESOURCE: legislation://info
    # =========================================================================
    @mcp.resource("legislation://info")
    def get_legislation_info() -> str:
        """Informações sobre a base de legislação VectorGov."""
        return """
# Base de Legislação VectorGov

A base VectorGov contém legislação brasileira sobre licitações e contratos públicos.

## Documentos Disponíveis

- **Lei 14.133/2021** - Nova Lei de Licitações e Contratos
- **IN SEGES 58/2022** - Estudo Técnico Preliminar (ETP)
- **IN SEGES 65/2021** - Pesquisa de Preços
- **IN SEGES 81/2022** - Plano de Contratações Anual

## Como Usar

Use a ferramenta `search_legislation` para buscar informações específicas.
Exemplos de perguntas:
- "O que é ETP?"
- "Quando o ETP pode ser dispensado?"
- "Quais os critérios de julgamento na licitação?"
- "Como fazer pesquisa de preços?"

## Suporte

- Site: https://vectorgov.io
- Documentação: https://docs.vectorgov.io
"""

    logger.info(f"Servidor MCP '{name}' criado com sucesso")
    return mcp


def run_server(
    api_key: Optional[str] = None,
    transport: str = "stdio",
):
    """Executa o servidor MCP.

    Args:
        api_key: Chave de API do VectorGov.
        transport: Tipo de transporte (stdio, sse, streamable-http).
    """
    _check_mcp()

    mcp = create_server(api_key=api_key)
    logger.info(f"Iniciando servidor MCP via {transport}...")
    mcp.run(transport=transport)


# Entry point para CLI
def main():
    """Entry point para o comando vectorgov-mcp."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Servidor MCP do VectorGov para integração com Claude Desktop e outros"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Tipo de transporte (default: stdio)",
    )
    parser.add_argument(
        "--api-key",
        help="API key do VectorGov (ou use VECTORGOV_API_KEY)",
    )

    args = parser.parse_args()

    try:
        run_server(api_key=args.api_key, transport=args.transport)
    except ValueError as e:
        print(f"Erro: {e}")
        print("\nConfigure a variável de ambiente VECTORGOV_API_KEY:")
        print("  export VECTORGOV_API_KEY=vg_sua_chave_aqui")
        exit(1)
    except ImportError as e:
        print(f"Erro: {e}")
        exit(1)


if __name__ == "__main__":
    main()
