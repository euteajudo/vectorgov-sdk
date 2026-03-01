"""
Cliente assíncrono do VectorGov SDK.

Wrapper async sobre VectorGov síncrono usando asyncio.to_thread(),
sem dependências adicionais (não requer httpx/aiohttp).

Uso:
    >>> async with AsyncVectorGov(api_key="vg_xxx") as vg:
    ...     results = await vg.search("O que é ETP?")
    ...     print(results.to_context())
"""

from __future__ import annotations

import asyncio
from typing import Optional, Union

from vectorgov.client import VectorGov
from vectorgov.config import SearchMode
from vectorgov.models import (
    AuditLogsResponse,
    AuditStats,
    DeleteResponse,
    DocumentsResponse,
    EnrichStatus,
    HybridResult,
    IngestStatus,
    LookupResult,
    SearchResult,
    SmartSearchResult,
    StoreResponseResult,
    TokenStats,
    UploadResponse,
)


class AsyncVectorGov:
    """Cliente assíncrono para a API VectorGov.

    Todas as chamadas de rede são executadas em threads via
    ``asyncio.to_thread()``, preservando compatibilidade com
    o event loop sem dependências extras.

    Example:
        >>> async with AsyncVectorGov(api_key="vg_xxx") as vg:
        ...     results = await vg.search("O que é ETP?")
        ...     hybrid = await vg.hybrid("critérios de julgamento")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        default_top_k: int = 5,
        default_mode: Union[SearchMode, str] = SearchMode.BALANCED,
    ):
        self._sync = VectorGov(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            default_top_k=default_top_k,
            default_mode=default_mode,
        )

    # =========================================================================
    # Busca
    # =========================================================================

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: Optional[Union[SearchMode, str]] = None,
        filters: Optional[dict] = None,
        use_cache: Optional[bool] = None,
        document_id_filter: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> SearchResult:
        """Busca assíncrona na base de conhecimento."""
        return await asyncio.to_thread(
            self._sync.search,
            query,
            top_k=top_k,
            mode=mode,
            filters=filters,
            use_cache=use_cache,
            document_id_filter=document_id_filter,
            trace_id=trace_id,
        )

    async def hybrid(
        self,
        query: str,
        top_k: Optional[int] = None,
        collections: Optional[list[str]] = None,
        hops: int = 1,
        graph_expansion: str = "bidirectional",
        token_budget: Optional[int] = None,
        use_cache: Optional[bool] = None,
        trace_id: Optional[str] = None,
    ) -> HybridResult:
        """Busca híbrida assíncrona (Milvus + Neo4j)."""
        return await asyncio.to_thread(
            self._sync.hybrid,
            query,
            top_k=top_k,
            collections=collections,
            hops=hops,
            graph_expansion=graph_expansion,
            token_budget=token_budget,
            use_cache=use_cache,
            trace_id=trace_id,
        )

    async def smart_search(
        self,
        query: str,
        use_cache: bool = False,
        trace_id: Optional[str] = None,
    ) -> SmartSearchResult:
        """Smart search assíncrono (pipeline MOC v4 com Juiz)."""
        return await asyncio.to_thread(
            self._sync.smart_search,
            query,
            use_cache=use_cache,
            trace_id=trace_id,
        )

    async def lookup(
        self,
        reference: str,
        collection: str = "leis_v4",
        include_parent: bool = True,
        include_siblings: bool = True,
        trace_id: Optional[str] = None,
    ) -> LookupResult:
        """Lookup assíncrono de dispositivo normativo."""
        return await asyncio.to_thread(
            self._sync.lookup,
            reference,
            collection=collection,
            include_parent=include_parent,
            include_siblings=include_siblings,
            trace_id=trace_id,
        )

    # =========================================================================
    # Tokens & Feedback
    # =========================================================================

    async def estimate_tokens(
        self,
        content: Union[str, SearchResult],
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> TokenStats:
        """Estima tokens de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.estimate_tokens,
            content,
            query=query,
            system_prompt=system_prompt,
        )

    async def feedback(self, query_id: str, like: bool) -> bool:
        """Envia feedback de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.feedback,
            query_id,
            like,
        )

    async def store_response(
        self,
        query: str,
        answer: str,
        provider: str,
        model: str,
        chunks_used: int = 0,
        latency_ms: float = 0,
        retrieval_ms: float = 0,
        generation_ms: float = 0,
    ) -> StoreResponseResult:
        """Armazena resposta de LLM externo de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.store_response,
            query,
            answer,
            provider,
            model,
            chunks_used=chunks_used,
            latency_ms=latency_ms,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
        )

    # =========================================================================
    # Documentos
    # =========================================================================

    async def list_documents(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> DocumentsResponse:
        """Lista documentos de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.list_documents,
            page=page,
            limit=limit,
        )

    async def upload_pdf(
        self,
        file_path: str,
        tipo_documento: str,
        numero: str,
        ano: int,
    ) -> UploadResponse:
        """Upload de PDF de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.upload_pdf,
            file_path,
            tipo_documento,
            numero,
            ano,
        )

    async def get_ingest_status(self, task_id: str) -> IngestStatus:
        """Status de ingestão de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.get_ingest_status,
            task_id,
        )

    async def delete_document(self, document_id: str) -> DeleteResponse:
        """Deleta documento de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.delete_document,
            document_id,
        )

    # =========================================================================
    # Auditoria
    # =========================================================================

    async def get_audit_logs(
        self,
        limit: int = 50,
        page: int = 1,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> AuditLogsResponse:
        """Lista logs de auditoria de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.get_audit_logs,
            limit=limit,
            page=page,
            severity=severity,
            event_type=event_type,
        )

    async def get_audit_stats(self, days: int = 30) -> AuditStats:
        """Estatísticas de auditoria de forma assíncrona."""
        return await asyncio.to_thread(
            self._sync.get_audit_stats,
            days=days,
        )

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def close(self):
        """Libera recursos."""
        self._sync.close()

    async def aclose(self):
        """Libera recursos de forma assíncrona."""
        self._sync.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()

    def __repr__(self) -> str:
        return f"AsyncVectorGov(base_url='{self._sync._config.base_url}')"
