# VectorGov API — Endpoints Reference

> Referencia completa de todos os endpoints publicos com exemplos de request/response.
>
> **Base URL:** `https://vectorgov.io/api/v1`
> **Auth:** Header `Authorization: Bearer vg_xxx` (API Key)

---

## Indice

1. [POST /sdk/search](#1-post-sdksearch) — Busca semantica
2. [POST /sdk/smart-search](#2-post-sdksmart-search) — Consulta inteligente MOC4
3. [POST /sdk/feedback](#3-post-sdkfeedback) — Feedback like/dislike
4. [POST /sdk/tokens](#4-post-sdktokens) — Estimativa de tokens
5. [POST /retrieve/search](#5-post-retrievesearch) — Busca com reranking e expansao
6. [POST /retrieve/lookup](#6-post-retrievelookup) — Consulta direta por referencia
7. [POST /retrieve/hybrid](#7-post-retrievehybrid) — Busca hibrida com grafo
8. [POST /filesystem/search](#8-post-filesystemsearch) — Busca no indice curado
9. [POST /filesystem/grep](#9-post-filesystemgrep) — Busca textual exata
10. [GET /filesystem/read/{document_id}](#10-get-filesystemreaddocument_id) — Leitura de canonical
11. [POST /search/merged](#11-post-searchmerged) — Busca dual-path combinada
12. [GET /sdk/audit/logs](#12-get-sdkauditlogs) — Logs de auditoria
13. [GET /sdk/audit/stats](#13-get-sdkauditstats) — Estatisticas de auditoria

---

## 1. POST /sdk/search

Busca semantica com guardrails de seguranca (deteccao de PII, prompt injection, circuit breaker).

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/sdk/search \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quando a licitacao pode ser dispensada?",
    "top_k": 5,
    "mode": "balanced"
  }'
```

| Campo | Tipo | Obrigatorio | Default | Descricao |
|-------|------|:-----------:|---------|-----------|
| query | string | Sim | — | Consulta (3-1000 chars) |
| top_k | int | Nao | 5 | Resultados (1-20) |
| mode | string | Nao | "balanced" | "fast" (~2s), "balanced" (~5s), "precise" (~15s) |
| tipo_documento | string | Nao | null | Filtro: "lei", "decreto", "in", "portaria" |
| ano | int | Nao | null | Filtro por ano (1900-2100) |
| use_cache | bool | Nao | false | Cache semantico compartilhado (ver nota abaixo) |
| scope | string | Nao | null | Escopo federativo |

> **Cache e privacidade:** O cache e compartilhado entre todos os clientes.
> Com `use_cache: true`, sua query/resposta pode ser reutilizada por outros usuarios
> e voce pode receber respostas de queries de outros. Use `true` apenas para
> queries genericas onde a troca privacidade/latencia e aceitavel.
> Default: `false` (privacidade maxima).

### Response (200)

```json
{
  "success": true,
  "hits": [
    {
      "text": "Art. 75. E dispensavel a licitacao...",
      "score": 0.94,
      "source": "Lei 14.133/2021, Art. 75",
      "breadcrumb": "Lei 14.133/2021 > Cap. VIII > Art. 75",
      "tipo_documento": "LEI",
      "numero": "14133",
      "ano": 2021,
      "article_number": "75",
      "context_header": "Este artigo define as hipoteses de dispensa...",
      "nota_especialista": "Valores atualizados em 2024 pelo Decreto...",
      "evidence_url": "https://vectorgov.io/api/v1/evidence/highlight/leis:LEI-14133-2021%23ART-075?token=...",
      "document_url": "https://vectorgov.io/api/v1/evidence/download/source/LEI-14133-2021?token=..."
    }
  ],
  "total": 5,
  "latency_ms": 1832,
  "cached": false,
  "mode": "balanced",
  "query_id": "a1b2c3d4",
  "timestamp": "2026-03-30T03:00:00Z"
}
```

---

## 2. POST /sdk/smart-search

Pipeline completo MOC v4: Pensador (analisa query) -> Motor (coleta contexto) -> Juiz (avalia e aprova chunks). Latencia tipica: 5-18 segundos.

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/sdk/smart-search \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quem pode ser designado como agente de contratacao?",
    "use_cache": false
  }'
```

| Campo | Tipo | Obrigatorio | Default | Descricao |
|-------|------|:-----------:|---------|-----------|
| query | string | Sim | — | Consulta juridica (3-1000 chars) |
| use_cache | bool | Nao | false | Cache compartilhado (ver nota de privacidade em /sdk/search) |

### Response (200)

```json
{
  "hits": [
    {
      "node_id": "leis:LEI-14133-2021#ART-008",
      "source": "Lei 14.133/2021, Art. 8",
      "breadcrumb": "Lei 14.133/2021 > Cap. II > Art. 8",
      "text": "Art. 8. A licitacao sera conduzida por agente de contratacao...",
      "score": 0.92,
      "tipo_documento": "LEI",
      "article_number": "8",
      "device_type": "article",
      "nota_especialista": "O agente deve ser servidor efetivo...",
      "evidence_url": "https://vectorgov.io/api/v1/evidence/highlight/..."
    }
  ],
  "total": 4,
  "confianca": "ALTO",
  "raciocinio": "A query refere-se ao agente de contratacao previsto no art. 8 da Lei 14.133/2021. Os dispositivos selecionados cobrem: definicao do agente (art. 8), requisitos (art. 7), e vedacoes (par. 1).",
  "tentativas": 1,
  "normas_presentes": ["Lei 14.133/2021", "Decreto 10.947/2022"],
  "quantidade_normas": 2,
  "relacoes_count": 3,
  "latency_ms": 8432,
  "cached": false,
  "query_id": "e5f6g7h8"
}
```

---

## 3. POST /sdk/feedback

Registra avaliacao do usuario sobre um resultado de busca.

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/sdk/feedback \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "a1b2c3d4",
    "is_like": true
  }'
```

### Response (200)

```json
{
  "success": true,
  "message": "Feedback registrado",
  "new_likes": 1,
  "new_dislikes": 0
}
```

---

## 4. POST /sdk/tokens

Estima quantos tokens um contexto vai consumir no LLM. Usa encoding cl100k_base (compativel com GPT-4, Claude, Gemini).

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/sdk/tokens \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Art. 75. E dispensavel a licitacao para contratacao...",
    "query": "Quando pode dispensar licitacao?",
    "system_prompt": "Voce e um especialista em licitacoes."
  }'
```

### Response (200)

```json
{
  "success": true,
  "context_tokens": 1500,
  "system_tokens": 12,
  "query_tokens": 8,
  "total_tokens": 1520,
  "char_count": 5800,
  "encoding": "cl100k_base"
}
```

---

## 5. POST /retrieve/search

Busca semantica completa com reranking, parent-child expansion, query rewriting e dual lane.

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/retrieve/search \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "criterios de julgamento em licitacao",
    "top_k": 10,
    "collection": "leis_v4",
    "use_reranker": true,
    "use_parent_child": true,
    "include_evidence": true
  }'
```

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| query | string | — | Consulta (3-1000 chars) |
| top_k | int | 20 | Resultados (1-30) |
| collection | string | "leis_v4" | Collection Milvus |
| use_reranker | bool | true | Cross-encoder reranking |
| use_hyde | bool | false | HyDE query expansion |
| use_parent_child | bool | false | Expandir pai/filhos |
| use_graph_retrieval | bool | false | Expandir via Neo4j |
| include_evidence | bool | true | Incluir URLs de highlight |
| dual_ingestion | bool | true | Dedup chunks @FULL |
| query_rewrite | bool | true | Extrair referencia normativa |
| dual_lane | bool | true | Query filtrada + livre em paralelo |
| document_id_filter | string | null | Filtrar por documento |
| scope | string | null | Escopo federativo |

### Response (200)

```json
{
  "success": true,
  "query": "criterios de julgamento em licitacao",
  "hits": [
    {
      "rank": 1,
      "node_id": "leis:LEI-14133-2021#ART-033",
      "document_id": "LEI-14133-2021",
      "text": "Art. 33. O julgamento das propostas...",
      "device_type": "article",
      "breadcrumb": "Lei 14.133/2021 > Cap. V > Art. 33",
      "score": 0.78,
      "rerank_score": 0.94,
      "final_score": 0.94,
      "is_parent": false,
      "is_graph_expanded": false,
      "nota_especialista": null,
      "evidence_url": "https://vectorgov.io/api/v1/evidence/highlight/...",
      "evidence": {
        "canonical_start": 12450,
        "canonical_end": 13200,
        "canonical_hash": "abc123...",
        "page_number": 15
      }
    }
  ],
  "total_found": 10,
  "search_time_ms": 245,
  "rerank_time_ms": 1200,
  "reranker_used": true,
  "hyde_used": false,
  "query_rewrite_active": true,
  "query_rewrite_clean_query": "criterios de julgamento",
  "dual_lane_active": true,
  "timings": {
    "stage1_hyde": 0,
    "stage2_seeds": 245,
    "stage3_parent_child": 120,
    "stage5_rerank": 1200
  }
}
```

---

## 6. POST /retrieve/lookup

Resolucao direta de referencia normativa. Aceita linguagem natural ("art. 75 da Lei 14.133") e retorna o dispositivo exato com pai, filhos e irmaos.

### Request (single)

```bash
curl -X POST https://vectorgov.io/api/v1/retrieve/lookup \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "reference": "art. 75 da Lei 14.133/2021",
    "include_siblings": true,
    "include_parent": true
  }'
```

### Request (batch)

```bash
curl -X POST https://vectorgov.io/api/v1/retrieve/lookup \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "references": [
      "art. 75 da Lei 14.133",
      "art. 3 da IN 65/2021",
      "art. 18 do Decreto 10.947"
    ]
  }'
```

### Response (200 — single)

```json
{
  "status": "found",
  "reference": "art. 75 da Lei 14.133/2021",
  "elapsed_ms": 45,
  "resolved": {
    "device_type": "article",
    "article_number": "75",
    "resolved_document_id": "LEI-14133-2021",
    "resolved_span_id": "ART-075"
  },
  "node_id": "leis:LEI-14133-2021#ART-075",
  "text": "Art. 75. E dispensavel a licitacao...",
  "device_type": "article",
  "breadcrumb": "Lei 14.133/2021 > Cap. VIII > Art. 75",
  "parent": null,
  "children": [
    {
      "node_id": "leis:LEI-14133-2021#INC-075-I",
      "span_id": "INC-075-I",
      "text": "I - para contratacao que envolva valores...",
      "device_type": "inciso"
    }
  ],
  "stitched_text": "Art. 75. E dispensavel a licitacao...\nI - para contratacao...\nII - para outros servicos...",
  "siblings": [],
  "evidence_url": "https://vectorgov.io/api/v1/evidence/highlight/..."
}
```

---

## 7. POST /retrieve/hybrid

Busca hibrida: Milvus (semantica) + Neo4j (grafo de citacoes). Retorna evidencia direta + expansao via grafo com token budget.

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/retrieve/hybrid \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "criterios de julgamento",
    "top_k": 10,
    "hops": 1,
    "token_budget": 3500,
    "graph_expansion": "bidirectional"
  }'
```

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| query | string | — | Consulta |
| top_k | int | 20 | Seeds do Milvus (1-50) |
| topK_graph | int | 15 | Nos expandidos (1-50) |
| hops | int | 1 | Saltos no grafo (1-2) |
| token_budget | int | 3500 | Limite de tokens (500-8000) |
| graph_expansion | string | "bidirectional" | "forward", "bidirectional", "off" |
| collections | list | ["leis_v4"] | Collections |

### Response (200)

```json
{
  "direct_evidence": [
    {
      "rank": 1,
      "node_id": "leis:LEI-14133-2021#ART-033",
      "score": 0.92,
      "text": "Art. 33. O julgamento das propostas...",
      "document_id": "LEI-14133-2021",
      "span_id": "ART-033",
      "device_type": "article",
      "breadcrumb": "Lei 14.133/2021 > Cap. V > Art. 33",
      "is_parent": false,
      "is_graph_expanded": false
    }
  ],
  "graph_expansion": [
    {
      "node_id": "leis:LEI-14133-2021#ART-036",
      "text": "Art. 36. A avaliacao de propostas...",
      "document_id": "LEI-14133-2021",
      "span_id": "ART-036",
      "device_type": "article",
      "hop": 1,
      "frequency": 3,
      "paths": [
        ["leis:LEI-14133-2021#ART-033", "leis:LEI-14133-2021#ART-036"]
      ]
    }
  ],
  "llm_context_text": "=== EVIDENCIA DIRETA ===\n[1] Lei 14.133/2021, Art. 33\n...",
  "llm_context_tokens": 2800,
  "confidence": 0.89,
  "search_time_ms": 1450,
  "stats": {
    "seeds_count": 10,
    "graph_nodes": 5,
    "total_chunks": 15,
    "truncated": false
  }
}
```

---

## 8. POST /filesystem/search

Busca no indice curado do PostgreSQL + ripgrep. Modo "auto" detecta se a query e uma referencia legal (usa grep) ou semantica (usa indice).

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/filesystem/search \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "art. 75 da Lei 14.133",
    "mode": "auto",
    "top_k": 10
  }'
```

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| query | string | — | Busca |
| document_id | string | null | Filtro por norma |
| mode | string | "auto" | "auto", "index", "grep", "both" |
| top_k | int | 10 | Resultados (1-50) |
| include_text | bool | true | Incluir texto completo |

### Response (200)

```json
{
  "results": [
    {
      "node_id": "leis:LEI-14133-2021#ART-075",
      "document_id": "LEI-14133-2021",
      "span_id": "ART-075",
      "text": "Art. 75. E dispensavel a licitacao...",
      "score": 1.0,
      "source": "grep",
      "breadcrumb": "Lei 14.133/2021 > Art. 75",
      "match_reason": "Referencia direta detectada"
    }
  ],
  "total": 1,
  "query": "art. 75 da Lei 14.133",
  "mode_used": "grep",
  "latency_ms": 85,
  "documents_searched": 8
}
```

---

## 9. POST /filesystem/grep

Busca textual exata via ripgrep nos canonical.md dos documentos indexados. Util para encontrar trechos especificos por palavras-chave.

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/filesystem/grep \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "dispensa de licitacao",
    "document_id": "LEI-14133-2021",
    "max_results": 10,
    "context_lines": 3
  }'
```

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| query | string | — | Texto exato a buscar |
| document_id | string | null | Filtro por documento |
| max_results | int | 20 | Maximo (1-50) |
| context_lines | int | 3 | Linhas de contexto (0-10) |

### Response (200)

```json
{
  "matches": [
    {
      "node_id": "leis:LEI-14133-2021#ART-075",
      "document_id": "LEI-14133-2021",
      "span_id": "ART-075",
      "text": "Art. 75. E dispensavel a licitacao...",
      "matched_line": "Art. 75. E dispensavel a licitacao para contratacao que envolva valores",
      "line_number": 1245,
      "char_offset": 45230,
      "score": 1.0,
      "match_reason": "grep exact"
    }
  ],
  "total": 3,
  "query": "dispensa de licitacao",
  "latency_ms": 42,
  "files_searched": 1
}
```

---

## 10. GET /filesystem/read/{document_id}

Le o canonical completo de um documento ou um trecho especifico.

### Request (documento inteiro)

```bash
curl https://vectorgov.io/api/v1/filesystem/read/LEI-14133-2021 \
  -H "Authorization: Bearer vg_sua_chave"
```

### Request (dispositivo especifico)

```bash
curl "https://vectorgov.io/api/v1/filesystem/read/LEI-14133-2021?span_id=ART-075" \
  -H "Authorization: Bearer vg_sua_chave"
```

### Response (200)

```json
{
  "document_id": "LEI-14133-2021",
  "span_id": "ART-075",
  "text": "Art. 75. E dispensavel a licitacao...",
  "breadcrumb": "Lei 14.133/2021 > Art. 75",
  "token_count": 342,
  "char_count": 1250,
  "source": "canonical"
}
```

---

## 11. POST /search/merged

Busca dual-path: combina hybrid (Milvus+Neo4j) com filesystem (PG index + ripgrep). Resultados unificados, deduplicados e ranqueados via RRF.

### Request

```bash
curl -X POST https://vectorgov.io/api/v1/search/merged \
  -H "Authorization: Bearer vg_sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "prazo para impugnacao do edital",
    "top_k": 10,
    "token_budget": 6000,
    "enable_hybrid": true,
    "enable_filesystem": true
  }'
```

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| query | string | — | Consulta (2-1000 chars) |
| document_id | string | null | Filtro |
| top_k | int | 10 | Resultados (1-30) |
| token_budget | int | 6000 | Limite de tokens (0-20000) |
| boost_mutual | float | 1.5 | Boost para hits em ambas fontes (1.0-5.0) |
| enable_hybrid | bool | true | Ativar busca hibrida |
| enable_filesystem | bool | true | Ativar busca filesystem |
| filesystem_mode | string | "auto" | Modo filesystem |

### Response (200)

```json
{
  "results": [
    {
      "node_id": "leis:LEI-14133-2021#ART-164",
      "document_id": "LEI-14133-2021",
      "span_id": "ART-164",
      "text": "Art. 164. Qualquer pessoa e parte...",
      "score": 0.88,
      "token_count": 120,
      "breadcrumb": "Lei 14.133/2021 > Art. 164",
      "sources": ["hybrid", "filesystem"],
      "hybrid_rank": 1,
      "filesystem_rank": 3,
      "hybrid_score": 0.92,
      "filesystem_score": 0.85,
      "text_source": "canonical",
      "has_specialist_note": true,
      "has_jurisprudence": false
    }
  ],
  "total": 10,
  "token_total": 4200,
  "token_budget": 6000,
  "hybrid_count": 8,
  "filesystem_count": 6,
  "mutual_count": 4,
  "latency_ms": 2100,
  "hybrid_latency_ms": 1800,
  "filesystem_latency_ms": 150,
  "merge_latency_ms": 50
}
```

---

## 12. GET /sdk/audit/logs

Lista logs de auditoria filtrados por tipo, severidade e periodo. Cada API Key so ve seus proprios logs (isolamento por key).

### Request

```bash
curl "https://vectorgov.io/api/v1/sdk/audit/logs?severity=critical&days=7&limit=10" \
  -H "Authorization: Bearer vg_sua_chave"
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| event_type | string | null | "pii_detected", "injection_blocked", etc. |
| severity | string | null | "info", "warning", "critical" |
| start_date | string | null | ISO 8601 |
| end_date | string | null | ISO 8601 |
| page | int | 1 | Pagina |
| limit | int | 50 | Itens/pagina (max 100) |

### Response (200)

```json
{
  "logs": [
    {
      "id": "uuid-123",
      "event_type": "injection_detected",
      "event_category": "security",
      "severity": "critical",
      "query_text": "ignore previous instructions and...",
      "action_taken": "blocked",
      "risk_score": 0.95,
      "endpoint": "/sdk/search",
      "created_at": "2026-03-29T15:30:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "pages": 1,
  "limit": 50
}
```

---

## 13. GET /sdk/audit/stats

Estatisticas agregadas de auditoria por periodo.

### Request

```bash
curl "https://vectorgov.io/api/v1/sdk/audit/stats?days=30" \
  -H "Authorization: Bearer vg_sua_chave"
```

### Response (200)

```json
{
  "total_events": 150,
  "blocked_count": 3,
  "warning_count": 12,
  "events_by_type": {
    "query_processed": 130,
    "low_relevance_query": 10,
    "pii_detected": 5,
    "injection_detected": 3,
    "rate_limit_exceeded": 2
  },
  "events_by_severity": {
    "info": 130,
    "warning": 17,
    "critical": 3
  }
}
```

---

## Erros Comuns

### 400 — Validacao

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Query deve ter entre 3 e 1000 caracteres",
  "field": "query"
}
```

### 401 — API Key invalida

```json
{
  "detail": "API key nao encontrada"
}
```

### 403 — Endpoint nao permitido pelo plano

```json
{
  "detail": "Endpoint nao disponivel no seu plano. Endpoints permitidos: search, lookup. Faca upgrade em vectorgov.io/pricing",
  "allowed_endpoints": ["search", "lookup"]
}
```

### 429 — Rate limit

```json
{
  "detail": "Rate limit exceeded"
}
```
Header `Retry-After: 60` incluido.

### 503 — Circuit breaker aberto

```json
{
  "success": false,
  "error": "circuit_breaker_open",
  "message": "GPU Server indisponivel. Tente novamente em alguns minutos."
}
```

---

## Python SDK

Todos os endpoints acima tem metodos correspondentes no SDK Python:

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_sua_chave")

# /sdk/search
results = vg.search("Quando dispensar licitacao?", top_k=5, mode="balanced")

# /sdk/smart-search
results = vg.smart_search("Quem pode ser agente de contratacao?")

# /sdk/feedback
vg.feedback(query_id="a1b2c3d4", like=True)

# /sdk/tokens
stats = vg.estimate_tokens(results)

# Converter resultado para contexto LLM
context = results.to_context()
messages = results.to_messages("Minha pergunta")
```

Instalacao: `pip install vectorgov`
Documentacao completa: https://vectorgov.io/documentacao
