"""
Cliente principal do VectorGov SDK.
"""

import os
from typing import Optional, Union

import json
from vectorgov._http import HTTPClient
from vectorgov.config import SDKConfig, SearchMode, MODE_CONFIG, SYSTEM_PROMPTS
from vectorgov.models import SearchResult, Hit, Metadata, TokenStats
from vectorgov.exceptions import ValidationError, AuthError
from vectorgov.integrations import tools as tool_utils


class VectorGov:
    """Cliente principal para acessar a API VectorGov.

    Exemplo de uso básico:
        >>> from vectorgov import VectorGov
        >>> vg = VectorGov(api_key="vg_xxxx")
        >>> results = vg.search("O que é ETP?")
        >>> print(results.to_context())

    Exemplo com OpenAI:
        >>> from openai import OpenAI
        >>> vg = VectorGov(api_key="vg_xxxx")
        >>> openai = OpenAI()
        >>> results = vg.search("Critérios de julgamento")
        >>> response = openai.chat.completions.create(
        ...     model="gpt-4o",
        ...     messages=results.to_messages()
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        default_top_k: int = 5,
        default_mode: Union[SearchMode, str] = SearchMode.BALANCED,
    ):
        """Inicializa o cliente VectorGov.

        Args:
            api_key: Chave de API. Se não informada, usa VECTORGOV_API_KEY do ambiente.
            base_url: URL base da API. Default: https://vectorgov.io/api/v1
            timeout: Timeout em segundos para requisições. Default: 30
            default_top_k: Quantidade padrão de resultados. Default: 5
            default_mode: Modo de busca padrão. Default: balanced

        Raises:
            AuthError: Se a API key não for fornecida
        """
        # Obtém API key do ambiente se não fornecida
        self._api_key = api_key or os.environ.get("VECTORGOV_API_KEY")
        if not self._api_key:
            raise AuthError(
                "API key não fornecida. Passe api_key no construtor ou "
                "defina a variável de ambiente VECTORGOV_API_KEY"
            )

        # Valida formato da API key
        if not self._api_key.startswith("vg_"):
            raise AuthError(
                "Formato de API key inválido. A key deve começar com 'vg_'"
            )

        # Configurações
        self._config = SDKConfig(
            base_url=base_url or "https://vectorgov.io/api/v1",
            timeout=timeout,
            default_top_k=default_top_k,
            default_mode=SearchMode(default_mode) if isinstance(default_mode, str) else default_mode,
        )

        # Cliente HTTP
        self._http = HTTPClient(
            base_url=self._config.base_url,
            api_key=self._api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
            retry_delay=self._config.retry_delay,
        )

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: Optional[Union[SearchMode, str]] = None,
        filters: Optional[dict] = None,
        use_cache: Optional[bool] = None,
        expand_citations: bool = False,
        citation_expansion_top_n: int = 3,
    ) -> SearchResult:
        """Busca informações na base de conhecimento.

        Args:
            query: Texto da consulta
            top_k: Quantidade de resultados (1-50). Default: 5
            mode: Modo de busca (fast, balanced, precise). Default: balanced
            filters: Filtros opcionais:
                - tipo: Tipo do documento (lei, decreto, in, portaria)
                - ano: Ano do documento
                - orgao: Órgão emissor
            use_cache: Usar cache compartilhado. Default: False (privacidade).
                ATENÇÃO: O cache é compartilhado entre todos os clientes.
                Se True, sua pergunta/resposta pode ser vista por outros clientes
                e você pode receber respostas de perguntas de outros clientes.
                Habilite apenas se aceitar o trade-off privacidade vs latência.
            expand_citations: Se True, expande citações normativas encontradas nos
                resultados (ex: "art. 18 da Lei 14.133"). Chunks citados são
                automaticamente recuperados e adicionados ao contexto.
                Default: False
            citation_expansion_top_n: Número máximo de citações a expandir por chunk.
                Default: 3

        Returns:
            SearchResult com os documentos encontrados. Se expand_citations=True,
            inclui `expanded_chunks` e `expansion_stats`.

        Raises:
            ValidationError: Se os parâmetros forem inválidos
            AuthError: Se a API key for inválida
            RateLimitError: Se exceder o rate limit

        Exemplo:
            >>> # Busca privada (padrão)
            >>> results = vg.search("O que é ETP?")
            >>>
            >>> # Busca com cache (aceita compartilhamento)
            >>> results = vg.search("O que é ETP?", use_cache=True)
            >>>
            >>> # Busca com expansão de citações
            >>> results = vg.search("O que é ETP?", expand_citations=True)
            >>> print(f"Chunks expandidos: {len(results.expanded_chunks)}")
            >>>
            >>> for hit in results:
            ...     print(f"{hit.source}: {hit.text[:100]}...")
        """
        # Validações
        if not query or not query.strip():
            raise ValidationError("Query não pode ser vazia", field="query")

        query = query.strip()
        if len(query) < 3:
            raise ValidationError("Query deve ter pelo menos 3 caracteres", field="query")

        if len(query) > 1000:
            raise ValidationError("Query deve ter no máximo 1000 caracteres", field="query")

        # Valores padrão
        top_k = top_k or self._config.default_top_k
        if top_k < 1 or top_k > 50:
            raise ValidationError("top_k deve estar entre 1 e 50", field="top_k")

        mode = mode or self._config.default_mode
        if isinstance(mode, str):
            try:
                mode = SearchMode(mode)
            except ValueError:
                raise ValidationError(
                    f"Modo inválido: {mode}. Use: fast, balanced ou precise",
                    field="mode",
                )

        # Obtém configuração do modo
        mode_config = MODE_CONFIG[mode]

        # Determina se usa cache
        # Se o desenvolvedor passou explicitamente, usa o valor dele
        # Senão, usa o padrão do modo (que é False por privacidade)
        cache_enabled = use_cache if use_cache is not None else mode_config["use_cache"]

        # Prepara request
        request_data = {
            "query": query,
            "top_k": top_k,
            "use_hyde": mode_config["use_hyde"],
            "use_reranker": mode_config["use_reranker"],
            "use_cache": cache_enabled,
            "mode": mode.value,
            "expand_citations": expand_citations,
            "citation_expansion_top_n": citation_expansion_top_n,
        }

        # Adiciona filtros se fornecidos
        if filters:
            if "tipo" in filters:
                request_data["tipo_documento"] = filters["tipo"]
            if "ano" in filters:
                request_data["ano"] = filters["ano"]
            if "orgao" in filters:
                request_data["orgao"] = filters["orgao"]

        # Faz requisição
        response = self._http.post("/sdk/search", data=request_data)

        # Converte resposta
        return self._parse_search_response(query, response, mode.value)

    def _parse_search_response(
        self,
        query: str,
        response: dict,
        mode: str,
    ) -> SearchResult:
        """Converte resposta da API em SearchResult."""
        from vectorgov.models import ExpandedChunk, CitationExpansionStats

        hits = []
        for item in response.get("hits", []):
            metadata = Metadata(
                document_type=item.get("tipo_documento", ""),
                document_number=item.get("numero", ""),
                year=item.get("ano", 0),
                article=item.get("article_number"),
                paragraph=item.get("paragraph"),
                item=item.get("inciso"),
                orgao=item.get("orgao"),
            )

            hit = Hit(
                text=item.get("text", ""),
                score=item.get("score", 0.0),
                source=item.get("source", str(metadata)),
                metadata=metadata,
                chunk_id=item.get("chunk_id"),
                context=item.get("context_header"),
            )
            hits.append(hit)

        # Parse expanded_chunks se presente
        expanded_chunks = []
        for ec in response.get("expanded_chunks", []):
            expanded_chunks.append(ExpandedChunk(
                chunk_id=ec.get("chunk_id", ""),
                node_id=ec.get("node_id", ""),
                text=ec.get("text", ""),
                document_id=ec.get("document_id", ""),
                span_id=ec.get("span_id", ""),
                device_type=ec.get("device_type", "article"),
                source_chunk_id=ec.get("source_chunk_id", ""),
                source_citation_raw=ec.get("source_citation_raw", ""),
            ))

        # Parse expansion_stats se presente
        expansion_stats = None
        if "expansion_stats" in response and response["expansion_stats"]:
            es = response["expansion_stats"]
            expansion_stats = CitationExpansionStats(
                expanded_chunks_count=es.get("expanded_chunks_count", 0),
                citations_scanned_count=es.get("citations_scanned_count", 0),
                citations_resolved_count=es.get("citations_resolved_count", 0),
                expansion_time_ms=es.get("expansion_time_ms", 0.0),
                skipped_self_references=es.get("skipped_self_references", 0),
                skipped_duplicates=es.get("skipped_duplicates", 0),
                skipped_token_budget=es.get("skipped_token_budget", 0),
            )

        return SearchResult(
            query=query,
            hits=hits,
            total=response.get("total", len(hits)),
            latency_ms=response.get("latency_ms", 0),
            cached=response.get("cached", False),
            query_id=response.get("query_id", ""),
            mode=mode,
            expanded_chunks=expanded_chunks,
            expansion_stats=expansion_stats,
        )

    def feedback(self, query_id: str, like: bool) -> bool:
        """Envia feedback sobre um resultado de busca.

        O feedback ajuda a melhorar a qualidade das buscas futuras.

        Args:
            query_id: ID da query (obtido via result.query_id ou store_response().query_hash)
            like: True para positivo, False para negativo

        Returns:
            True se o feedback foi registrado com sucesso

        Exemplo:
            >>> results = vg.search("O que é ETP?")
            >>> # Após verificar que o resultado foi útil:
            >>> vg.feedback(results.query_id, like=True)
        """
        if not query_id:
            raise ValidationError("query_id não pode ser vazio", field="query_id")

        response = self._http.post(
            "/sdk/feedback",
            data={"query_id": query_id, "is_like": like},
        )
        return response.get("success", False)

    def estimate_tokens(
        self,
        content: Union[str, "SearchResult"],
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> "TokenStats":
        """Estima o número de tokens de um texto ou resultado de busca.

        A contagem é feita no servidor usando tiktoken, garantindo precisão
        sem dependências extras no cliente.

        Args:
            content: Texto para contar tokens, ou SearchResult para calcular
                     tokens do contexto completo (to_messages)
            query: Pergunta a ser usada (apenas se content for SearchResult).
                   Se não informado, usa a query original do SearchResult.
            system_prompt: Prompt de sistema customizado

        Returns:
            TokenStats com contagem detalhada de tokens

        Raises:
            ValidationError: Se os parâmetros forem inválidos

        Exemplo com texto simples:
            >>> stats = vg.estimate_tokens("Texto para contar tokens")
            >>> print(f"Total: {stats.total_tokens} tokens")

        Exemplo com SearchResult:
            >>> results = vg.search("O que é ETP?")
            >>> stats = vg.estimate_tokens(results)
            >>> print(f"Contexto: {stats.context_tokens} tokens")
            >>> print(f"Total: {stats.total_tokens} tokens")
            >>>
            >>> # Verificar se cabe na janela de contexto
            >>> if stats.total_tokens > 128000:
            ...     print("Excede limite do GPT-4!")

        Exemplo com system prompt customizado:
            >>> stats = vg.estimate_tokens(
            ...     results,
            ...     system_prompt=vg.get_system_prompt("detailed")
            ... )
        """
        from vectorgov.models import TokenStats, SearchResult as SearchResultClass

        # Se for SearchResult, extrai contexto formatado
        if isinstance(content, SearchResultClass):
            query = query or content.query
            context = content.to_context()
            hits_count = len(content.hits)
        else:
            # É uma string simples
            if not content or not str(content).strip():
                raise ValidationError("content não pode ser vazio", field="content")
            context = str(content)
            hits_count = 0
            query = query or ""

        # Monta o request
        request_data = {
            "context": context,
            "query": query,
            "system_prompt": system_prompt or "",
        }

        # Chama a API
        response = self._http.post("/sdk/tokens", data=request_data)

        return TokenStats(
            context_tokens=response.get("context_tokens", 0),
            system_tokens=response.get("system_tokens", 0),
            query_tokens=response.get("query_tokens", 0),
            total_tokens=response.get("total_tokens", 0),
            hits_count=hits_count,
            char_count=response.get("char_count", len(context)),
            encoding=response.get("encoding", "cl100k_base"),
        )

    def store_response(
        self,
        query: str,
        answer: str,
        provider: str,
        model: str,
        chunks_used: int = 0,
        latency_ms: float = 0,
        retrieval_ms: float = 0,
        generation_ms: float = 0,
    ) -> "StoreResponseResult":
        """Armazena resposta de LLM externo no cache do VectorGov.

        Use este método quando você gera uma resposta usando seu próprio LLM
        (OpenAI, Gemini, Claude, etc.) e quer:
        1. Habilitar o sistema de feedback (like/dislike)
        2. Contribuir para o treinamento de modelos futuros

        Args:
            query: A pergunta original feita pelo usuário
            answer: A resposta gerada pelo seu LLM
            provider: Nome do provedor (ex: "OpenAI", "Google", "Anthropic")
            model: ID do modelo usado (ex: "gpt-4o", "gemini-2.0-flash")
            chunks_used: Quantidade de chunks usados como contexto
            latency_ms: Latência total em ms (busca + geração)
            retrieval_ms: Tempo de busca em ms
            generation_ms: Tempo de geração do LLM em ms

        Returns:
            StoreResponseResult com o query_hash para usar em feedback()

        Exemplo:
            >>> from openai import OpenAI
            >>> vg = VectorGov(api_key="vg_xxx")
            >>> openai_client = OpenAI()
            >>>
            >>> # 1. Busca no VectorGov
            >>> results = vg.search("O que é ETP?")
            >>>
            >>> # 2. Gera resposta com seu LLM
            >>> response = openai_client.chat.completions.create(
            ...     model="gpt-4o",
            ...     messages=results.to_messages()
            ... )
            >>> answer = response.choices[0].message.content
            >>>
            >>> # 3. Salva a resposta no VectorGov para feedback
            >>> stored = vg.store_response(
            ...     query="O que é ETP?",
            ...     answer=answer,
            ...     provider="OpenAI",
            ...     model="gpt-4o",
            ...     chunks_used=len(results)
            ... )
            >>>
            >>> # 4. Depois o usuário pode dar feedback
            >>> vg.feedback(stored.query_hash, like=True)
        """
        from vectorgov.models import StoreResponseResult

        if not query or not query.strip():
            raise ValidationError("query não pode ser vazia", field="query")

        if not answer or not answer.strip():
            raise ValidationError("answer não pode ser vazia", field="answer")

        if not provider or not provider.strip():
            raise ValidationError("provider não pode ser vazio", field="provider")

        if not model or not model.strip():
            raise ValidationError("model não pode ser vazio", field="model")

        response = self._http.post(
            "/cache/store",
            data={
                "query": query.strip(),
                "answer": answer.strip(),
                "provider": provider.strip(),
                "model": model.strip(),
                "chunks_used": chunks_used,
                "latency_ms": latency_ms,
                "retrieval_ms": retrieval_ms,
                "generation_ms": generation_ms,
            },
        )

        return StoreResponseResult(
            success=response.get("success", False),
            query_hash=response.get("query_hash", ""),
            message=response.get("message", ""),
        )

    def get_system_prompt(self, style: str = "default") -> str:
        """Retorna um system prompt pré-definido.

        Args:
            style: Estilo do prompt (default, concise, detailed, chatbot)

        Returns:
            String com o system prompt

        Exemplo:
            >>> prompt = vg.get_system_prompt("detailed")
            >>> messages = results.to_messages(system_prompt=prompt)
        """
        return SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["default"])

    @property
    def available_prompts(self) -> list[str]:
        """Lista os estilos de system prompt disponíveis."""
        return list(SYSTEM_PROMPTS.keys())

    def __repr__(self) -> str:
        return f"VectorGov(base_url='{self._config.base_url}')"

    # =========================================================================
    # Métodos de Integração com Function Calling
    # =========================================================================

    def to_openai_tool(self) -> dict:
        """Retorna a ferramenta VectorGov no formato OpenAI Function Calling.

        Returns:
            Dicionário com a definição da ferramenta

        Exemplo:
            >>> from openai import OpenAI
            >>> vg = VectorGov(api_key="vg_xxx")
            >>> client = OpenAI()
            >>>
            >>> response = client.chat.completions.create(
            ...     model="gpt-4o",
            ...     messages=[{"role": "user", "content": "O que é ETP?"}],
            ...     tools=[vg.to_openai_tool()],
            ... )
        """
        return tool_utils.to_openai_tool()

    def to_anthropic_tool(self) -> dict:
        """Retorna a ferramenta VectorGov no formato Anthropic Claude Tools.

        Returns:
            Dicionário com a definição da ferramenta

        Exemplo:
            >>> from anthropic import Anthropic
            >>> vg = VectorGov(api_key="vg_xxx")
            >>> client = Anthropic()
            >>>
            >>> response = client.messages.create(
            ...     model="claude-sonnet-4-20250514",
            ...     messages=[{"role": "user", "content": "O que é ETP?"}],
            ...     tools=[vg.to_anthropic_tool()],
            ... )
        """
        return tool_utils.to_anthropic_tool()

    def to_google_tool(self) -> dict:
        """Retorna a ferramenta VectorGov no formato Google Gemini Function Calling.

        Returns:
            Dicionário com a definição da ferramenta

        Exemplo:
            >>> import google.generativeai as genai
            >>> vg = VectorGov(api_key="vg_xxx")
            >>>
            >>> model = genai.GenerativeModel(
            ...     model_name="gemini-2.0-flash",
            ...     tools=[vg.to_google_tool()],
            ... )
        """
        return tool_utils.to_google_tool()

    def execute_tool_call(
        self,
        tool_call: any,
        mode: Optional[Union[SearchMode, str]] = None,
    ) -> str:
        """Executa uma chamada de ferramenta e retorna o resultado formatado.

        Este método aceita tool_calls de OpenAI, Anthropic ou Gemini e executa
        a busca apropriada.

        Args:
            tool_call: Objeto de tool_call do LLM (OpenAI, Anthropic ou dict)
            mode: Modo de busca opcional (fast, balanced, precise)

        Returns:
            String formatada com os resultados para passar de volta ao LLM

        Exemplo com OpenAI:
            >>> response = client.chat.completions.create(...)
            >>> if response.choices[0].message.tool_calls:
            ...     tool_call = response.choices[0].message.tool_calls[0]
            ...     result = vg.execute_tool_call(tool_call)
            ...     # Passa 'result' de volta para o LLM na próxima mensagem

        Exemplo com Anthropic:
            >>> response = client.messages.create(...)
            >>> for block in response.content:
            ...     if block.type == "tool_use":
            ...         result = vg.execute_tool_call(block)
        """
        # Extrai argumentos dependendo do tipo de tool_call
        arguments = self._extract_tool_arguments(tool_call)

        # Parseia argumentos
        query, filters, top_k = tool_utils.parse_tool_arguments(arguments)

        # Executa busca
        result = self.search(query=query, top_k=top_k, mode=mode, filters=filters)

        # Formata resposta
        return tool_utils.format_tool_response(result)

    def _extract_tool_arguments(self, tool_call: any) -> dict:
        """Extrai argumentos de diferentes formatos de tool_call."""
        # OpenAI format
        if hasattr(tool_call, "function") and hasattr(tool_call.function, "arguments"):
            args = tool_call.function.arguments
            return json.loads(args) if isinstance(args, str) else args

        # Anthropic format
        if hasattr(tool_call, "input"):
            return tool_call.input if isinstance(tool_call.input, dict) else {}

        # Dict format (Gemini ou manual)
        if isinstance(tool_call, dict):
            if "function" in tool_call and "arguments" in tool_call["function"]:
                args = tool_call["function"]["arguments"]
                return json.loads(args) if isinstance(args, str) else args
            if "args" in tool_call:
                return tool_call["args"]
            return tool_call

        raise ValueError(
            f"Formato de tool_call não reconhecido: {type(tool_call)}. "
            "Esperado: OpenAI ChatCompletionMessageToolCall, Anthropic ToolUseBlock, ou dict"
        )

    # =========================================================================
    # Metodos de Gerenciamento de Documentos
    # =========================================================================

    def list_documents(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> "DocumentsResponse":
        from vectorgov.models import DocumentSummary, DocumentsResponse

        if limit < 1 or limit > 100:
            raise ValidationError("limit deve estar entre 1 e 100", field="limit")

        response = self._http.get("/sdk/documents", params={"page": page, "limit": limit})

        documents = [
            DocumentSummary(
                document_id=doc["document_id"],
                tipo_documento=doc["tipo_documento"],
                numero=doc["numero"],
                ano=doc["ano"],
                titulo=doc.get("titulo"),
                descricao=doc.get("descricao"),
                chunks_count=doc.get("chunks_count", 0),
                enriched_count=doc.get("enriched_count", 0),
            )
            for doc in response.get("documents", [])
        ]

        return DocumentsResponse(
            documents=documents,
            total=response.get("total", len(documents)),
            page=response.get("page", page),
            pages=response.get("pages", 1),
        )

    def get_document(self, document_id: str) -> "DocumentSummary":
        from vectorgov.models import DocumentSummary

        if not document_id or not document_id.strip():
            raise ValidationError("document_id nao pode ser vazio", field="document_id")

        response = self._http.get(f"/sdk/documents/{document_id}")

        return DocumentSummary(
            document_id=response["document_id"],
            tipo_documento=response["tipo_documento"],
            numero=response["numero"],
            ano=response["ano"],
            titulo=response.get("titulo"),
            descricao=response.get("descricao"),
            chunks_count=response.get("chunks_count", 0),
            enriched_count=response.get("enriched_count", 0),
        )

    def upload_pdf(self, file_path: str, tipo_documento: str, numero: str, ano: int) -> "UploadResponse":
        from vectorgov.models import UploadResponse
        import os as _os

        if not _os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        if not file_path.lower().endswith(".pdf"):
            raise ValidationError("Apenas arquivos PDF sao aceitos", field="file_path")

        valid_types = ["LEI", "DECRETO", "IN", "PORTARIA", "RESOLUCAO"]
        tipo_documento = tipo_documento.upper()
        if tipo_documento not in valid_types:
            raise ValidationError(f"tipo_documento invalido", field="tipo_documento")

        if not numero:
            raise ValidationError("numero nao pode ser vazio", field="numero")

        if ano < 1900 or ano > 2100:
            raise ValidationError("ano invalido", field="ano")

        with open(file_path, "rb") as f:
            files = {"file": (_os.path.basename(file_path), f, "application/pdf")}
            data = {"tipo_documento": tipo_documento, "numero": numero, "ano": str(ano)}
            response = self._http.post_multipart("/sdk/documents/upload", files=files, data=data)

        return UploadResponse(
            success=response.get("success", True),
            message=response.get("message", "Upload iniciado"),
            document_id=response.get("document_id", ""),
            task_id=response.get("task_id", ""),
        )

    def get_ingest_status(self, task_id: str) -> "IngestStatus":
        from vectorgov.models import IngestStatus

        if not task_id or not task_id.strip():
            raise ValidationError("task_id nao pode ser vazio", field="task_id")

        response = self._http.get(f"/sdk/ingest/status/{task_id}")

        return IngestStatus(
            task_id=task_id,
            status=response.get("status", "unknown"),
            progress=response.get("progress", 0),
            message=response.get("message", ""),
            document_id=response.get("document_id"),
            chunks_created=response.get("chunks_created", 0),
        )

    def start_enrichment(self, document_id: str) -> dict:
        if not document_id or not document_id.strip():
            raise ValidationError("document_id nao pode ser vazio", field="document_id")

        response = self._http.post("/sdk/documents/enrich", data={"document_id": document_id})
        return {"task_id": response.get("task_id", ""), "message": response.get("message", "")}

    def get_enrichment_status(self, task_id: str) -> "EnrichStatus":
        from vectorgov.models import EnrichStatus

        if not task_id or not task_id.strip():
            raise ValidationError("task_id nao pode ser vazio", field="task_id")

        response = self._http.get(f"/sdk/enrich/status/{task_id}")

        return EnrichStatus(
            task_id=task_id,
            status=response.get("status", "unknown"),
            progress=response.get("progress", 0.0),
            chunks_enriched=response.get("chunks_enriched", 0),
            chunks_pending=response.get("chunks_pending", 0),
            chunks_failed=response.get("chunks_failed", 0),
            errors=response.get("errors", []),
        )

    def delete_document(self, document_id: str) -> "DeleteResponse":
        from vectorgov.models import DeleteResponse

        if not document_id or not document_id.strip():
            raise ValidationError("document_id nao pode ser vazio", field="document_id")

        response = self._http.delete(f"/sdk/documents/{document_id}")

        return DeleteResponse(
            success=response.get("success", False),
            message=response.get("message", ""),
        )

    # =========================================================================
    # Métodos de Auditoria
    # =========================================================================

    def get_audit_logs(
        self,
        limit: int = 50,
        page: int = 1,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        event_category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> "AuditLogsResponse":
        """Obtém logs de auditoria do seu uso da API.

        Cada chamada à SDK gera eventos de auditoria que podem ser
        consultados para análise de segurança, debugging e compliance.

        IMPORTANTE: Você só tem acesso aos seus próprios logs de auditoria.
        Logs de outros clientes não são visíveis.

        Args:
            limit: Quantidade máxima de logs por página (1-100). Default: 50
            page: Página de resultados. Default: 1
            severity: Filtrar por severidade (info, warning, critical)
            event_type: Filtrar por tipo de evento (pii_detected, injection_detected, etc.)
            event_category: Filtrar por categoria (security, performance, validation)
            start_date: Data inicial (ISO 8601: "2025-01-01")
            end_date: Data final (ISO 8601: "2025-01-31")

        Returns:
            AuditLogsResponse com a lista de logs e metadados de paginação

        Raises:
            ValidationError: Se os parâmetros forem inválidos
            AuthError: Se a API key for inválida

        Exemplo:
            >>> logs = vg.get_audit_logs(limit=10, severity="warning")
            >>> for log in logs.logs:
            ...     print(f"{log.event_type}: {log.query_text}")
        """
        from vectorgov.models import AuditLog, AuditLogsResponse

        if limit < 1 or limit > 100:
            raise ValidationError("limit deve estar entre 1 e 100", field="limit")

        if page < 1:
            raise ValidationError("page deve ser maior que 0", field="page")

        if severity and severity not in ("info", "warning", "critical"):
            raise ValidationError(
                "severity deve ser: info, warning ou critical",
                field="severity",
            )

        if event_category and event_category not in ("security", "performance", "validation"):
            raise ValidationError(
                "event_category deve ser: security, performance ou validation",
                field="event_category",
            )

        # Monta parâmetros
        params = {"limit": limit, "page": page}
        if severity:
            params["severity"] = severity
        if event_type:
            params["event_type"] = event_type
        if event_category:
            params["event_category"] = event_category
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self._http.get("/sdk/audit/logs", params=params)

        logs = [
            AuditLog(
                id=log["id"],
                event_type=log["event_type"],
                event_category=log["event_category"],
                severity=log["severity"],
                query_text=log.get("query_text"),
                detection_types=log.get("detection_types", []),
                risk_score=log.get("risk_score"),
                action_taken=log.get("action_taken"),
                endpoint=log.get("endpoint"),
                client_ip=log.get("client_ip"),
                created_at=log.get("created_at"),
                details=log.get("details", {}),
            )
            for log in response.get("logs", [])
        ]

        return AuditLogsResponse(
            logs=logs,
            total=response.get("total", len(logs)),
            page=response.get("page", page),
            pages=response.get("pages", 1),
            limit=response.get("limit", limit),
        )

    def get_audit_stats(self, days: int = 30) -> "AuditStats":
        """Obtém estatísticas agregadas de auditoria.

        Fornece uma visão geral dos eventos de auditoria em um período,
        útil para dashboards de monitoramento e análise de tendências.

        IMPORTANTE: As estatísticas são apenas dos seus próprios eventos.

        Args:
            days: Período em dias para as estatísticas (1-90). Default: 30

        Returns:
            AuditStats com contagens por tipo, severidade e categoria

        Raises:
            ValidationError: Se days for inválido
            AuthError: Se a API key for inválida

        Exemplo:
            >>> stats = vg.get_audit_stats(days=7)
            >>> print(f"Eventos: {stats.total_events}")
            >>> print(f"Bloqueados: {stats.blocked_count}")
            >>> print(f"Por tipo: {stats.events_by_type}")
        """
        from vectorgov.models import AuditStats

        if days < 1 or days > 90:
            raise ValidationError("days deve estar entre 1 e 90", field="days")

        response = self._http.get("/sdk/audit/stats", params={"days": days})

        return AuditStats(
            total_events=response.get("total_events", 0),
            events_by_type=response.get("events_by_type", {}),
            events_by_severity=response.get("events_by_severity", {}),
            events_by_category=response.get("events_by_category", {}),
            blocked_count=response.get("blocked_count", 0),
            warning_count=response.get("warning_count", 0),
            period_days=response.get("period_days", days),
        )

    def get_audit_event_types(self) -> list[str]:
        """Lista os tipos de eventos de auditoria disponíveis.

        Returns:
            Lista de strings com os tipos de evento

        Exemplo:
            >>> types = vg.get_audit_event_types()
            >>> print(types)  # ['pii_detected', 'injection_detected', ...]
        """
        response = self._http.get("/sdk/audit/event-types")
        return response.get("types", [])
