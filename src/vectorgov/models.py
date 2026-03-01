"""
Modelos de dados do VectorGov SDK.
"""

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from functools import cached_property
from typing import Optional, Iterator, Any, Literal
from datetime import datetime


# =============================================================================
# TOKEN STATS MODEL
# =============================================================================


@dataclass(slots=True)
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


@dataclass(slots=True)
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

    device_type: Optional[str] = None
    """Tipo do dispositivo (article, paragraph, inciso, alinea, article_consolidated)"""

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


@dataclass(slots=True)
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

    page_number: Optional[int] = None
    """Número da página no PDF original (1-indexed)"""

    canonical_hash: Optional[str] = None
    """SHA-256 do texto canônico (para verificação de integridade)"""

    canonical_start: Optional[int] = None
    """Offset de início no texto canônico (para ordenação posicional)"""

    origin_type: Optional[str] = None
    """Proveniência: 'self' (próprio documento) ou outro tipo (referência cruzada)"""

    origin_reference: Optional[str] = None
    """Referência à fonte original se proveniência cruzada (ex: 'Lei 14.133/2021, Art. 75')"""

    origin_reference_name: Optional[str] = None
    """Nome legível do documento de referência (ex: 'Lei 14.133/2021')"""

    is_external_material: bool = False
    """Se este hit é material externo (não pertence à base principal)"""

    theme: Optional[str] = None
    """Tema do dispositivo (curadoria)"""

    stitched_text: Optional[str] = None
    """Texto consolidado (contexto + conteúdo). Prioridade sobre text no XML."""

    pure_rerank_score: Optional[float] = None
    """Score original do reranker, antes de boosts institucionais."""

    parent_node_id: Optional[str] = None
    """node_id do chunk pai (quando hit veio de parent-child expansion)."""

    is_parent: bool = False
    """Se este hit é um chunk pai trazido por expansão."""

    is_sibling: bool = False
    """Se este hit é um irmão do seed."""

    is_child_of_seed: bool = False
    """Se este hit é filho de um seed."""

    evidence_url: Optional[str] = None
    """URL direta para a evidência verificável."""

    document_url: Optional[str] = None
    """URL para o documento fonte."""

    sha256_source: Optional[str] = None
    """SHA-256 do texto fonte (verificação de integridade)."""

    graph_boost_applied: Optional[float] = None
    """Boost aplicado pelo grafo institucional."""

    curation_boost_applied: Optional[float] = None
    """Boost aplicado pela curadoria."""

    # --- Campos unificados (graph_nodes, lookup) ---

    node_id: Optional[str] = None
    """Node ID canônico (ex: leis:LEI-14133-2021#ART-033)"""

    span_id: Optional[str] = None
    """Span ID do dispositivo (ex: ART-033)"""

    document_id: Optional[str] = None
    """ID do documento (ex: LEI-14133-2021)"""

    device_type: Optional[str] = None
    """Tipo: article, paragraph, inciso, alinea"""

    article_number: Optional[str] = None
    """Número do artigo"""

    tipo_documento: Optional[str] = None
    """Tipo do documento (LEI, DECRETO, IN)"""

    hop: Optional[int] = None
    """Distância no grafo em relação ao seed (1 = citação direta)"""

    frequency: Optional[int] = None
    """Frequência de citação no grafo"""

    paths: list = field(default_factory=list)
    """Caminhos no grafo (listas de node_ids)"""

    relacao: Optional[str] = None
    """Tipo de relacionamento (citacao, regulamenta, referencia)"""

    is_current: bool = False
    """Se este hit é o dispositivo consultado (em siblings de lookup)"""

    def __repr__(self) -> str:
        text_preview = self.text[:100] + "..." if len(self.text) > 100 else self.text
        return f"Hit(score={self.score:.3f}, source='{self.source}', text='{text_preview}')"


# =============================================================================
# CITATION EXPANSION (deprecated — backend usa R1 enable_reference_expansion)
# =============================================================================
# ExpandedChunk e CitationExpansionStats removidos em v0.15.0.
# O campo expanded_chunks em SearchResult agora é list[dict] (raw da API).
# A feature real de expansão é automática no pipeline Fênix (Stage 5.5).


@dataclass  # type: ignore[misc]
class BaseResult(ABC):
    """Classe base abstrata para todos os tipos de resultado do SDK.

    Define campos e métodos comuns a SearchResult, HybridResult e LookupResult.
    """

    query: str = ""
    """Query original"""

    total: int = 0
    """Quantidade total de resultados"""

    latency_ms: float = 0.0
    """Tempo de resposta em milissegundos"""

    cached: bool = False
    """Se o resultado veio do cache"""

    query_id: str = ""
    """ID único da query (para feedback)"""

    timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp da busca"""

    _raw_response: Optional[dict] = field(default=None, repr=False)
    """Resposta bruta da API (uso interno para to_dict)"""

    @property
    @abstractmethod
    def endpoint_type(self) -> str:
        """Tipo do endpoint para billing."""
        ...

    @abstractmethod
    def to_xml(self, level: str = "data") -> str:
        """Gera payload XML estruturado para LLMs."""
        ...

    @abstractmethod
    def to_markdown(self) -> str:
        """Gera representação Markdown legível."""
        ...

    def to_dict(self) -> dict:
        """Serialização base — subclasses podem sobrescrever.

        Filtra campos internos (prefixo '_') automaticamente.
        """
        d = asdict(self)
        return {k: v for k, v in d.items() if not k.startswith("_")}


@dataclass
class SearchResult(BaseResult):
    """Resultado completo de uma busca.

    Example:
        >>> result = vg.search("O que é ETP?")
        >>> print(f"Hits: {len(result.hits)}")
        >>> for hit in result:
        ...     print(f"{hit.source}: {hit.text[:100]}...")
    """

    hits: list[Hit] = field(default_factory=list)
    """Lista de resultados encontrados"""

    mode: str = ""
    """Modo de busca utilizado"""

    expanded_chunks: list[dict] = field(default_factory=list)
    """Chunks expandidos via R1 (reference expansion). Dicts raw da API."""

    expansion_stats: Optional[dict] = None
    """Estatísticas de expansão (dict raw da API)."""

    @property
    def endpoint_type(self) -> str:
        """Tipo do endpoint para billing: ``'search'``."""
        return "search"

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
                # Informações de rastreabilidade (ec é dict raw da API)
                source_chunk = ec.get("source_chunk_id") or "(origem não informada)"
                citation_raw = ec.get("source_citation_raw") or "(citação não informada)"
                node_id = ec.get("node_id") or "(node_id não informado)"
                device_type = ec.get("device_type") or "unknown"

                # Monta bloco estruturado
                entry_lines = [
                    f"[XC-{j}] TRECHO CITADO (expansão por citação)",
                    f"  CITADO POR: {source_chunk}",
                    f"  CITAÇÃO ORIGINAL: {citation_raw}",
                    f"  ALVO (node_id): {node_id}",
                    f"  FONTE: {ec.get('document_id', '')}, {ec.get('span_id', '')} ({device_type})",
                    f"{ec.get('text', '')}",
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
                    f"\n[Expansão: encontradas={stats.get('citations_scanned_count', 0)}, "
                    f"resolvidas={stats.get('citations_resolved_count', 0)}, "
                    f"expandidas={stats.get('expanded_chunks_count', 0)}, "
                    f"tempo={stats.get('expansion_time_ms', 0):.0f}ms]"
                )
                if not max_chars or total_chars + len(stats_line) <= max_chars:
                    parts.append(stats_line)

        return "\n".join(parts)

    def to_messages(
        self,
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_context_chars: Optional[int] = None,
        level: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """Converte os resultados em formato de mensagens para chat completions.

        Args:
            query: Pergunta a ser feita (usa self.query se não informado)
            system_prompt: Prompt de sistema customizado
            max_context_chars: Limite de caracteres do contexto
            level: Se informado, usa payload XML estruturado em vez de texto plano.
                Valores: "data", "instructions", "full".

        Returns:
            Lista de mensagens no formato OpenAI/Anthropic

        Example:
            >>> # Legacy (texto plano)
            >>> messages = results.to_messages("O que é ETP?")
            >>> # Novo (XML estruturado)
            >>> messages = results.to_messages("O que é ETP?", level="instructions")
            >>> response = openai.chat.completions.create(messages=messages)
        """
        if level is not None:
            from vectorgov.payload import build_messages_xml
            return build_messages_xml(self, query=query, level=level)

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
        level: Optional[str] = None,
    ) -> str:
        """Converte os resultados em um prompt único (para Gemini e similares).

        Args:
            query: Pergunta a ser feita (usa self.query se não informado)
            system_prompt: Prompt de sistema customizado
            max_context_chars: Limite de caracteres do contexto
            level: Se informado, usa payload XML estruturado em vez de texto plano.
                Valores: "data", "instructions", "full".

        Returns:
            String com o prompt completo

        Example:
            >>> # Legacy (texto plano)
            >>> prompt = results.to_prompt("O que é ETP?")
            >>> # Novo (XML estruturado)
            >>> prompt = results.to_prompt("O que é ETP?", level="full")
            >>> response = model.generate_content(prompt)
        """
        if level is not None:
            from vectorgov.payload import build_prompt_xml
            return build_prompt_xml(self, query=query, level=level)

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
        """Converte o resultado para dicionário.

        Prioriza _raw_response (resposta completa da API) quando disponível,
        caso contrário reconstrói manualmente a partir dos campos.
        """
        if self._raw_response is not None:
            return dict(self._raw_response)

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

        # Adiciona campos de expansão se presentes (já são dicts raw)
        if self.expanded_chunks:
            result["expanded_chunks"] = list(self.expanded_chunks)

        if self.expansion_stats:
            result["expansion_stats"] = dict(self.expansion_stats)

        return result

    # =================================================================
    # XML / Markdown / Schema — novos em v0.14.0
    # =================================================================

    def to_xml(self, level: str = "data") -> str:
        """Gera payload XML estruturado para LLMs.

        Todas as 7 seções de dados estão presentes em todos os níveis.
        A diferença entre níveis é apenas quais instruções são adicionadas.

        Args:
            level: Nível de instrução:
                - "data": só dados (7 seções), sem instruções
                - "instructions": dados + <instrucoes> com 7 regras leves
                - "full": dados + <instrucoes_completas> com anti-alucinação
                    e contrato dinâmico (whitelist de IDs, mapa de evidências)

        Returns:
            String XML pretty-printed.

        Example:
            >>> xml = results.to_xml("full")
            >>> print(xml)
        """
        from vectorgov.payload import build_xml
        return build_xml(self, level=level)

    def to_markdown(self) -> str:
        """Gera representação Markdown legível dos resultados.

        Returns:
            String Markdown formatada.

        Example:
            >>> md = results.to_markdown()
            >>> print(md)
        """
        from vectorgov.payload import build_markdown
        return build_markdown(self)

    def to_response_schema(
        self,
        include_jurisprudencia: bool = False,
        include_observacoes: bool = False,
    ) -> Optional[dict]:
        """Gera JSON Schema para structured output (response_format).

        Retorna wrapper ``{name, strict, schema}`` com schema detalhado
        contendo ``fundamentacao`` (array de afirmações jurídicas) e
        ``dispositivo_id`` com enum restrito aos span IDs presentes nos
        resultados, prevenindo alucinação mecanicamente via constrained decoding.

        Args:
            include_jurisprudencia: Mantido para compatibilidade (no-op).
            include_observacoes: Mantido para compatibilidade (no-op).

        Returns:
            Dict wrapper ``{name, strict, schema}``, ou None se não houver hits.

        Example:
            >>> wrapper = results.to_response_schema()
            >>> response = openai.chat.completions.create(
            ...     model="gpt-4o",
            ...     messages=results.to_messages(level="instructions"),
            ...     response_format={"type": "json_schema", "json_schema": wrapper},
            ... )
        """
        from vectorgov.payload import build_response_schema
        return build_response_schema(
            self,
            include_jurisprudencia=include_jurisprudencia,
            include_observacoes=include_observacoes,
        )

    def to_anthropic_tool_schema(self) -> Optional[dict]:
        """Gera schema no formato Anthropic tool_use para structured output.

        Returns:
            Dict no formato Anthropic tool, ou None se não houver hits.

        Example:
            >>> tool = results.to_anthropic_tool_schema()
            >>> response = anthropic.messages.create(
            ...     model="claude-sonnet-4-20250514",
            ...     messages=[{"role": "user", "content": query}],
            ...     tools=[tool],
            ... )
        """
        from vectorgov.payload import build_anthropic_tool_schema
        return build_anthropic_tool_schema(self)

    # =================================================================
    # Properties de acesso granular — novos em v0.14.0
    # =================================================================

    @cached_property
    def confidence(self) -> float:
        """Score de confiança do resultado (0.0 a 1.0).

        Calculado como média ponderada dos scores (peso = score²),
        com penalidade para poucos hits e bonus para top hit forte.
        """
        from vectorgov.payload import _calculate_confidence
        return _calculate_confidence(self)

    @cached_property
    def normative_trail(self) -> list[str]:
        """Lista deduplicada de fontes normativas dos resultados.

        Example:
            >>> results.normative_trail
            ['LEI 14133/2021', 'IN 65/2021']
        """
        from vectorgov.payload import _extract_normative_trail
        return _extract_normative_trail(self)

    @property
    def query_interpretation(self) -> dict:
        """Interpretação da query pela API (quando disponível via _raw_response).

        Returns:
            Dict com campos como 'original_query', 'rewritten_query',
            'detected_entities', etc. Dict vazio se não disponível.
        """
        if self._raw_response and "query_interpretation" in self._raw_response:
            return dict(self._raw_response["query_interpretation"])
        return {"original_query": self.query}


@dataclass
class SmartSearchResult(SearchResult):
    """Resultado de smart search (pipeline MOC v4 completo).

    Herda todos os campos e métodos de SearchResult, e adiciona
    metadados do Juiz (confiança, raciocínio) e contexto normativo.

    Example:
        >>> r = vg.smart_search("dispensa de licitação por baixo valor")
        >>> print(r.confianca)       # "ALTO", "MEDIO" ou "BAIXO"
        >>> print(r.raciocinio)      # Texto completo do Juiz
        >>> print(r.tentativas)      # 1 ou 2 (se houve retry)
        >>> print(r.normas_presentes) # ["LEI-14.133-2021", "IN-65-2021", ...]
    """

    # Julgamento do Juiz
    confianca: str = ""
    """Nível de confiança do Juiz: 'ALTO', 'MEDIO' ou 'BAIXO'"""

    raciocinio: str = ""
    """Raciocínio completo do Juiz sobre a completude dos resultados"""

    tentativas: int = 1
    """Número de tentativas do pipeline (1 = sem retry, 2 = com retry)"""

    # Contexto normativo
    normas_presentes: list[str] = field(default_factory=list)
    """Lista de document_ids das normas encontradas (ex: ['LEI-14.133-2021', 'IN-65-2021'])"""

    quantidade_normas: int = 0
    """Quantidade de normas distintas presentes nos resultados"""

    relacoes_count: int = 0
    """Quantidade de relações normativas encontradas via grafo"""

    @property
    def endpoint_type(self) -> str:
        return "smart_search"


# =============================================================================
# HYBRID RESULT MODEL
# =============================================================================


@dataclass
class HybridResult(BaseResult):
    """Resultado de busca híbrida (Milvus + Neo4j grafo).

    Combina evidências diretas (busca semântica) com expansão
    via grafo de citações normativas.

    Example:
        >>> result = vg.hybrid("critérios de julgamento")
        >>> print(f"Evidências: {len(result.hits)}")
        >>> print(f"Expandidos: {len(result.graph_nodes)}")
        >>> xml = result.to_xml("full")
    """

    hits: list[Hit] = field(default_factory=list)
    """Evidências diretas da busca semântica (Milvus).

    Alias: ``direct_evidence`` (backward-compatible).
    """

    graph_nodes: list[Hit] = field(default_factory=list)
    """Chunks expandidos via grafo de citações (Neo4j) — agora como Hit.

    Alias: ``graph_expansion`` (backward-compatible).
    """

    stats: dict = field(default_factory=dict)
    """Estatísticas do pipeline (timings, contagens)"""

    confidence: float = 0.0
    """Confiança calculada pelo backend"""

    hyde_used: bool = False
    """Se HyDE (Hypothetical Document Embeddings) foi utilizado"""

    docfilter_active: bool = False
    """Se filtro por documento foi ativado automaticamente"""

    docfilter_detected_doc_id: Optional[str] = None
    """Document ID detectado automaticamente pelo filtro"""

    query_rewrite_active: bool = False
    """Se a query foi reescrita"""

    query_rewrite_clean_query: Optional[str] = None
    """Query limpa após reescrita"""

    query_rewrite_document_id: Optional[str] = None
    """Document ID extraído da query"""

    dual_lane_active: bool = False
    """Se dual-lane (filtrado + livre) foi ativado"""

    dual_lane_filtered_doc: Optional[str] = None
    """Documento filtrado na lane restrita"""

    dual_lane_from_filtered: int = 0
    """Hits vindos da lane filtrada"""

    dual_lane_from_free: int = 0
    """Hits vindos da lane livre"""

    mode: str = "hybrid"
    """Modo de busca utilizado"""

    # --- Backward-compatible properties ---

    @property
    def direct_evidence(self) -> list[Hit]:
        """Alias backward-compatible para ``hits``."""
        return self.hits

    @property
    def graph_expansion(self) -> list[Hit]:
        """Alias backward-compatible para ``graph_nodes``."""
        return self.graph_nodes

    @property
    def search_time_ms(self) -> float:
        """Alias backward-compatible para ``latency_ms``."""
        return self.latency_ms

    @property
    def endpoint_type(self) -> str:
        """Tipo do endpoint para billing: ``'hybrid'``."""
        return "hybrid"

    def __len__(self) -> int:
        return len(self.hits)

    def __iter__(self) -> Iterator[Hit]:
        return iter(self.hits)

    def __getitem__(self, index: int) -> Hit:
        return self.hits[index]

    def __repr__(self) -> str:
        return (
            f"HybridResult(query='{self.query[:50]}...', "
            f"evidence={len(self.hits)}, "
            f"graph={len(self.graph_nodes)}, "
            f"confidence={self.confidence:.3f})"
        )

    @property
    def normative_trail(self) -> list[str]:
        """Lista deduplicada de fontes normativas."""
        seen: set[str] = set()
        trail: list[str] = []
        for hit in self.direct_evidence:
            m = hit.metadata
            doc_type = m.document_type.upper() if m.document_type else "DOC"
            name = f"{doc_type} {m.document_number or '?'}/{m.year or '?'}"
            if name not in seen:
                seen.add(name)
                trail.append(name)
        return trail

    @property
    def query_interpretation(self) -> dict:
        """Interpretação da query pela API (quando disponível via _raw_response).

        Agrega campos de reescrita e filtro em um dict unificado.

        Returns:
            Dict com campos como 'original_query', 'rewritten_query',
            'detected_document_id', etc. Dict mínimo se não disponível.
        """
        if self._raw_response and "query_interpretation" in self._raw_response:
            return dict(self._raw_response["query_interpretation"])
        result: dict[str, Any] = {"original_query": self.query}
        if self.query_rewrite_active and self.query_rewrite_clean_query:
            result["rewritten_query"] = self.query_rewrite_clean_query
        if self.docfilter_detected_doc_id:
            result["detected_document_id"] = self.docfilter_detected_doc_id
        if self.query_rewrite_document_id:
            result["query_rewrite_document_id"] = self.query_rewrite_document_id
        return result

    def to_xml(self, level: str = "data") -> str:
        """Gera payload XML estruturado para LLMs.

        Args:
            level: "data", "instructions" ou "full"

        Returns:
            String XML pretty-printed.
        """
        from vectorgov.payload import build_hybrid_xml
        return build_hybrid_xml(self, level=level)

    def to_messages(
        self,
        query: Optional[str] = None,
        level: str = "instructions",
    ) -> list[dict[str, str]]:
        """Gera lista de mensagens com XML no system e query no user."""
        from vectorgov.payload import build_hybrid_messages_xml
        return build_hybrid_messages_xml(self, query=query, level=level)

    def to_prompt(
        self,
        query: Optional[str] = None,
        level: str = "instructions",
    ) -> str:
        """Gera prompt único com XML + query."""
        from vectorgov.payload import build_hybrid_prompt_xml
        return build_hybrid_prompt_xml(self, query=query, level=level)

    def to_markdown(self) -> str:
        """Gera representação Markdown legível."""
        from vectorgov.payload import build_hybrid_markdown
        return build_hybrid_markdown(self)

    def to_response_schema(self) -> Optional[dict]:
        """Gera JSON Schema para structured output."""
        from vectorgov.payload import build_response_schema, _collect_authorized_ids_from_hits
        authorized_ids = _collect_authorized_ids_from_hits(self.direct_evidence, self.graph_expansion)
        if not authorized_ids:
            return None
        from vectorgov.payload import _build_schema_dict
        return _build_schema_dict(authorized_ids)

    def to_anthropic_tool_schema(self) -> Optional[dict]:
        """Gera schema no formato Anthropic tool_use."""
        wrapper = self.to_response_schema()
        if wrapper is None:
            return None
        return {
            "name": wrapper["name"],
            "description": (
                "Gera uma resposta jurídica fundamentada nos dispositivos legais fornecidos. "
                "Use APENAS as fontes listadas no enum de dispositivo_id."
            ),
            "input_schema": wrapper["schema"],
        }

    def to_dict(self) -> dict[str, Any]:
        """Converte o resultado para dicionário."""
        if self._raw_response is not None:
            return dict(self._raw_response)
        return {
            "query": self.query,
            "direct_evidence": [
                {"text": h.text, "score": h.score, "source": h.source}
                for h in self.hits
            ],
            "graph_expansion": [
                {"chunk_id": h.chunk_id, "text": h.text, "hop": h.hop, "frequency": h.frequency}
                for h in self.graph_nodes
            ],
            "confidence": self.confidence,
            "cached": self.cached,
            "mode": self.mode,
        }

    def to_context(
        self,
        max_chars: Optional[int] = None,
        include_expanded: bool = True,
    ) -> str:
        """Converte em string de contexto estruturado."""
        parts = []
        total_chars = 0

        header = "=== EVIDÊNCIA DIRETA (busca híbrida) ==="
        parts.append(header)
        total_chars += len(header) + 1

        for i, hit in enumerate(self.hits, 1):
            entry = f"[{i}] {hit.source}\n{hit.text}\n"
            if max_chars and total_chars + len(entry) > max_chars:
                break
            parts.append(entry)
            total_chars += len(entry)

        if include_expanded and self.graph_nodes:
            sep = "\n=== EXPANSÃO VIA GRAFO ==="
            parts.append(sep)
            total_chars += len(sep) + 1

            for j, hit in enumerate(self.graph_nodes, 1):
                entry = (
                    f"[G-{j}] {hit.document_id}, {hit.span_id} "
                    f"(hop={hit.hop}, freq={hit.frequency})\n{hit.text}\n"
                )
                if max_chars and total_chars + len(entry) > max_chars:
                    break
                parts.append(entry)
                total_chars += len(entry)

        return "\n".join(parts)


# =============================================================================
# LOOKUP RESULT MODELS
# =============================================================================


@dataclass
class LookupMatch:
    """Deprecated: use Hit instead."""

    node_id: str = ""
    span_id: str = ""
    document_id: str = ""
    text: str = ""
    device_type: str = ""
    article_number: Optional[str] = None
    tipo_documento: Optional[str] = None
    origin_type: Optional[str] = None
    evidence_url: Optional[str] = None

    def __post_init__(self):
        warnings.warn(
            f"{type(self).__name__} será removido em v1.0. Use Hit.",
            DeprecationWarning,
            stacklevel=2,
        )


@dataclass
class LookupParent:
    """Deprecated: use Hit instead."""

    node_id: str = ""
    span_id: str = ""
    text: str = ""
    device_type: str = ""

    def __post_init__(self):
        warnings.warn(
            f"{type(self).__name__} será removido em v1.0. Use Hit.",
            DeprecationWarning,
            stacklevel=2,
        )


@dataclass
class LookupSibling:
    """Deprecated: use Hit instead."""

    span_id: str = ""
    node_id: str = ""
    device_type: str = ""
    text: str = ""
    is_current: bool = False

    def __post_init__(self):
        warnings.warn(
            f"{type(self).__name__} será removido em v1.0. Use Hit.",
            DeprecationWarning,
            stacklevel=2,
        )


@dataclass
class LookupResolved:
    """Deprecated: use dict instead."""

    device_type: Optional[str] = None
    article_number: Optional[str] = None
    paragraph_number: Optional[str] = None
    inciso_number: Optional[str] = None
    alinea_letter: Optional[str] = None
    document_alias: Optional[str] = None
    resolved_document_id: Optional[str] = None
    resolved_span_id: Optional[str] = None

    def __post_init__(self):
        warnings.warn(
            f"{type(self).__name__} será removido em v1.0. Use Hit.",
            DeprecationWarning,
            stacklevel=2,
        )


@dataclass
class LookupCandidate:
    """Candidato para referência ambígua."""

    document_id: str
    """Document ID do candidato"""

    node_id: str
    """Node ID do candidato"""

    text: str
    """Texto do candidato"""

    tipo_documento: Optional[str] = None
    """Tipo do documento"""


@dataclass
class LookupResult(BaseResult):
    """Resultado de lookup de dispositivo normativo.

    O lookup resolve referências textuais (ex: "Art. 33 da Lei 14.133")
    para o dispositivo exato, incluindo contexto hierárquico (pai, irmãos).

    Example:
        >>> result = vg.lookup("Inc. III do Art. 9 da IN 58")
        >>> if result.status == "found":
        ...     print(result.match.text)
        ...     for sibling in result.siblings:
        ...         print(f"  {'>' if sibling.is_current else ' '} {sibling.span_id}")
    """

    status: str = ""
    """Status: 'found', 'not_found', 'ambiguous', 'parse_failed'"""

    message: Optional[str] = None
    """Mensagem informativa"""

    match: Optional[Hit] = None
    """Dispositivo encontrado (quando status=found)"""

    parent: Optional[Hit] = None
    """Chunk pai do dispositivo"""

    siblings: list[Hit] = field(default_factory=list)
    """Dispositivos irmãos na hierarquia"""

    resolved: Optional[dict] = None
    """Componentes parseados da referência"""

    candidates: list[LookupCandidate] = field(default_factory=list)
    """Candidatos (quando status=ambiguous)"""

    @property
    def endpoint_type(self) -> str:
        """Tipo do endpoint para billing: ``'lookup'``."""
        return "lookup"

    @property
    def reference(self) -> str:
        """Alias backward-compatible para query."""
        return self.query

    @reference.setter
    def reference(self, value: str) -> None:
        self.query = value

    @property
    def elapsed_ms(self) -> float:
        """Alias backward-compatible para latency_ms."""
        return self.latency_ms

    @elapsed_ms.setter
    def elapsed_ms(self, value: float) -> None:
        self.latency_ms = value

    def __repr__(self) -> str:
        return f"LookupResult(reference='{self.query}', status='{self.status}')"

    def to_xml(self, level: str = "data") -> str:
        """Gera payload XML estruturado.

        Args:
            level: "data", "instructions" ou "full"

        Returns:
            String XML pretty-printed.
        """
        from vectorgov.payload import build_lookup_xml
        return build_lookup_xml(self, level=level)

    def to_markdown(self) -> str:
        """Gera representação Markdown legível."""
        from vectorgov.payload import build_lookup_markdown
        return build_lookup_markdown(self)

    def to_prompt(
        self,
        query: Optional[str] = None,
        level: str = "instructions",
    ) -> str:
        """Gera prompt único com XML + query para lookup.

        Args:
            query: Pergunta do usuário (usa self.reference se omitido).
            level: Nível de instrução ("data", "instructions", "full").

        Returns:
            String com XML seguido da query.
        """
        from vectorgov.payload import build_lookup_prompt_xml
        return build_lookup_prompt_xml(self, query=query, level=level)

    def to_messages(
        self,
        query: Optional[str] = None,
        level: str = "instructions",
    ) -> list[dict[str, str]]:
        """Gera lista de mensagens com XML no system e query no user.

        Args:
            query: Pergunta do usuário (usa self.reference se omitido).
            level: Nível de instrução ("data", "instructions", "full").

        Returns:
            Lista de dicts no formato OpenAI/Anthropic chat messages.
        """
        from vectorgov.payload import build_lookup_messages_xml
        return build_lookup_messages_xml(self, query=query, level=level)

    def to_response_schema(self) -> Optional[dict]:
        """Gera JSON Schema para structured output.

        Coleta IDs de match, parent e siblings para restringir
        o enum de dispositivo_id, prevenindo alucinação.

        Returns:
            Dict wrapper ``{name, strict, schema}``, ou None se não houver match.
        """
        authorized_ids: list[str] = []
        if self.match:
            authorized_ids.append(self.match.span_id)
        if self.parent and self.parent.span_id not in authorized_ids:
            authorized_ids.append(self.parent.span_id)
        for sib in self.siblings:
            if sib.span_id not in authorized_ids:
                authorized_ids.append(sib.span_id)
        if not authorized_ids:
            return None
        from vectorgov.payload import _build_schema_dict
        return _build_schema_dict(authorized_ids)

    def to_anthropic_tool_schema(self) -> Optional[dict]:
        """Gera schema no formato Anthropic tool_use.

        Returns:
            Dict no formato Anthropic tool, ou None se não houver match.
        """
        wrapper = self.to_response_schema()
        if wrapper is None:
            return None
        return {
            "name": wrapper["name"],
            "description": (
                "Gera uma resposta jurídica fundamentada nos dispositivos legais fornecidos. "
                "Use APENAS as fontes listadas no enum de dispositivo_id."
            ),
            "input_schema": wrapper["schema"],
        }

    def to_dict(self) -> dict[str, Any]:
        """Converte o resultado para dicionário."""
        if self._raw_response is not None:
            return dict(self._raw_response)
        result: dict[str, Any] = {
            "reference": self.query,
            "status": self.status,
            "elapsed_ms": self.latency_ms,
        }
        if self.message:
            result["message"] = self.message
        if self.match:
            result["match"] = {
                "node_id": self.match.node_id,
                "span_id": self.match.span_id,
                "document_id": self.match.document_id,
                "text": self.match.text,
                "device_type": self.match.device_type,
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

    status: str
    """Status atual (ex: pending, processing, completed, failed, queued, cancelled)"""

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

    status: str
    """Status atual (ex: pending, processing, completed, error, not_found, unknown)"""

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
