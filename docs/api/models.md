# Modelos e Exceções — Referência Completa

> Atualizado para v0.15.2 (Março 2026)

## Resultados de Busca

### `BaseResult` (ABC)

Classe base abstrata para todos os tipos de resultado. Não instanciada diretamente.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `query` | `str` | Query original |
| `total` | `int` | Quantidade total de resultados |
| `latency_ms` | `float` | Tempo de resposta (ms) |
| `cached` | `bool` | Se veio do cache |
| `query_id` | `str` | ID para feedback |
| `timestamp` | `datetime` | Timestamp da busca |

**Métodos de formatação (todos os resultados):**

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `to_context(max_chars, include_expanded, include_stats)` | `str` | Contexto formatado para LLMs |
| `to_messages(query, system_prompt, max_context_chars)` | `list[dict]` | Messages prontas para OpenAI/Anthropic |
| `to_prompt(query, system_prompt)` | `str` | Prompt completo (system + context + query) |
| `to_xml(level)` | `str` | Payload XML estruturado |
| `to_markdown()` | `str` | Markdown legível |
| `to_dict()` | `dict` | Serialização para JSON |

**Iteração:** Todos os resultados suportam `for hit in result`, `len(result)`, `result[0]`.

---

### `SearchResult`

Retornado por `vg.search()`.

```python
result = vg.search("O que é ETP?")
print(result.total)       # 5
print(result.mode)        # "balanced"
for hit in result:
    print(hit.source, hit.score)
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `hits` | `list[Hit]` | Lista de resultados |
| `mode` | `str` | Modo usado (fast/balanced/precise) |
| + campos de `BaseResult` | | |

---

### `SmartSearchResult` <sup>v0.15.0</sup>

Retornado por `vg.smart_search()`. Herda `SearchResult`.

```python
result = vg.smart_search("Hipóteses de dispensa")
print(result.confianca)        # "ALTO"
print(result.raciocinio[:200]) # Análise jurídica
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `raciocinio` | `str` | Análise jurídica completa do Juiz |
| `confianca` | `str` | `ALTO`, `MEDIO` ou `BAIXO` |
| `normas_presentes` | `list[str]` | Normas identificadas |
| `tentativas` | `int` | Quantas tentativas o pipeline fez (1 ou 2) |
| + campos de `SearchResult` | | |

---

### `HybridResult` <sup>v0.15.0</sup>

Retornado por `vg.hybrid()`. Herda `BaseResult`.

```python
result = vg.hybrid("critérios de julgamento", hops=2)
for hit in result.direct_evidence:
    print(f"[DIRETO] {hit.source}")
for node in result.graph_expansion:
    print(f"[GRAFO] hop={node['hop']}")
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `direct_evidence` | `list[Hit]` | Resultados da busca semântica |
| `graph_expansion` | `list[dict]` | Nós expandidos via grafo (hop, frequency, paths, text) |
| `stats` | `dict` | Estatísticas (seeds_count, graph_nodes, total_tokens, truncated) |
| + campos de `BaseResult` | | |

---

### `LookupResult` <sup>v0.15.0</sup>

Retornado por `vg.lookup()`. Herda `BaseResult`.

```python
result = vg.lookup("Art. 75 da Lei 14.133/2021")
print(result.status)  # "found"
match = result.matches[0]
print(match.text[:100])
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `status` | `str` | `found`, `not_found`, `ambiguous`, `parse_failed` |
| `matches` | `list[LookupMatch]` | Dispositivos encontrados |
| + campos de `BaseResult` | | |

---

## Hits e Matches

### `Hit`

Resultado individual de uma busca semântica.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `text` | `str` | Texto do dispositivo |
| `score` | `float` | Score de relevância (0.0 a 1.0) |
| `source` | `str` | Referência legível ("Lei 14.133/2021, Art. 75") |
| `document_id` | `str` | ID do documento ("LEI-14133-2021") |
| `span_id` | `str` | ID do span ("ART-075") |
| `node_id` | `str` | ID completo ("leis:LEI-14133-2021#ART-075") |
| `device_type` | `str` | article, paragraph, inciso, alinea |
| `metadata` | `Metadata` | Metadados adicionais |
| `nota_especialista` | `str\|None` | Nota do especialista (smart_search) |
| `jurisprudencia_tcu` | `str\|None` | Jurisprudência TCU vinculada |
| `acordao_tcu_link` | `str\|None` | Link do acórdão TCU |
| `evidence_url` | `str\|None` | URL do trecho com destaque (30min) |
| `document_url` | `str\|None` | URL do PDF original |

### `LookupMatch` <sup>v0.15.0</sup>

Resultado de uma consulta por referência.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `text` | `str` | Texto completo (caput + filhos) |
| `document_id` | `str` | ID do documento |
| `span_id` | `str` | ID do span |
| `node_id` | `str` | ID completo |
| `evidence` | `dict\|None` | `{highlight_url, pdf_url, page_number}` |
| `parent` | `dict\|None` | Artigo pai |
| `siblings` | `list[dict]\|None` | Dispositivos irmãos |
| `children` | `list[dict]\|None` | Dispositivos filhos |
| `nota_especialista` | `str\|None` | Nota do especialista |
| `jurisprudencia_tcu` | `str\|None` | Jurisprudência vinculada |

---

## Metadados

### `Metadata`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `document_type` | `str` | LEI, DECRETO, IN, PORTARIA |
| `number` | `str` | Número do documento |
| `year` | `int` | Ano |
| `article_number` | `str\|None` | Número do artigo |

### `SearchMode`

Enum de modos de busca.

```python
from vectorgov import SearchMode

results = vg.search("query", mode=SearchMode.PRECISE)
```

| Valor | Latência | Descrição |
|-------|----------|-----------|
| `FAST` | ~2s | Busca rápida, menos precisa |
| `BALANCED` | ~5s | Equilíbrio (padrão) |
| `PRECISE` | ~7s | Máxima precisão, mais lenta |

---

## Tokens

### `TokenStats` <sup>v0.13.0</sup>

Retornado por `vg.estimate_tokens()`.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `context_tokens` | `int` | Tokens do contexto |
| `system_tokens` | `int` | Tokens do system prompt |
| `query_tokens` | `int` | Tokens da query |
| `total_tokens` | `int` | Soma total |
| `char_count` | `int` | Caracteres totais |
| `encoding` | `str` | Encoding usado (cl100k_base) |

---

## Auditoria

### `AuditLog` <sup>v0.12.0</sup>

Registro individual de auditoria.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `str` | UUID do log |
| `event_type` | `str` | search, smart_search, hybrid, lookup, feedback |
| `query` | `str\|None` | Query (se aplicável) |
| `latency_ms` | `float` | Tempo de resposta |
| `results_count` | `int` | Resultados retornados |
| `cached` | `bool` | Se veio do cache |
| `api_key_prefix` | `str` | Prefixo da API key |
| `created_at` | `str` | Timestamp ISO |

### `AuditLogsResponse` <sup>v0.12.0</sup>

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `logs` | `list[AuditLog]` | Lista de logs |
| `total` | `int` | Total de registros |
| `page` | `int` | Página atual |

### `AuditStats` <sup>v0.12.0</sup>

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `total_requests` | `int` | Total de requisições no período |
| `successful` | `int` | Requisições com sucesso |
| `errors` | `int` | Requisições com erro |
| `success_rate` | `float` | Taxa de sucesso (%) |
| `cache_hits` | `int` | Hits no cache |
| `cache_rate` | `float` | Taxa de cache (%) |
| `avg_latency_ms` | `float` | Latência média |
| `by_endpoint` | `dict` | Requisições por endpoint |
| `by_status` | `dict` | Requisições por status HTTP |

---

## Documentos

### `DocumentSummary` <sup>v0.11.0</sup>

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `document_id` | `str` | ID do documento |
| `tipo_documento` | `str` | Tipo (LEI, DECRETO, IN) |
| `numero` | `str` | Número |
| `ano` | `int` | Ano |
| `total_chunks` | `int` | Total de chunks |

### `UploadResponse` <sup>v0.11.0</sup>

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `task_id` | `str` | ID da task async |
| `status` | `str` | processing |
| `message` | `str` | Mensagem descritiva |

### `IngestStatus` <sup>v0.11.0</sup>

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `task_id` | `str` | ID da task |
| `status` | `str` | processing, completed, failed |
| `progress` | `float` | Progresso (0.0 a 1.0) |
| `current_phase` | `str` | Fase atual |
| `total_chunks` | `int\|None` | Chunks gerados (quando completo) |

### `DeleteResponse` <sup>v0.12.0</sup>

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `success` | `bool` | Se deletou com sucesso |
| `document_id` | `str` | ID do documento removido |
| `chunks_deleted` | `int` | Chunks removidos |

---

## Exceções

Todas herdam de `VectorGovError`.

```python
from vectorgov.exceptions import (
    VectorGovError,    # base
    AuthError,         # 401 — API key inválida
    RateLimitError,    # 429 — rate limit (tem retry_after)
    ValidationError,   # 400 — parâmetros inválidos (tem field)
    TierError,         # 403 — plano insuficiente (tem upgrade_url)
    ServerError,       # 500 — erro interno
    ConnectionError,   # sem HTTP — falha de rede
    TimeoutError,      # sem HTTP — timeout
)
```

| Exceção | HTTP | Campos extras | Quando ocorre |
|---------|------|--------------|---------------|
| `AuthError` | 401 | — | API key inválida ou expirada |
| `RateLimitError` | 429 | `retry_after: int` | Limite de requisições excedido |
| `ValidationError` | 400 | `field: str` | Parâmetros inválidos |
| `TierError` | 403 | `upgrade_url: str` | Recurso não incluso no plano |
| `ServerError` | 500 | — | Erro interno do servidor |
| `ConnectionError` | — | — | Falha de rede/DNS |
| `TimeoutError` | — | — | Requisição excedeu timeout |

Veja o [guia de tratamento de erros](../guides/error-handling.md) para padrões de uso.
