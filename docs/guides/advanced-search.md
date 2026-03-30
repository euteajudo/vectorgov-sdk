# Guia de Busca Avançada

O SDK oferece 8 métodos de busca, cada um otimizado para um cenário diferente.

## Comparação Rápida

| Método | Latência | Custo | Melhor para |
|--------|----------|-------|-------------|
| `search()` | 2-7s | Baixo | Buscas simples, prototipagem |
| `smart_search()` | 5-18s | Alto (Premium) | Perguntas complexas, análise jurídica |
| `hybrid()` | 3-10s | Médio | Normas relacionadas, cadeia regulatória |
| `lookup()` | < 1s | Baixo | Referência exata ("Art. 75 da Lei X") |
| `grep()` | < 1s | Baixo | Busca textual exata, palavras-chave |
| `filesystem_search()` | < 1s | Baixo | Busca no índice curado, referências legais |
| `merged()` | 2-5s | Médio | Busca completa dual-path (semântica + filesystem) |
| `read_canonical()` | < 1s | Mínimo | Leitura de texto canônico completo |

## Quando usar cada método

```
Pergunta do usuário
  │
  ├─ É referência exata? ("Art. 75", "IN 65/2021")
  │  └─ SIM → lookup()
  │
  ├─ Precisa de análise jurídica completa?
  │  └─ SIM → smart_search()
  │
  ├─ Precisa de normas relacionadas/cadeia regulatória?
  │  └─ SIM → hybrid()
  │
  ├─ Busca simples por tema
  │  └─ search()
  │
  ├─ Precisa encontrar texto exato/palavra-chave?
  │  └─ SIM → grep()
  │
  ├─ Quer buscar no índice curado (determinístico)?
  │  └─ SIM → filesystem_search()
  │
  ├─ Quer combinar semântica + filesystem (máxima cobertura)?
  │  └─ SIM → merged()
  │
  └─ Precisa ler o texto completo de um dispositivo?
     └─ read_canonical()
```

## 1. `search()` — Busca Semântica

Busca rápida por similaridade semântica. 3 modos: `fast` (~2s), `balanced` (~5s), `precise` (~7s).

```python
from vectorgov import VectorGov, SearchMode

vg = VectorGov(api_key="vg_xxx")

# Modo rápido (2s)
results = vg.search("O que é ETP?", mode=SearchMode.FAST)

# Modo preciso com filtros (7s)
results = vg.search(
    "dispensa de licitação",
    mode=SearchMode.PRECISE,
    top_k=10,
    tipo_documento="LEI",
    ano=2021,
)

for hit in results:
    print(f"{hit.source}: {hit.text[:100]}")
```

**Retorna:** `SearchResult` com `hits`, `total`, `latency_ms`, `cached`, `mode`.

## 2. `smart_search()` — Busca Completa com Análise (Premium)

Pipeline inteligente de 3 estágios. O sistema analisa a query, decide a melhor estratégia de busca, e retorna análise jurídica de completude.

```python
result = vg.smart_search("Quais as hipóteses de dispensa por valor?")

# Análise do Juiz
print(result.confianca)        # ALTO | MEDIO | BAIXO
print(result.raciocinio)       # Análise jurídica completa
print(result.normas_presentes) # ["Lei 14.133/2021", "Decreto 10.947/2022"]

# Dispositivos encontrados
for hit in result:
    print(f"{hit.source}: {hit.text[:100]}")
```

**Retorna:** `SmartSearchResult` com `raciocinio`, `confianca`, `normas_presentes`, `tentativas`, além de `hits`, `total`, `latency_ms`.

**Requer:** Plano Premium. Lança `TierError` se o plano não incluir.

## 3. `hybrid()` — Busca com Expansão por Grafo

Combina busca semântica com navegação por relações normativas no grafo de citações. Encontra artigos que se citam, regulamentam ou complementam.

```python
result = vg.hybrid(
    "critérios de julgamento na licitação",
    top_k=5,
    hops=2,                          # até 2 saltos no grafo
    graph_expansion="bidirectional",  # ambas direções
    token_budget=3000,               # limite de tokens
)

# Evidências diretas (busca semântica)
for hit in result.direct_evidence:
    print(f"[DIRETO] {hit.source} (score: {hit.score:.2%})")

# Artigos citados (expansão via grafo)
for node in result.graph_expansion:
    print(f"[GRAFO] hop={node['hop']}, citado {node['frequency']}x")
```

**Retorna:** `HybridResult` com `direct_evidence` (lista de `Hit`), `graph_expansion` (lista de dicts com `hop`, `frequency`, `paths`), `stats`.

**Tipos de relação no grafo:** CITA, REGULAMENTA, COMPLEMENTA, EXCEPCIONA, DEPENDE_DE, ALTERA_EXPRESSAMENTE, REVOGA_EXPRESSAMENTE, INTERPRETA.

## 4. `lookup()` — Consulta Direta por Referência

Busca determinística por referência textual. Retorna o texto exato do dispositivo com contexto hierárquico (pai, filhos, irmãos).

```python
# Consulta única
result = vg.lookup("Art. 75 da Lei 14.133/2021")

# Consulta em lote (até 20 referências)
result = vg.lookup([
    "Art. 75 da Lei 14.133/2021",
    "Art. 6 da IN 65/2021",
    "Art. 3 do Decreto 10.947/2022",
])

# Acessar resultados
for match in result.matches:
    print(f"{match.span_id}: {match.text[:100]}")

    # Evidence (links para verificação)
    if match.evidence:
        print(f"  PDF: {match.evidence['pdf_url']}")
        print(f"  Destaque: {match.evidence['highlight_url']}")
```

**Retorna:** `LookupResult` com `status` (found/not_found/ambiguous), `matches` com `text`, `evidence`, `parent`, `siblings`, `children`.

**Formatos aceitos:** "Art. 75 da Lei 14.133/2021", "Art. 3 da IN 58/2022", "§ 2º do Art. 75 da Lei 14.133/2021".

---

## 5. `grep()` — Busca Textual Exata

Busca textual exata via ripgrep. Ideal para encontrar palavras-chave ou trechos específicos.

```python
# Busca simples
result = vg.grep("dispensa de licitacao")
for m in result:
    print(f"{m.span_id}: {m.matched_line}")

# Filtrar por documento
result = vg.grep("art. 75", document_id="LEI-14133-2021", max_results=5)
```

---

## 6. `filesystem_search()` — Índice Curado

Busca no índice PostgreSQL + ripgrep. O modo `auto` detecta se a query é referência legal ou texto livre.

```python
# Auto-detecta tipo de query
result = vg.filesystem_search("art. 75 da Lei 14.133")
for hit in result:
    print(f"[{hit.source}] {hit.breadcrumb}")

# Forçar modo grep
result = vg.filesystem_search("dispensa", mode="grep", top_k=5)
```

---

## 7. `merged()` — Busca Dual-Path

Combina busca híbrida (Milvus + Neo4j) com filesystem (PostgreSQL + ripgrep) em paralelo. Usa Reciprocal Rank Fusion (RRF) para unificar rankings.

```python
result = vg.merged("prazo para impugnacao do edital", top_k=10)
for hit in result:
    print(f"[{','.join(hit.sources)}] {hit.breadcrumb}: {hit.score:.2f}")
print(f"Em ambas fontes: {result.mutual_count}")
```

---

## 8. `read_canonical()` — Texto Canônico

Lê o texto completo de um documento ou dispositivo específico. Sem busca — acesso direto.

```python
# Documento inteiro
doc = vg.read_canonical("LEI-14133-2021")
print(f"{doc.token_count} tokens")

# Dispositivo específico
art = vg.read_canonical("LEI-14133-2021", span_id="ART-075")
print(art.text)
```

---

## Formatação para LLMs

Todos os métodos retornam objetos com métodos de formatação:

```python
result = vg.search("query")

# Texto plano com contexto
result.to_context()

# Messages prontas para OpenAI/Anthropic
result.to_messages("Minha pergunta", system_prompt="Responda em PT-BR")

# Prompt completo (system + context + query)
result.to_prompt("Minha pergunta")

# XML estruturado
result.to_xml()

# Markdown formatado
result.to_markdown()
```

## Performance e Custos

| Método | Chamadas API | Tokens LLM | Créditos |
|--------|-------------|------------|----------|
| `search(mode="fast")` | 1 | 0 | 1 |
| `search(mode="balanced")` | 1 | 0 | 1 |
| `search(mode="precise")` | 1-2 | 0 | 1-2 |
| `smart_search()` | 2-3 | ~2000 | 5 |
| `hybrid()` | 1-2 | 0 | 2 |
| `lookup()` | 1 | 0 | 1 |
| `lookup([...])` (lote) | 1 | 0 | 1 |
| `grep()` | 1 | 0 | 1 |
| `filesystem_search()` | 1 | 0 | 1 |
| `merged()` | 2-3 | 0 | 2 |
| `read_canonical()` | 1 | 0 | 1 |

> **Nota:** Valores de créditos são aproximados e dependem do plano contratado.
