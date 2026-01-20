"""
Modelos de dados do VectorGov SDK.
"""

from dataclasses import dataclass, field
from typing import Optional, Iterator, Any, Literal
from datetime import datetime


# =============================================================================
# TOKEN STATS MODEL
# =============================================================================


@dataclass
class TokenStats:
    """Estatísticas de tokens retornadas pela API VectorGov.

    O cálculo de tokens é feito no servidor usando tiktoken,
    garantindo contagem precisa sem dependências extras no cliente.

    Útil para:
    - Estimar custos de API
    - Verificar se o contexto cabe na janela de contexto do modelo
    - Otimizar o número de resultados retornados

    Example:
        >>> stats = vg.estimate_tokens(results)
        >>> print(f"Context: {stats.context_tokens} tokens")
        >>> print(f"Total: {stats.total_tokens} tokens")
        >>> if stats.total_tokens > 128000:
        ...     print("Excede limite do GPT-4!")
    """

    context_tokens: int
    """Tokens do contexto (hits formatados)"""

    system_tokens: int
    """Tokens do system prompt"""

    query_tokens: int
    """Tokens da query do usuário"""

    total_tokens: int
    """Total de tokens (context + system + query)"""

    hits_count: int
    """Número de hits incluídos no contexto"""

    char_count: int
    """Número total de caracteres"""

    encoding: str = "cl100k_base"
    """Encoding usado (padrão: cl100k_base, compatível com GPT-4/Claude)"""

    def __repr__(self) -> str:
        return f"TokenStats(total={self.total_tokens}, context={self.context_tokens}, hits={self.hits_count})"


# =============================================================================
# SEARCH MODELS
# =============================================================================


@dataclass
class Metadata:
    """Metadados de um documento encontrado."""

    document_type: str
    """Tipo do documento (lei, decreto, in, etc.)"""

    document_number: str
    """Número do documento"""

    year: int
    """Ano do documento"""

    article: Optional[str] = None
    """Número do artigo"""

    paragraph: Optional[str] = None
    """Número do parágrafo"""

    item: Optional[str] = None
    """Número do inciso"""

    orgao: Optional[str] = None
    """Órgão emissor"""

    extra: dict = field(default_factory=dict)
    """Metadados adicionais"""

    def __repr__(self) -> str:
        parts = [f"{self.document_type.upper()} {self.document_number}/{self.year}"]
        if self.article:
            parts.append(f"Art. {self.article}")
        if self.paragraph:
            parts.append(f"§{self.paragraph}")
        if self.item:
            parts.append(f"inciso {self.item}")
        return ", ".join(parts)


@dataclass
class Hit:
    """Um resultado individual da busca."""

    text: str
    """Texto do chunk encontrado"""

    score: float
    """Score de relevância (0-1)"""

    source: str
    """Fonte formatada (ex: 'Lei 14.133/2021, Art. 33')"""

    metadata: Metadata
    """Metadados completos do documento"""

    chunk_id: Optional[str] = None
    """ID interno do chunk (para debugging)"""

    context: Optional[str] = None
    """Contexto adicional do chunk"""

    def __repr__(self) -> str:
        text_preview = self.text[:100] + "..." if len(self.text) > 100 else self.text
        return f"Hit(score={self.score:.3f}, source='{self.source}', text='{text_preview}')"


@dataclass
class SearchResult:
    """Resultado completo de uma busca."""

    query: str
    """Query original"""

    hits: list[Hit]
    """Lista de resultados encontrados"""

    total: int
    """Quantidade total de resultados"""

    latency_ms: int
    """Tempo de resposta em milissegundos"""

    cached: bool
    """Se o resultado veio do cache"""

    query_id: str
    """ID único da query (para feedback)"""

    mode: str
    """Modo de busca utilizado"""

    timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp da busca"""

    def __len__(self) -> int:
        return len(self.hits)

    def __iter__(self) -> Iterator[Hit]:
        return iter(self.hits)

    def __getitem__(self, index: int) -> Hit:
        return self.hits[index]

    def __repr__(self) -> str:
        return (
            f"SearchResult(query='{self.query[:50]}...', "
            f"total={self.total}, latency={self.latency_ms}ms, cached={self.cached})"
        )

    def to_context(self, max_chars: Optional[int] = None) -> str:
        """Converte os resultados em uma string de contexto.

        Args:
            max_chars: Limite máximo de caracteres (None = sem limite)

        Returns:
            String formatada com os resultados numerados

        Example:
            >>> context = results.to_context()
            >>> print(context)
        """
        parts = []
        total_chars = 0

        for i, hit in enumerate(self.hits, 1):
            entry = f"[{i}] {hit.source}\n{hit.text}\n"

            if max_chars and total_chars + len(entry) > max_chars:
                break

            parts.append(entry)
            total_chars += len(entry)

        return "\n".join(parts)

    def to_messages(
        self,
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_context_chars: Optional[int] = None,
    ) -> list[dict[str, str]]:
        """Converte os resultados em formato de mensagens para chat completions.

        Args:
            query: Pergunta a ser feita (usa self.query se não informado)
            system_prompt: Prompt de sistema customizado
            max_context_chars: Limite de caracteres do contexto

        Returns:
            Lista de mensagens no formato OpenAI/Anthropic

        Example:
            >>> messages = results.to_messages("O que é ETP?")
            >>> response = openai.chat.completions.create(messages=messages)
        """
        from vectorgov.config import SYSTEM_PROMPTS

        query = query or self.query
        system = system_prompt or SYSTEM_PROMPTS["default"]
        context = self.to_context(max_chars=max_context_chars)

        user_content = f"Contexto:\n{context}\n\nPergunta: {query}"

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

    def to_prompt(
        self,
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_context_chars: Optional[int] = None,
    ) -> str:
        """Converte os resultados em um prompt único (para Gemini e similares).

        Args:
            query: Pergunta a ser feita (usa self.query se não informado)
            system_prompt: Prompt de sistema customizado
            max_context_chars: Limite de caracteres do contexto

        Returns:
            String com o prompt completo

        Example:
            >>> prompt = results.to_prompt("O que é ETP?")
            >>> response = model.generate_content(prompt)
        """
        from vectorgov.config import SYSTEM_PROMPTS

        query = query or self.query
        system = system_prompt or SYSTEM_PROMPTS["default"]
        context = self.to_context(max_chars=max_context_chars)

        return f"""{system}

Contexto:
{context}

Pergunta: {query}

Resposta:"""

    def to_dict(self) -> dict[str, Any]:
        """Converte o resultado para dicionário."""
        return {
            "query": self.query,
            "hits": [
                {
                    "text": hit.text,
                    "score": hit.score,
                    "source": hit.source,
                    "metadata": {
                        "document_type": hit.metadata.document_type,
                        "document_number": hit.metadata.document_number,
                        "year": hit.metadata.year,
                        "article": hit.metadata.article,
                        "paragraph": hit.metadata.paragraph,
                        "item": hit.metadata.item,
                    },
                }
                for hit in self.hits
            ],
            "total": self.total,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
            "query_id": self.query_id,
            "mode": self.mode,
        }



# =============================================================================
# DOCUMENT MODELS
# =============================================================================


@dataclass
class DocumentSummary:
    """Resumo de um documento na base de conhecimento."""

    document_id: str
    """ID único do documento"""

    tipo_documento: str
    """Tipo do documento (LEI, DECRETO, IN, etc.)"""

    numero: str
    """Número do documento"""

    ano: int
    """Ano do documento"""

    titulo: Optional[str] = None
    """Título do documento"""

    descricao: Optional[str] = None
    """Descrição do documento"""

    chunks_count: int = 0
    """Número total de chunks"""

    enriched_count: int = 0
    """Número de chunks enriquecidos"""

    @property
    def is_enriched(self) -> bool:
        """Verifica se o documento está completamente enriquecido."""
        return self.enriched_count >= self.chunks_count and self.chunks_count > 0

    @property
    def enrichment_progress(self) -> float:
        """Progresso do enriquecimento (0.0 a 1.0)."""
        if self.chunks_count == 0:
            return 0.0
        return self.enriched_count / self.chunks_count

    def __repr__(self) -> str:
        status = "enriched" if self.is_enriched else f"{self.enrichment_progress:.0%}"
        return f"Document({self.tipo_documento} {self.numero}/{self.ano}, {status})"


@dataclass
class DocumentsResponse:
    """Resposta da listagem de documentos."""

    documents: list[DocumentSummary]
    """Lista de documentos"""

    total: int
    """Total de documentos"""

    page: int
    """Página atual"""

    pages: int
    """Total de páginas"""


@dataclass
class UploadResponse:
    """Resposta do upload de documento."""

    success: bool
    """Se o upload foi iniciado com sucesso"""

    message: str
    """Mensagem de status"""

    document_id: str
    """ID do documento criado"""

    task_id: str
    """ID da task de ingestão"""


@dataclass
class IngestStatus:
    """Status da ingestão de um documento."""

    task_id: str
    """ID da task"""

    status: Literal["pending", "processing", "completed", "failed"]
    """Status atual"""

    progress: int
    """Progresso (0-100)"""

    message: str
    """Mensagem de status"""

    document_id: Optional[str] = None
    """ID do documento (quando disponível)"""

    chunks_created: int = 0
    """Número de chunks criados"""


@dataclass
class EnrichStatus:
    """Status do enriquecimento de um documento."""

    task_id: str
    """ID da task"""

    status: Literal["pending", "processing", "completed", "error", "not_found", "unknown"]
    """Status atual"""

    progress: float
    """Progresso (0.0 a 1.0)"""

    chunks_enriched: int = 0
    """Chunks já enriquecidos"""

    chunks_pending: int = 0
    """Chunks pendentes"""

    chunks_failed: int = 0
    """Chunks com falha"""

    errors: list[str] = field(default_factory=list)
    """Lista de erros encontrados"""


@dataclass
class DeleteResponse:
    """Resposta da exclusão de documento."""

    success: bool
    """Se a exclusão foi bem-sucedida"""

    message: str
    """Mensagem de status"""


@dataclass
class StoreResponseResult:
    """Resultado do armazenamento de resposta de LLM externo.

    Usado quando o usuário gera uma resposta com seu próprio LLM
    e quer salvar no cache do VectorGov para permitir feedback.
    """

    success: bool
    """Se a resposta foi armazenada com sucesso"""

    query_hash: str
    """Hash único da query (usar em feedback())"""

    message: str
    """Mensagem de status"""


# =============================================================================
# AUDIT MODELS
# =============================================================================


@dataclass
class AuditLog:
    """Registro de evento de auditoria.

    Cada chamada à SDK gera um ou mais eventos de auditoria que permitem
    rastrear o uso da API, detectar problemas de segurança e analisar
    padrões de uso.
    """

    id: str
    """ID único do evento"""

    event_type: str
    """Tipo do evento (pii_detected, injection_detected, low_relevance_query, etc.)"""

    event_category: str
    """Categoria do evento (security, performance, validation)"""

    severity: str
    """Severidade do evento (info, warning, critical)"""

    query_text: Optional[str] = None
    """Texto da query que gerou o evento (se aplicável)"""

    detection_types: list[str] = field(default_factory=list)
    """Tipos de detecção ativados (para eventos de segurança)"""

    risk_score: Optional[float] = None
    """Score de risco (0.0 a 1.0)"""

    action_taken: Optional[str] = None
    """Ação tomada pelo sistema (logged, blocked, warned)"""

    endpoint: Optional[str] = None
    """Endpoint que gerou o evento"""

    client_ip: Optional[str] = None
    """IP do cliente (anonimizado)"""

    created_at: Optional[str] = None
    """Data/hora do evento (ISO 8601)"""

    details: dict = field(default_factory=dict)
    """Detalhes adicionais do evento"""

    def __repr__(self) -> str:
        return f"AuditLog({self.event_type}, severity={self.severity}, {self.created_at})"


@dataclass
class AuditLogsResponse:
    """Resposta da listagem de logs de auditoria."""

    logs: list[AuditLog]
    """Lista de logs de auditoria"""

    total: int
    """Total de logs encontrados"""

    page: int
    """Página atual"""

    pages: int
    """Total de páginas"""

    limit: int
    """Limite por página"""


@dataclass
class AuditStats:
    """Estatísticas agregadas de auditoria.

    Fornece uma visão geral dos eventos de auditoria em um período,
    útil para dashboards e monitoramento.
    """

    total_events: int
    """Total de eventos no período"""

    events_by_type: dict
    """Contagem de eventos por tipo"""

    events_by_severity: dict
    """Contagem de eventos por severidade"""

    events_by_category: dict
    """Contagem de eventos por categoria"""

    blocked_count: int
    """Quantidade de eventos bloqueados"""

    warning_count: int
    """Quantidade de avisos"""

    period_days: int
    """Período em dias das estatísticas"""

    def __repr__(self) -> str:
        return f"AuditStats(total={self.total_events}, blocked={self.blocked_count}, period={self.period_days}d)"
