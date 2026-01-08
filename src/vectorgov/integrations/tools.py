"""
Ferramentas para integração com Function Calling de LLMs.

Suporta:
- OpenAI (gpt-4, gpt-4o, etc.)
- Anthropic Claude (claude-3, claude-sonnet, etc.)
- Google Gemini (gemini-1.5, gemini-2.0, etc.)

Exemplo com OpenAI:
    >>> from vectorgov import VectorGov
    >>> from openai import OpenAI
    >>>
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> client = OpenAI()
    >>>
    >>> response = client.chat.completions.create(
    ...     model="gpt-4o",
    ...     messages=[{"role": "user", "content": "O que é ETP?"}],
    ...     tools=[vg.to_openai_tool()],
    ... )
    >>>
    >>> if response.choices[0].message.tool_calls:
    ...     result = vg.execute_tool_call(response.choices[0].message.tool_calls[0])
"""

from typing import Any, Optional

# Nome padrão da ferramenta
TOOL_NAME = "search_brazilian_legislation"

# Descrição da ferramenta
TOOL_DESCRIPTION = """Busca informações em legislação brasileira (leis, decretos, instruções normativas).
Use esta ferramenta quando precisar de informações sobre:
- Leis federais (Lei 14.133/2021, Lei 8.666/93, etc.)
- Decretos
- Instruções Normativas (INs)
- Portarias
- Regulamentos de licitações e contratos públicos
- Planejamento de contratações (ETP, TR, etc.)

A ferramenta retorna trechos relevantes da legislação com citações."""

# JSON Schema base para os parâmetros
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Pergunta ou termo de busca sobre legislação brasileira. Seja específico.",
        },
        "filters": {
            "type": "object",
            "description": "Filtros opcionais para refinar a busca",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["lei", "decreto", "in", "portaria"],
                    "description": "Tipo de documento (lei, decreto, in, portaria)",
                },
                "ano": {
                    "type": "integer",
                    "description": "Ano do documento (ex: 2021)",
                },
            },
        },
        "top_k": {
            "type": "integer",
            "description": "Quantidade de resultados (1-10). Default: 5",
            "minimum": 1,
            "maximum": 10,
            "default": 5,
        },
    },
    "required": ["query"],
}


def to_openai_tool() -> dict[str, Any]:
    """Retorna a ferramenta no formato OpenAI Function Calling.

    Returns:
        Dicionário com a definição da ferramenta para OpenAI

    Exemplo:
        >>> from openai import OpenAI
        >>> client = OpenAI()
        >>> response = client.chat.completions.create(
        ...     model="gpt-4o",
        ...     messages=[{"role": "user", "content": "O que é ETP?"}],
        ...     tools=[to_openai_tool()],
        ... )
    """
    return {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": TOOL_DESCRIPTION,
            "parameters": TOOL_SCHEMA,
        },
    }


def to_anthropic_tool() -> dict[str, Any]:
    """Retorna a ferramenta no formato Anthropic Claude Tools.

    Returns:
        Dicionário com a definição da ferramenta para Claude

    Exemplo:
        >>> from anthropic import Anthropic
        >>> client = Anthropic()
        >>> response = client.messages.create(
        ...     model="claude-sonnet-4-20250514",
        ...     messages=[{"role": "user", "content": "O que é ETP?"}],
        ...     tools=[to_anthropic_tool()],
        ... )
    """
    return {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "input_schema": TOOL_SCHEMA,
    }


def to_google_tool() -> dict[str, Any]:
    """Retorna a ferramenta no formato Google Gemini Function Calling.

    Returns:
        Dicionário com a definição da ferramenta para Gemini

    Exemplo:
        >>> import google.generativeai as genai
        >>> model = genai.GenerativeModel(
        ...     model_name="gemini-2.0-flash",
        ...     tools=[to_google_tool()],
        ... )
    """
    return {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "parameters": TOOL_SCHEMA,
    }


def parse_tool_arguments(arguments: dict[str, Any]) -> tuple[str, Optional[dict], int]:
    """Parseia os argumentos recebidos de uma chamada de ferramenta.

    Args:
        arguments: Dicionário com os argumentos da chamada

    Returns:
        Tupla (query, filters, top_k)

    Exemplo:
        >>> args = {"query": "O que é ETP?", "top_k": 3}
        >>> query, filters, top_k = parse_tool_arguments(args)
    """
    query = arguments.get("query", "")
    filters = arguments.get("filters")
    top_k = arguments.get("top_k", 5)

    return query, filters, top_k


def format_tool_response(search_result: "SearchResult") -> str:
    """Formata o resultado da busca para retornar ao LLM.

    Args:
        search_result: Resultado da busca VectorGov

    Returns:
        String formatada para o LLM processar

    Esta função cria um formato otimizado para LLMs, incluindo:
    - Contexto numerado com citações
    - Metadados relevantes
    - Instruções implícitas para citar fontes
    """
    if not search_result.hits:
        return "Nenhum resultado encontrado para esta busca na legislação."

    parts = [
        f"Encontrados {search_result.total} resultados na legislação brasileira:\n"
    ]

    for i, hit in enumerate(search_result.hits, 1):
        parts.append(f"[{i}] {hit.source}")
        parts.append(f"Relevância: {hit.score:.0%}")
        parts.append(f"{hit.text}")
        parts.append("")  # linha em branco

    parts.append("---")
    parts.append("Ao responder, cite as fontes usando o formato [número] ou o nome completo do documento.")

    return "\n".join(parts)
