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

    # Curadoria (SPEC 1C) — acompanham o chunk, não disputam slots
    nota_especialista: Optional[str] = None
    """Nota do especialista jurídico sobre este dispositivo"""

    jurisprudencia_tcu: Optional[str] = None
    """Jurisprudência TCU relacionada a este dispositivo"""

    acordao_tcu_key: Optional[str] = None
    """Chave/número do acórdão TCU"""

    acordao_tcu_link: Optional[str] = None
    """Link para o acórdão TCU"""

    def __repr__(self) -> str:
        text_preview = self.text[:100] + "..." if len(self.text) > 100 else self.text
        return f"Hit(score={self.score:.3f}, source='{self.source}', text='{text_preview}')"


# =============================================================================
# CITATION EXPANSION MODELS
# =============================================================================


@dataclass
class ExpandedChunk:
    """Chunk obtido via expansão de citações normativas.

    Quando um chunk referencia outro documento/artigo (ex: "conforme art. 18 da Lei 14.133"),
    o sistema pode expandir automaticamente trazendo o conteúdo referenciado.

    Example:
        >>> result = vg.search("ETP", expand_citations=True)
        >>> for expanded in result.expanded_chunks:
        ...     print(f"Citado por: {expanded.source_chunk_id}")
        ...     print(f"Texto: {expanded.text[:100]}...")
    """

    chunk_id: str
    """ID do chunk expandido (ex: 'LEI-14133-2021#ART-018')"""

    node_id: str
    """Node ID canônico no formato leis:{document_id}#{span_id}"""

    text: str
    """Texto do chunk expandido"""

    document_id: str
    """ID do documento fonte"""

    span_id: str
    """ID do dispositivo (ex: 'ART-018', 'PAR-005-1')"""

    device_type: str = "article"
    """Tipo do dispositivo (article, paragraph, inciso, alinea)"""

    source_chunk_id: str = ""
    """ID do chunk que citou este (origem da referência)"""

    source_citation_raw: str = ""
    """Texto original da citação (ex: 'art. 18 da Lei nº 14.133')"""

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"ExpandedChunk(node_id='{self.node_id}', text='{text_preview}')"


@dataclass
class CitationExpansionStats:
    """Estatísticas de expansão de citações.

    Fornece métricas sobre quantas citações foram encontradas, resolvidas
    e expandidas durante a busca.

    Example:
        >>> result = vg.search("ETP", expand_citations=True)
        >>> stats = result.expansion_stats
        >>> print(f"Encontradas: {stats.citations_scanned_count}")
        >>> print(f"Resolvidas: {stats.citations_resolved_count}")
        >>> print(f"Expandidas: {stats.expanded_chunks_count}")
    """

    expanded_chunks_count: int
    """Número de chunks expandidos com sucesso"""

    citations_scanned_count: int
    """Total de citações encontradas nos hits originais"""

    citations_resolved_count: int
    """Citações que foram resolvidas para node_ids válidos"""

    expansion_time_ms: float
    """Tempo de expansão em milissegundos"""

    skipped_self_references: int = 0
    """Citações ignoradas por serem auto-referências"""

    skipped_duplicates: int = 0
    """Citações ignoradas por serem duplicadas"""

    skipped_token_budget: int = 0
    """Citações ignoradas por exceder budget de tokens"""

    def __repr__(self) -> str:
        return (
            f"CitationExpansionStats(expanded={self.expanded_chunks_count}, "
            f"scanned={self.citations_scanned_count}, "
            f"resolved={self.citations_resolved_count})"
        )


@dataclass
class SearchResult:
    """Resultado completo de uma busca.

    Quando `expand_citations=True` é passado na busca, o resultado
    incluirá chunks expandidos e estatísticas de expansão.

    Example:
        >>> result = vg.search("ETP", expand_citations=True)
        >>> print(f"Hits: {len(result.hits)}")
        >>> print(f"Expanded: {len(result.expanded_chunks)}")
        >>> if result.expansion_stats:
        ...     print(f"Citações encontradas: {result.expansion_stats.citations_scanned_count}")
    """

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

    expanded_chunks: list[ExpandedChunk] = field(default_factory=list)
    """Chunks expandidos via citações (requer expand_citations=True)"""

    expansion_stats: Optional[CitationExpansionStats] = None
    """Estatísticas de expansão de citações (requer expand_citations=True)"""

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

    def to_context(
        self,
        max_chars: Optional[int] = None,
        include_expanded: bool = True,
        include_stats: bool = True,
    ) -> str:
        """Converte os resultados em uma string de contexto estruturado.

        O contexto é dividido em duas seções:
        - EVIDÊNCIA DIRETA: resultados diretos da busca semântica
        - TRECHOS CITADOS: chunks trazidos por expansão de citações

        Isso permite que o LLM entenda claramente a origem de cada trecho
        e priorize a evidência direta nas respostas.

        Args:
            max_chars: Limite máximo de caracteres (None = sem limite)
            include_expanded: Se True, inclui chunks expandidos via citações
            include_stats: Se True, inclui resumo das estatísticas de expansão

        Returns:
            String formatada com os resultados em seções separadas

        Example:
            >>> context = results.to_context()
            >>> print(context)

            >>> # Sem chunks expandidos
            >>> context = results.to_context(include_expanded=False)
        """
        parts = []
        total_chars = 0

        # === SEÇÃO 1: EVIDÊNCIA DIRETA ===
        header_direct = "=== EVIDÊNCIA DIRETA (resultados da busca) ==="
        parts.append(header_direct)
        total_chars += len(header_direct) + 1

        for i, hit in enumerate(self.hits, 1):
            entry = f"[{i}] {hit.source}\n{hit.text}"

            # SPEC 1C: nota e jurisprudência acompanham o chunk
            if hit.nota_especialista:
                entry += f"\n[Nota do Especialista]: {hit.nota_especialista}"
            if hit.jurisprudencia_tcu:
                entry += f"\n[Jurisprudência TCU]: {hit.jurisprudencia_tcu}"
                if hit.acordao_tcu_link:
                    entry += f"\n[Link Acórdão]: {hit.acordao_tcu_link}"

            entry += "\n"

            if max_chars and total_chars + len(entry) > max_chars:
                break

            parts.append(entry)
            total_chars += len(entry)

        # === SEÇÃO 2: TRECHOS CITADOS (expansão por citação) ===
        if include_expanded and self.expanded_chunks:
            separator = "\n=== TRECHOS CITADOS (expansão por citação) ==="
            parts.append(separator)
            total_chars += len(separator) + 1

            for j, ec in enumerate(self.expanded_chunks, 1):
                # Informações de rastreabilidade
                source_chunk = ec.source_chunk_id or "(origem não informada)"
                citation_raw = ec.source_citation_raw or "(citação não informada)"
                node_id = ec.node_id or "(node_id não informado)"
                device_type = ec.device_type or "unknown"

                # Monta bloco estruturado
                entry_lines = [
                    f"[XC-{j}] TRECHO CITADO (expansão por citação)",
                    f"  CITADO POR: {source_chunk}",
                    f"  CITAÇÃO ORIGINAL: {citation_raw}",
                    f"  ALVO (node_id): {node_id}",
                    f"  FONTE: {ec.document_id}, {ec.span_id} ({device_type})",
                    f"{ec.text}",
                    "",  # linha em branco entre chunks
                ]
                entry = "\n".join(entry_lines)

                if max_chars and total_chars + len(entry) > max_chars:
                    break

                parts.append(entry)
                total_chars += len(entry)

            # === RESUMO DE ESTATÍSTICAS (opcional) ===
            if include_stats and self.expansion_stats:
                stats = self.expansion_stats
                stats_line = (
                    f"\n[Expansão: encontradas={stats.citations_scanned_count}, "
                    f"resolvidas={stats.citations_resolved_count}, "
                    f"expandidas={stats.expanded_chunks_count}, "
                    f"tempo={stats.expansion_time_ms:.0f}ms]"
                )
                if not max_chars or total_chars + len(stats_line) <= max_chars:
                    parts.append(stats_line)

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
        result = {
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
                    **({"nota_especialista": hit.nota_especialista} if hit.nota_especialista else {}),
                    **({"jurisprudencia_tcu": hit.jurisprudencia_tcu} if hit.jurisprudencia_tcu else {}),
                    **({"acordao_tcu_key": hit.acordao_tcu_key} if hit.acordao_tcu_key else {}),
                    **({"acordao_tcu_link": hit.acordao_tcu_link} if hit.acordao_tcu_link else {}),
                }
                for hit in self.hits
            ],
            "total": self.total,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
            "query_id": self.query_id,
            "mode": self.mode,
        }

        # Adiciona campos de expansão se presentes
        if self.expanded_chunks:
            result["expanded_chunks"] = [
                {
                    "chunk_id": ec.chunk_id,
                    "node_id": ec.node_id,
                    "text": ec.text,
                    "document_id": ec.document_id,
                    "span_id": ec.span_id,
                    "device_type": ec.device_type,
                    "source_chunk_id": ec.source_chunk_id,
                    "source_citation_raw": ec.source_citation_raw,
                }
                for ec in self.expanded_chunks
            ]

        if self.expansion_stats:
            result["expansion_stats"] = {
                "expanded_chunks_count": self.expansion_stats.expanded_chunks_count,
                "citations_scanned_count": self.expansion_stats.citations_scanned_count,
                "citations_resolved_count": self.expansion_stats.citations_resolved_count,
                "expansion_time_ms": self.expansion_stats.expansion_time_ms,
                "skipped_self_references": self.expansion_stats.skipped_self_references,
                "skipped_duplicates": self.expansion_stats.skipped_duplicates,
                "skipped_token_budget": self.expansion_stats.skipped_token_budget,
            }

        return result



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
