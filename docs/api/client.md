# Cliente VectorGov — Referência Completa

> Atualizado para v0.15.2 (Março 2026)

A classe `VectorGov` é o ponto de entrada principal do SDK.

## Inicialização

```python
from vectorgov import VectorGov

vg = VectorGov(
    api_key="vg_xxx",          # ou VECTORGOV_API_KEY env var
    base_url="https://vectorgov.io/api/v1",
    timeout=30,
    default_top_k=5,
    default_mode="balanced",
)
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `api_key` | `str` | `None` | Chave de API. Usa env `VECTORGOV_API_KEY` se omitida |
| `base_url` | `str` | `"https://vectorgov.io/api/v1"` | URL base da API |
| `timeout` | `int` | `30` | Timeout em segundos |
| `default_top_k` | `int` | `5` | Resultados padrão por busca |
| `default_mode` | `str\|SearchMode` | `"balanced"` | Modo de busca padrão |

---

## Busca

### `search()`

Busca semântica na base de conhecimento. 3 modos: `fast` (~2s), `balanced` (~5s), `precise` (~7s).

```python
results = vg.search("O que é ETP?", mode="precise", top_k=10)
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | — | Texto da consulta (obrigatório) |
| `top_k` | `int` | `5` | Quantidade de resultados (1-50) |
| `mode` | `str\|SearchMode` | `"balanced"` | `fast`, `balanced`, `precise` |
| `filters` | `dict` | `None` | `{"tipo": "lei", "ano": 2021, "orgao": "seges"}` |
| `use_cache` | `bool` | `False` | Cache compartilhado (trade-off privacidade) |
| `document_id_filter` | `str` | `None` | Filtro por documento (ex: `"LEI-14133-2021"`) |
| `trace_id` | `str` | `None` | ID para correlação de logs |

**Retorna:** [`SearchResult`](models.md#searchresult)
**Exceções:** `ValidationError`, `AuthError`, `RateLimitError`

---

### `smart_search()` <sup>v0.15.0 · Premium</sup>

Busca completa com análise jurídica automática (pipeline de 3 estágios). O sistema decide a melhor estratégia automaticamente.

```python
result = vg.smart_search("Hipóteses de dispensa por valor")
print(result.confianca)   # ALTO | MEDIO | BAIXO
print(result.raciocinio)  # Análise jurídica completa
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | — | Texto da consulta (3-1000 chars) |
| `use_cache` | `bool` | `False` | Reutilizar resultado cacheado |
| `trace_id` | `str` | `None` | ID para correlação |

**Retorna:** [`SmartSearchResult`](models.md#smartsearchresult) — herda `SearchResult` + campos `raciocinio`, `confianca`, `normas_presentes`, `tentativas`
**Exceções:** `TierError` (plano insuficiente), `ValidationError`, `AuthError`, `RateLimitError`, `TimeoutError`

**Fallback:**
```python
try:
    result = vg.smart_search("query")
except TierError:
    result = vg.search("query", mode="precise")
```

---

### `hybrid()` <sup>v0.15.0</sup>

Busca híbrida: semântica + expansão por grafo normativo.

```python
result = vg.hybrid("critérios de julgamento", hops=2, token_budget=3000)
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | — | Texto da consulta |
| `top_k` | `int` | `None` | Resultados da busca semântica |
| `collections` | `list[str]` | `None` | Collections a buscar |
| `hops` | `int` | `1` | Saltos no grafo (1 ou 2) |
| `graph_expansion` | `str` | `"bidirectional"` | `"bidirectional"` ou `"forward"` |
| `token_budget` | `int` | `None` | Limite de tokens no contexto |
| `use_cache` | `bool` | `None` | Usar cache |
| `trace_id` | `str` | `None` | ID para correlação |

**Retorna:** [`HybridResult`](models.md#hybridresult) com `direct_evidence`, `graph_expansion`, `stats`
**Exceções:** `ValidationError`, `AuthError`, `RateLimitError`

---

### `lookup()` <sup>v0.15.0</sup>

Consulta direta por referência textual. Determinística, < 1 segundo.

```python
# Único
result = vg.lookup("Art. 75 da Lei 14.133/2021")

# Lote (até 20)
result = vg.lookup(["Art. 75 da Lei 14.133/2021", "Art. 6 da IN 65/2021"])
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `reference` | `str\|list[str]` | — | Referência(s) legal(is) |
| `collection` | `str` | `"leis_v4"` | Collection de dados |
| `include_parent` | `bool` | `True` | Incluir artigo pai |
| `include_siblings` | `bool` | `True` | Incluir dispositivos irmãos |
| `trace_id` | `str` | `None` | ID para correlação |

**Retorna:** [`LookupResult`](models.md#lookupresult) com `status`, `matches`, `evidence`
**Exceções:** `ValidationError`, `AuthError`

---

## Documentos

### `list_documents()` <sup>v0.11.0</sup>

Lista documentos indexados.

```python
docs = vg.list_documents(page=1, limit=20, collection="leis_v4")
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `page` | `int` | `1` | Página |
| `limit` | `int` | `20` | Itens por página |
| `collection` | `str` | `"leis_v4"` | Collection |

**Retorna:** `DocumentsResponse`

### `get_document()` <sup>v0.11.0</sup>

Detalhes de um documento.

```python
doc = vg.get_document("LEI-14133-2021")
```

**Retorna:** `DocumentSummary`

### `upload_pdf()` <sup>v0.11.0</sup>

Upload e processamento de PDF.

```python
result = vg.upload_pdf("lei.pdf", tipo_documento="LEI", numero="14133", ano=2021)
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `file_path` | `str` | Caminho do PDF (máx 50MB) |
| `tipo_documento` | `str` | LEI, DECRETO, IN, PORTARIA |
| `numero` | `str` | Número do documento |
| `ano` | `int` | Ano |

**Retorna:** `UploadResponse` com `task_id`

### `get_ingest_status()` <sup>v0.11.0</sup>

Verifica status do processamento async de PDF.

```python
status = vg.get_ingest_status(task_id)
print(status.progress)  # 0.0 a 1.0
```

**Retorna:** `IngestStatus` com `status`, `progress`, `current_phase`

### `delete_document()` <sup>v0.12.0</sup>

Remove documento e todos seus chunks.

```python
result = vg.delete_document("LEI-14133-2021")
```

**Retorna:** `DeleteResponse`

---

## Tokens e Feedback

### `estimate_tokens()` <sup>v0.13.0</sup>

Estima tokens de um texto ou resultado de busca (tiktoken/cl100k_base no servidor).

```python
stats = vg.estimate_tokens(results)
print(f"Total: {stats.total_tokens} tokens")
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `content` | `str\|SearchResult` | Texto ou resultado de busca |
| `query` | `str` | Query (opcional, somada ao total) |
| `system_prompt` | `str` | System prompt (opcional) |

**Retorna:** [`TokenStats`](models.md#tokenstats)

### `feedback()` <sup>v0.10.0</sup>

Registra feedback (like/dislike) sobre resultado.

```python
vg.feedback(results.query_id, like=True)
```

**Retorna:** `bool`

### `store_response()` <sup>v0.14.0</sup>

Armazena resposta gerada pelo seu LLM para analytics.

```python
vg.store_response(
    query_id=results.query_id,
    response_text="A resposta do meu LLM...",
    model="gpt-4o",
    tokens_used=500,
)
```

**Retorna:** `bool`

---

## Function Calling / Tools

### `to_openai_tool()` <sup>v0.12.0</sup>

Gera definição de tool para OpenAI function calling.

```python
tools = [vg.to_openai_tool()]
response = openai.chat.completions.create(model="gpt-4o", tools=tools, ...)
```

**Retorna:** `dict` compatível com OpenAI tools API

### `to_anthropic_tool()` <sup>v0.12.0</sup>

Gera definição de tool para Claude/Anthropic.

```python
tools = [vg.to_anthropic_tool()]
response = anthropic.messages.create(model="claude-sonnet-4-20250514", tools=tools, ...)
```

**Retorna:** `dict` compatível com Anthropic tools API

### `to_google_tool()` <sup>v0.12.0</sup>

Gera definição de tool para Google Gemini.

```python
tools = [vg.to_google_tool()]
```

**Retorna:** `dict` compatível com Google Generative AI tools API

### `execute_tool_call()` <sup>v0.12.0</sup>

Executa uma chamada de tool retornada pelo LLM.

```python
result = vg.execute_tool_call(tool_name="vectorgov_search", arguments={"query": "ETP"})
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `tool_name` | `str` | Nome da tool chamada pelo LLM |
| `arguments` | `dict` | Argumentos extraídos pelo LLM |

**Retorna:** `SearchResult`

---

## System Prompts

### `get_system_prompt()` <sup>v0.10.0</sup>

Retorna system prompt pré-otimizado para RAG jurídico.

```python
prompt = vg.get_system_prompt("detailed")
```

| Estilo | Descrição |
|--------|-----------|
| `default` | Balanceado, formal, cita fontes |
| `concise` | Respostas curtas e diretas |
| `detailed` | Análise profunda, estruturada |
| `chatbot` | Tom amigável, acessível |

### `available_prompts` <sup>v0.10.0</sup>

Propriedade com estilos disponíveis.

```python
print(vg.available_prompts)  # ['default', 'concise', 'detailed', 'chatbot']
```

---

## Auditoria

### `get_audit_logs()` <sup>v0.12.0</sup>

Consulta logs de auditoria da API.

```python
logs = vg.get_audit_logs(limit=50, event_type="search")
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `limit` | `int` | `50` | Máximo de registros |
| `offset` | `int` | `0` | Paginação |
| `event_type` | `str` | `None` | Filtro por tipo |
| `start_date` | `str` | `None` | Data início (ISO) |
| `end_date` | `str` | `None` | Data fim (ISO) |
| `api_key_id` | `str` | `None` | Filtro por API key |

**Retorna:** `AuditLogsResponse`

### `get_audit_stats()` <sup>v0.12.0</sup>

Estatísticas agregadas de uso.

```python
stats = vg.get_audit_stats(days=30)
print(f"Total: {stats.total_requests}")
print(f"Cache hit rate: {stats.cache_rate}%")
```

**Retorna:** `AuditStats`

### `get_audit_event_types()` <sup>v0.13.0</sup>

Lista tipos de evento disponíveis para filtro.

```python
types = vg.get_audit_event_types()
# ['search', 'smart_search', 'hybrid', 'lookup', 'feedback', ...]
```

**Retorna:** `list[str]`

---

## Enriquecimento

### `start_enrichment()` <sup>v0.14.0</sup>

Inicia enriquecimento de um documento (context, thesis, questions).

```python
result = vg.start_enrichment("LEI-14133-2021")
```

**Retorna:** `dict` com `task_id`

### `get_enrichment_status()` <sup>v0.14.0</sup>

Status do enriquecimento.

```python
status = vg.get_enrichment_status(task_id)
```

**Retorna:** `EnrichStatus`

---

## Cliente Assíncrono <sup>v0.14.0</sup>

O `AsyncVectorGov` tem a mesma API do `VectorGov`, mas todos os métodos são `async`.

```python
from vectorgov import AsyncVectorGov

async with AsyncVectorGov(api_key="vg_xxx") as vg:
    result = await vg.search("O que é ETP?")
    print(result.to_context())

    # Buscas paralelas
    import asyncio
    r1, r2 = await asyncio.gather(
        vg.search("ETP"),
        vg.search("dispensa de licitação"),
    )
```

Todos os métodos documentados acima estão disponíveis como `await vg.metodo()`.

---

## Context Manager

```python
# Sync
with VectorGov(api_key="vg_xxx") as vg:
    results = vg.search("query")

# Async
async with AsyncVectorGov(api_key="vg_xxx") as vg:
    results = await vg.search("query")
```

O `close()` é chamado automaticamente ao sair do bloco.
