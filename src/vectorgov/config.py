"""
Configurações do VectorGov SDK.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class SearchMode(str, Enum):
    """Modos de busca disponíveis.

    - FAST: Sem HyDE, sem reranker. Latência ~2s. Ideal para chatbots.
    - BALANCED: Com reranker, sem HyDE. Latência ~5s. Uso geral.
    - PRECISE: Com HyDE e reranker. Latência ~15s. Análises críticas.
    """
    FAST = "fast"
    BALANCED = "balanced"
    PRECISE = "precise"


class DocumentType(str, Enum):
    """Tipos de documentos disponíveis para filtro."""
    LEI = "lei"
    DECRETO = "decreto"
    INSTRUCAO_NORMATIVA = "in"
    PORTARIA = "portaria"
    RESOLUCAO = "resolucao"


@dataclass
class SDKConfig:
    """Configuração global do SDK."""

    # URL base da API
    base_url: str = "https://vectorgov.io/api/v1"

    # Timeout padrão em segundos
    timeout: int = 30

    # Configurações de busca padrão
    default_top_k: int = 5
    default_mode: SearchMode = SearchMode.BALANCED

    # Headers customizados
    custom_headers: dict = field(default_factory=dict)

    # Retry automático
    max_retries: int = 3
    retry_delay: float = 1.0

    # Cache local (futuro)
    enable_local_cache: bool = False
    cache_ttl: int = 300  # 5 minutos


# System prompts pré-definidos
SYSTEM_PROMPTS = {
    "default": """Você é um assistente especializado em legislação brasileira, especialmente em licitações e contratos públicos.

Instruções:
1. Use APENAS as informações do contexto fornecido para responder
2. Se a informação não estiver no contexto, diga que não encontrou
3. Sempre cite as fontes usando o formato [Fonte: Lei X, Art. Y]
4. Seja objetivo e direto nas respostas
5. Use linguagem formal adequada ao contexto jurídico""",

    "concise": """Você é um assistente jurídico. Responda de forma concisa e direta usando apenas o contexto fornecido. Cite as fontes.""",

    "detailed": """Você é um especialista em direito administrativo brasileiro.

Ao responder:
1. Analise cuidadosamente todo o contexto fornecido
2. Estruture a resposta em tópicos quando apropriado
3. Cite TODAS as fontes relevantes no formato [Lei X/Ano, Art. Y, §Z]
4. Explique termos técnicos quando necessário
5. Se houver divergências ou exceções, mencione-as
6. Conclua com um resumo prático quando aplicável

Use SOMENTE informações do contexto. Não invente ou extrapole.""",

    "chatbot": """Você é um assistente virtual amigável especializado em licitações públicas.
Responda de forma clara e acessível, evitando jargão excessivo.
Baseie suas respostas apenas no contexto fornecido e cite as fontes.""",
}


# Mapeamento de modos para configurações internas
# NOTA: use_cache=False por padrão para privacidade
# O cache é compartilhado entre todos os clientes, então o desenvolvedor
# deve explicitamente habilitar (use_cache=True) se aceitar o trade-off
# de privacidade em troca de menor latência.
MODE_CONFIG = {
    SearchMode.FAST: {
        "use_hyde": False,
        "use_reranker": False,
        "use_cache": False,  # Privacidade por padrão
    },
    SearchMode.BALANCED: {
        "use_hyde": False,
        "use_reranker": True,
        "use_cache": False,  # Privacidade por padrão
    },
    SearchMode.PRECISE: {
        "use_hyde": True,
        "use_reranker": True,
        "use_cache": False,  # Privacidade por padrão
    },
}
