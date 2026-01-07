"""
Cliente principal do VectorGov SDK.
"""

import os
from typing import Optional, Union

from vectorgov._http import HTTPClient
from vectorgov.config import SDKConfig, SearchMode, MODE_CONFIG, SYSTEM_PROMPTS
from vectorgov.models import SearchResult, Hit, Metadata
from vectorgov.exceptions import ValidationError, AuthError


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
    ) -> SearchResult:
        """Busca informações na base de conhecimento.

        Args:
            query: Texto da consulta
            top_k: Quantidade de resultados (1-20). Default: 5
            mode: Modo de busca (fast, balanced, precise). Default: balanced
            filters: Filtros opcionais:
                - tipo: Tipo do documento (lei, decreto, in, portaria)
                - ano: Ano do documento
                - orgao: Órgão emissor

        Returns:
            SearchResult com os documentos encontrados

        Raises:
            ValidationError: Se os parâmetros forem inválidos
            AuthError: Se a API key for inválida
            RateLimitError: Se exceder o rate limit

        Exemplo:
            >>> results = vg.search("O que é ETP?")
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
        if top_k < 1 or top_k > 20:
            raise ValidationError("top_k deve estar entre 1 e 20", field="top_k")

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

        # Prepara request
        request_data = {
            "query": query,
            "top_k": top_k,
            "use_hyde": mode_config["use_hyde"],
            "use_reranker": mode_config["use_reranker"],
            "use_cache": mode_config["use_cache"],
            "mode": mode.value,
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

        return SearchResult(
            query=query,
            hits=hits,
            total=response.get("total", len(hits)),
            latency_ms=response.get("latency_ms", 0),
            cached=response.get("cached", False),
            query_id=response.get("query_id", ""),
            mode=mode,
        )

    def feedback(self, query_id: str, like: bool) -> bool:
        """Envia feedback sobre um resultado de busca.

        O feedback ajuda a melhorar a qualidade das buscas futuras.

        Args:
            query_id: ID da query (obtido via result.query_id)
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
