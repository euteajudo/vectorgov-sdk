# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.16.0] - 2026-03-30

### Adicionado

- **`grep()`** — Busca textual exata nos documentos via ripgrep:
  - Encontra trechos contendo exatamente o texto buscado
  - Filtro por `document_id`, controle de `max_results` e `context_lines`
  - Retorna `GrepResult` com `GrepMatch` iteravel

- **`filesystem_search()`** — Busca no indice curado (PostgreSQL + ripgrep):
  - Modos: `auto` (detecta tipo da query), `index`, `grep`, `both`
  - Retorna `FilesystemResult` com `FilesystemHit` incluindo breadcrumb e match_reason

- **`merged()`** — Busca dual-path: hibrida + filesystem combinadas:
  - Executa ambas buscas em paralelo com Reciprocal Rank Fusion (RRF)
  - Hits presentes em ambas fontes recebem boost mutuo
  - Controle de `token_budget` (0-20000) e toggle de fontes
  - Retorna `MergedResult` com `MergedHit` incluindo `sources`, scores por fonte

- **`read_canonical()`** — Leitura do texto canonical completo:
  - Documento inteiro ou dispositivo especifico via `span_id`
  - Retorna `CanonicalResult` com texto, contagem de tokens e metadados

### Modelos novos

- `GrepMatch`, `GrepResult` — Resultados da busca textual exata
- `FilesystemHit`, `FilesystemResult` — Resultados do indice curado
- `MergedHit`, `MergedResult` — Resultados unificados de busca dual-path
- `CanonicalResult` — Texto canonical com contagem de tokens

### Exemplos

```python
# Busca textual exata
result = vg.grep("dispensa de licitacao")
for m in result:
    print(f"{m.span_id}: {m.matched_line}")

# Busca no indice curado
result = vg.filesystem_search("art. 75 da Lei 14.133")
for hit in result:
    print(f"[{hit.source}] {hit.breadcrumb}")

# Busca dual-path (hibrida + filesystem)
result = vg.merged("prazo para impugnacao do edital")
for hit in result:
    print(f"[{','.join(hit.sources)}] {hit.breadcrumb}: {hit.score:.2f}")
print(f"Mutual: {result.mutual_count} hits em ambas fontes")

# Texto canonical completo
doc = vg.read_canonical("LEI-14133-2021")
print(f"{doc.document_id}: {doc.token_count} tokens")

art = vg.read_canonical("LEI-14133-2021", span_id="ART-075")
print(art.text)
```

## [0.15.2] - 2026-03-01

### Adicionado

- **Lookup: Children Stitching** — dispositivos filhos e texto consolidado:
  - `LookupResult.children` — lista de `Hit` com filhos (paragrafos, incisos, alineas)
  - `LookupResult.stitched_text` — texto do caput + todos os filhos concatenados
  - Funciona para artigos (filhos: paragrafos + incisos), paragrafos (filhos: incisos) e incisos (filhos: alineas)
  - XML e Markdown atualizado com secoes `<dispositivos_filhos>` e `<texto_consolidado>`

- **Lookup: Batch** — multiplas referencias em uma chamada:
  - `vg.lookup(["Art. 18 da Lei 14.133", "Art. 9 da IN 65"])` — aceita lista (max 20)
  - Retorna `LookupResult` com `status="batch"` e `results: list[LookupResult]`
  - Iteravel: `for r in result: print(r.reference, r.status)`
  - Retrocompativel: `vg.lookup("Art. 18 da Lei 14.133")` continua funcionando
  - `AsyncVectorGov.lookup()` tambem aceita lista

### Exemplos

```python
# Children stitching — texto completo do artigo
result = vg.lookup("Art. 18 da Lei 14.133")
print(result.stitched_text)  # caput + todos os filhos
print(f"{len(result.children)} filhos")

# Batch lookup — multiplas referencias
results = vg.lookup([
    "Art. 18 da Lei 14.133",
    "Art. 9 da IN 65",
    "Art. 5 da IN 65",
])
for r in results:
    print(f"{r.reference}: {r.status} ({len(r.children)} filhos)")
```

## [0.15.0] - 2026-03-01

### Adicionado

- **Smart Search (`smart_search()`)** — Pipeline inteligente completo com analise de confianca:
  - Novo modelo `SmartSearchResult` (herda de `SearchResult`)
  - Campos extras: `confianca`, `raciocinio`, `tentativas`, `normas_presentes`
  - Cada hit inclui `nota_especialista`, `evidence_url`, `document_url`
  - Requer tier Premium (`TierError` se nao disponivel)

- **Busca Hibrida (`hybrid()`)** — Semantica + grafo de citacoes normativas:
  - Novo modelo `HybridResult` (herda de `BaseResult`)
  - Campos: `hits` (evidencias diretas), `graph_nodes` (expansao via grafo), `stats`
  - Parametros: `top_k`, `hops` (1-2), `graph_expansion` (bidirectional/forward), `token_budget`
  - Metodos herdados: `to_context()`, `to_xml()`, `to_messages()`, `to_prompt()`

- **Lookup de Dispositivo (`lookup()`)** — Resolucao de referencias normativas:
  - Novo modelo `LookupResult` (herda de `BaseResult`)
  - Resolucao de referencia textual para dispositivo exato (ex: "Art. 33 da Lei 14.133")
  - Contexto hierarquico: `match`, `parent`, `siblings`
  - Status: `found`, `not_found`, `ambiguous`, `parse_failed`
  - `LookupCandidate` para referencias ambiguas

- **Classe Base `BaseResult`** — ABC com campos e metodos comuns:
  - Campos: `query`, `total`, `latency_ms`, `cached`
  - Metodos: `to_context()`, `to_messages()`, `to_prompt()`, `to_xml()`, `__iter__()`, `__len__()`
  - `SearchResult`, `HybridResult`, `LookupResult` herdam dela

- **Excecao `TierError`** — Tier do plano nao inclui o recurso solicitado:
  - Lancada quando smart_search() e chamado sem tier Premium
  - Inclui `upgrade_url` opcional para pagina de upgrade

- **Cliente Assincrono `AsyncVectorGov`** — Mesma API, mas async/await:
  - Import: `from vectorgov import AsyncVectorGov`
  - Todos os metodos sao `async`: `await vg.search()`, `await vg.hybrid()`, etc.

- **Campos de Proveniencia nos Hits**:
  - `is_graph_expanded`, `hop`, `graph_score` — Origem no grafo
  - `is_parent`, `is_sibling`, `is_child_of_seed` — Relacao hierarquica
  - `source` — Origem do chunk: `seed`, `family`, `graph`

- **Campos de Curadoria nos Hits**:
  - `resumo_ia` — Resumo gerado por IA
  - `aliases` — Nomes alternativos do dispositivo
  - `ativo` — Se o dispositivo esta vigente

- **Campos de Verificabilidade nos Hits**:
  - `canonical_hash`, `canonical_start`, `canonical_end` — Rastreabilidade do texto
  - `page_number`, `bbox_x0`, `bbox_y0`, `bbox_x1`, `bbox_y1` — Localizacao no PDF

### Deprecado

- `ExpandedChunk` — Agora retornado como dict. Classe mantida com `DeprecationWarning`.
- `CitationExpansionStats` — Agora retornado como dict. Classe mantida com `DeprecationWarning`.
- `LookupMatch`, `LookupParent`, `LookupSibling`, `LookupResolved` — Usar `Hit` no lugar. Mantidos com `DeprecationWarning`.

### Alterado

- `SearchResult` agora herda de `BaseResult` (ABC)
- `pyproject.toml` version alinhada com `__init__.py` (`0.15.0`)

### Exemplos

```python
# Smart Search — pipeline turnkey
from vectorgov import VectorGov, TierError

vg = VectorGov(api_key="vg_xxx")

try:
    result = vg.smart_search("Quais os criterios de julgamento?")
    print(result.confianca)     # "ALTO", "MEDIO" ou "BAIXO"
    print(result.raciocinio)    # Texto do Juiz
    for hit in result:
        print(hit.nota_especialista)
except TierError:
    result = vg.search("criterios de julgamento", mode="precise")

# Busca Hibrida — Semantica + Grafo
result = vg.hybrid("Dispensa de licitacao por baixo valor", hops=2)
print(f"Evidencias diretas: {len(result.hits)}")
print(f"Expansao via grafo: {len(result.graph_nodes)}")
context = result.to_context()

# Lookup de Dispositivo
result = vg.lookup("Inc. III do Art. 9 da IN 58")
if result.status == "found":
    print(result.match.text)
    for sib in result.siblings:
        marker = ">" if sib.is_current else " "
        print(f"  {marker} {sib.span_id}")
```

## [0.14.0] - 2025-01-22

### Adicionado

- **Citation Expansion (Expansão de Citações)** - Expande automaticamente referências normativas encontradas nos resultados:
  - Novo parâmetro `expand_citations=True` no método `search()`
  - Novo parâmetro `citation_expansion_top_n` para limitar citações por chunk (default: 3)
  - Quando um chunk cita outro artigo/lei (ex: "art. 18 da Lei 14.133"), o sistema busca e retorna o texto citado
  - Novos modelos de dados:
    - `ExpandedChunk` - Chunk obtido via expansão de citação
    - `CitationExpansionStats` - Estatísticas de expansão
  - Novos campos em `SearchResult`:
    - `expanded_chunks: list[ExpandedChunk]` - Lista de chunks expandidos
    - `expansion_stats: CitationExpansionStats` - Métricas de expansão
  - Atualizado `to_context(include_expanded=True)` para incluir chunks expandidos

### Exemplo

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Busca com expansão de citações
results = vg.search(
    "Quando o ETP pode ser dispensado?",
    expand_citations=True,
    citation_expansion_top_n=3,
)

# Resultados originais
print(f"Hits originais: {len(results.hits)}")

# Chunks expandidos via citações
print(f"Chunks expandidos: {len(results.expanded_chunks)}")
for ec in results.expanded_chunks:
    print(f"  - {ec.node_id}: {ec.text[:100]}...")
    print(f"    Citado por: {ec.source_chunk_id}")
    print(f"    Citação original: '{ec.source_citation_raw}'")

# Estatísticas de expansão
if results.expansion_stats:
    stats = results.expansion_stats
    print(f"Citações encontradas: {stats.citations_scanned_count}")
    print(f"Citações resolvidas: {stats.citations_resolved_count}")
    print(f"Chunks expandidos: {stats.expanded_chunks_count}")
    print(f"Tempo de expansão: {stats.expansion_time_ms:.1f}ms")

# O contexto formatado inclui chunks expandidos
context = results.to_context()
# Seção "--- Referências Expandidas ---" adicionada automaticamente

# Para excluir chunks expandidos do contexto:
context = results.to_context(include_expanded=False)
```

### Benefícios da Expansão de Citações

| Benefício | Descrição |
|-----------|-----------|
| **Contexto Mais Rico** | LLM recebe o texto completo dos artigos citados |
| **Menos Alucinações** | Referências são verificadas e expandidas automaticamente |
| **Transparência** | `source_citation_raw` mostra a citação original |
| **Controle de Tokens** | `citation_expansion_top_n` limita expansões por chunk |
| **Deduplicação** | Mesma citação não é expandida múltiplas vezes |

### Novos Modelos

```python
@dataclass
class ExpandedChunk:
    chunk_id: str          # ID do chunk expandido (ex: 'LEI-14133-2021#ART-018')
    node_id: str           # Node ID canônico: leis:{document_id}#{span_id}
    text: str              # Texto do chunk expandido
    document_id: str       # ID do documento fonte
    span_id: str           # ID do dispositivo (ex: 'ART-018')
    device_type: str       # Tipo: article, paragraph, inciso, alinea
    source_chunk_id: str   # ID do chunk que citou este
    source_citation_raw: str  # Texto original da citação

@dataclass
class CitationExpansionStats:
    expanded_chunks_count: int      # Chunks expandidos com sucesso
    citations_scanned_count: int    # Citações encontradas nos hits
    citations_resolved_count: int   # Citações resolvidas para node_ids
    expansion_time_ms: float        # Tempo de expansão em ms
    skipped_self_references: int    # Auto-referências ignoradas
    skipped_duplicates: int         # Duplicatas ignoradas
    skipped_token_budget: int       # Excederam budget de tokens
```

### Melhorado

- **Formato de Contexto Estruturado** - `to_context()` agora divide claramente em seções para melhor compreensão do LLM:
  - **EVIDÊNCIA DIRETA** (resultados da busca) - Chunks retornados diretamente pela busca semântica
  - **TRECHOS CITADOS** (expansão por citação) - Chunks trazidos via Citation Expansion
  - Cada chunk expandido agora exibe metadados completos:
    - `CITADO POR`: source_chunk_id (qual chunk fez a citação)
    - `CITAÇÃO ORIGINAL`: source_citation_raw (texto da citação)
    - `ALVO (node_id)`: node_id canônico do chunk expandido
    - `FONTE`: document_id, span_id, device_type
  - Resumo de estatísticas ao final (controlável via `include_stats=True`)
  - Novo parâmetro `include_stats: bool = True` em `to_context()`

### Exemplo de Saída do `to_context()`

```
=== EVIDÊNCIA DIRETA (resultados da busca) ===
[1] Lei 14.133/2021, Art. 18
O estudo técnico preliminar será elaborado...

[2] IN 65/2021, Art. 5
A pesquisa de preços deve conter, no mínimo...

=== TRECHOS CITADOS (expansão por citação) ===
[XC-1] TRECHO CITADO (expansão por citação)
  CITADO POR: IN-65-2021#ART-005
  CITAÇÃO ORIGINAL: art. 18 da Lei 14.133
  ALVO (node_id): leis:LEI-14133-2021#ART-018
  FONTE: LEI-14133-2021, ART-018 (article)
Texto completo do art. 18 da Lei 14.133...

[Expansão: encontradas=3, resolvidas=2, expandidas=2, tempo=45ms]
```

### Benefício do Formato Estruturado

| Aspecto | Benefício |
|---------|-----------|
| **Clareza para o LLM** | Modelo entende origem de cada trecho |
| **Priorização** | Evidência direta tem precedência sobre trechos citados |
| **Rastreabilidade** | node_id permite identificação única do chunk |
| **Debugging** | Metadados facilitam verificação de qualidade |

## [0.13.0] - 2025-01-19

### Adicionado

- **Contagem de Tokens (Server-Side)** - Estimar tokens antes de enviar para o LLM:
  - `vg.estimate_tokens(content)` - Método no cliente para estimar tokens
  - Aceita `SearchResult` ou `str` como entrada
  - A contagem é feita no servidor usando tiktoken, garantindo precisão sem dependências extras no cliente
  - Novo modelo `TokenStats` com campos:
    - `context_tokens` - Tokens do contexto (hits formatados)
    - `system_tokens` - Tokens do system prompt
    - `query_tokens` - Tokens da query do usuário
    - `total_tokens` - Total de tokens (context + system + query)
    - `hits_count` - Número de hits incluídos no contexto
    - `char_count` - Número total de caracteres
    - `encoding` - Encoding usado (padrão: cl100k_base, compatível com GPT-4/Claude)
  - Exemplo `14_token_counting.py` com 6 casos de uso:
    - Estimar tokens de um SearchResult
    - Estimar tokens de texto simples
    - Usar system prompt customizado
    - Otimizar para limite de tokens
    - Estimativa de custo por query
    - Verificação antes de enviar ao OpenAI
- Sem dependências extras necessárias - processamento server-side via API

### Exemplo

```python
from vectorgov import VectorGov, TokenStats

vg = VectorGov(api_key="vg_xxx")
results = vg.search("O que é ETP?", top_k=5)

# Estimar tokens do resultado de busca
stats = vg.estimate_tokens(results)
print(f"Total: {stats.total_tokens} tokens")
print(f"Contexto: {stats.context_tokens} tokens")
print(f"System: {stats.system_tokens} tokens")
print(f"Query: {stats.query_tokens} tokens")

# Estimar tokens de texto simples
stats = vg.estimate_tokens("Texto qualquer para contar tokens")
print(f"Tokens: {stats.total_tokens}")

# Verificar limite do modelo
MODEL_LIMITS = {"gpt-4o": 128_000, "claude-sonnet-4": 200_000}
for model, limit in MODEL_LIMITS.items():
    status = "OK" if stats.total_tokens < limit else "EXCEDE"
    print(f"{model}: {status}")

# Otimizar para caber em um limite
MAX_TOKENS = 4000
if stats.total_tokens > MAX_TOKENS:
    # Reduzir top_k até caber
    for k in range(5, 0, -1):
        results = vg.search("O que é ETP?", top_k=k)
        stats = vg.estimate_tokens(results)
        if stats.total_tokens <= MAX_TOKENS:
            print(f"Com top_k={k}: {stats.total_tokens} tokens OK")
            break
```

## [0.12.0] - 2025-01-19

### Adicionado

- **Documentação: Auditoria e Segurança no README** - Seção expandida com:
  - Por que auditoria é importante (compliance, segurança, debugging, monitoramento, billing)
  - Explicação do isolamento/privacidade multi-tenant por API Key
  - Documentação detalhada de `get_audit_logs()` com casos de uso e campos retornados
  - Documentação detalhada de `get_audit_stats()` com métricas e metas ideais
  - Documentação de `get_audit_event_types()` para descoberta dinâmica de eventos

- **Documentação: Guia de Observabilidade e Auditoria** - Novo guia completo em `docs/guides/observability-audit.md`:
  - Documentação dos 3 métodos de auditoria: `get_audit_logs()`, `get_audit_stats()`, `get_audit_event_types()`
  - Tabelas de parâmetros com tipos, padrões e descrições
  - Tipos de eventos: `pii_detected`, `injection_detected`, `rate_limit_exceeded`, `auth_failed`, `validation_error`, etc.
  - Severidades (`info`, `warning`, `critical`) e categorias (`security`, `performance`, `validation`)
  - Modelos de dados: `AuditLog`, `AuditLogsResponse`, `AuditStats`
  - 5 casos de uso práticos: dashboard de monitoramento, alertas de segurança, compliance LGPD, debugging, rate limit
  - Boas práticas de monitoramento
  - Integração com ferramentas externas (JSON, Slack)
  - Seção de Observabilidade adicionada ao `docs/index.md`

- **Documentação: "Do Básico ao Avançado"** - Nova seção no README com guia progressivo de adoção:
  - **Nível 1**: Mínimo necessário (`search()` + API key)
  - **Nível 2**: Integração com LLM (`to_messages()`)
  - **Nível 3**: Sistema de feedback (`feedback()`, `store_response()`)
  - **Nível 4**: Filtros de busca (tipo, ano, órgão)
  - **Nível 5**: Modos de performance (`fast`, `balanced`, `precise`)
  - **Nível 6**: Controle de custos com prompts customizados
  - **Nível 7**: Auditoria e rastreabilidade (`get_audit_logs()`)
  - **Nível 8**: Integrações avançadas (LangChain, LangGraph, MCP)
  - **Exemplo completo**: Função de produção usando todas as features

### Removido

- **Método `ask_stream()` removido** - O endpoint `/ask/stream` agora é restrito apenas para administradores. Desenvolvedores devem usar:
  - `search()` para obter contexto + `to_messages()` para enviar ao LLM de sua escolha
  - Integrações com Ollama, Transformers, LangChain para RAG local
  - Function Calling para agentes com OpenAI/Anthropic/Google

- **Modelo `StreamChunk` removido** - Não é mais necessário sem o método `ask_stream()`

### Migração

```python
# ANTES (v0.10.x) - ask_stream()
for chunk in vg.ask_stream("O que é ETP?"):
    if chunk.type == "token":
        print(chunk.content, end="")

# DEPOIS - Use seu próprio LLM
results = vg.search("O que é ETP?")
messages = results.to_messages("O que é ETP?")

# Com OpenAI
response = openai.chat.completions.create(model="gpt-4o", messages=messages, stream=True)
for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")

# Com Ollama (gratuito/local)
from vectorgov.integrations.ollama import VectorGovOllama
rag = VectorGovOllama(vg, model="qwen3:8b")
result = rag.ask("O que é ETP?")
print(result.answer)
```

## [0.10.0] - 2025-01-18

### Adicionado

- **Logs de Auditoria** - Novos métodos para acessar logs de segurança e compliance:
  - `get_audit_logs()` - Lista logs de auditoria com filtros:
    - Filtra por `event_type`, `event_category`, `severity`
    - Filtra por período (`start_date`, `end_date`)
    - Paginação com `page` e `limit`
  - `get_audit_stats(days)` - Estatísticas agregadas de auditoria:
    - Total de eventos no período
    - Eventos por tipo, severidade e categoria
    - Contagem de bloqueios e avisos
  - `get_audit_event_types()` - Lista tipos de eventos disponíveis

- **Novos modelos de dados**:
  - `AuditLog` - Log individual com campos:
    - `id`, `event_type`, `event_category`, `severity`
    - `created_at`, `query_text`, `detection_types`
    - `risk_score`, `action_taken`, `endpoint`
    - `client_ip`, `user_agent`, `details`
  - `AuditLogsResponse` - Resposta paginada de logs
  - `AuditStats` - Estatísticas agregadas com contadores
  - `AuditEventTypes` - Lista de tipos de eventos

### Exemplo

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Listar logs de segurança
logs = vg.get_audit_logs(severity="warning", limit=50)
for log in logs.logs:
    print(f"{log.created_at}: {log.event_type} - {log.action_taken}")

# Estatísticas dos últimos 30 dias
stats = vg.get_audit_stats(days=30)
print(f"Total eventos: {stats.total_events}")
print(f"Bloqueados: {stats.blocked_count}")
print(f"Avisos: {stats.warning_count}")

# Tipos de eventos disponíveis
types = vg.get_audit_event_types()
print(f"Tipos: {types.types}")
```

### Tipos de Eventos de Auditoria

| Tipo | Descrição |
|------|-----------|
| `pii_detected` | Dados pessoais detectados na query |
| `injection_blocked` | Tentativa de injeção bloqueada |
| `rate_limit_exceeded` | Rate limit excedido |
| `auth_failed` | Falha de autenticação |
| `validation_error` | Erro de validação |

### Severidades

| Severidade | Descrição |
|------------|-----------|
| `info` | Informativo |
| `warning` | Aviso (ação preventiva) |
| `critical` | Crítico (requisição bloqueada) |

## [0.9.0] - 2025-01-17

### ⚠️ BREAKING CHANGE

- **Cache desabilitado por padrão** - Por questões de privacidade, o cache semântico agora vem **desabilitado por padrão** em todos os modos de busca.

### Contexto

O VectorGov utiliza um **cache semântico compartilhado** entre todos os clientes da API. Isso significa que:
- Suas perguntas podem ser armazenadas no cache
- Suas respostas podem ser servidas a outros clientes com perguntas similares
- Você pode receber respostas já geradas por outros clientes

### Migração

```python
# ANTES (v0.8.x) - Cache habilitado por padrão
results = vg.search("O que é ETP?")  # use_cache=True implícito

# DEPOIS (v0.9.0) - Cache desabilitado por padrão
results = vg.search("O que é ETP?")  # use_cache=False implícito

# Para habilitar cache explicitamente (aceita trade-off de privacidade)
results = vg.search("O que é ETP?", use_cache=True)
```

### Adicionado

- **Método `store_response()`** - Permite salvar respostas de LLMs externos (OpenAI, Gemini, Claude, etc.) no cache do VectorGov:
  - Habilita feedback (like/dislike) para qualquer LLM
  - Retorna `query_hash` para usar no método `feedback()`
  - Útil para coletar dados de treinamento de modelos
  ```python
  # Exemplo de uso
  results = vg.search("O que é ETP?")
  response = openai.chat.completions.create(model="gpt-4o", messages=results.to_messages())
  answer = response.choices[0].message.content

  # Salva para feedback
  stored = vg.store_response(query="O que é ETP?", answer=answer, provider="OpenAI", model="gpt-4o")
  vg.feedback(stored.query_hash, like=True)  # Agora funciona!
  ```

- **Modelo `StoreResponseResult`** - Retorno do método `store_response()` com campos:
  - `success: bool` - Se a resposta foi armazenada
  - `query_hash: str` - Hash para usar em `feedback()`
  - `message: str` - Mensagem de status

- **Exemplo `15_feedback_external_llm.py`** - Demonstra fluxo completo de feedback com LLM externo

- **Parâmetro `use_cache`** no método `search()`:
  - `use_cache=True` - Habilita cache (menor latência, menor privacidade)
  - `use_cache=False` - Desabilita cache (padrão, maior privacidade)
  - Não especificado - Usa padrão do modo (agora `False`)

- **Documentação de privacidade** - Nova seção no README explicando:
  - Como funciona o cache compartilhado
  - Trade-offs entre latência e privacidade
  - Recomendações de uso por cenário

### Alterado

- `MODE_CONFIG` - Todos os modos agora têm `use_cache=False` por padrão:
  - `SearchMode.FAST` - `use_cache=False`
  - `SearchMode.BALANCED` - `use_cache=False`
  - `SearchMode.PRECISE` - `use_cache=False`

### Recomendações de Uso

| Cenário | use_cache | Motivo |
|---------|-----------|--------|
| Dados sensíveis | `False` (padrão) | Privacidade máxima |
| Perguntas genéricas | `True` | Menor latência, perguntas públicas |
| Produção multi-tenant | `False` | Isolamento entre clientes |
| Demo/Testes | `True` | Aproveita cache existente |

## [0.8.1] - 2025-01-13

### Alterado

- **Limite de top_k aumentado** - O parâmetro `top_k` agora aceita valores de 1 a 50 (antes: 1-20)
  - `search(query, top_k=50)` - Até 50 chunks de contexto
  - Padrão continua sendo 5

## [0.8.0] - 2025-01-10

### Adicionado

- **Gerenciamento de Documentos** - Novos métodos para gerenciar a base de conhecimento:
  - `list_documents(page, limit)` - Lista documentos disponíveis (paginado)
  - `get_document(document_id)` - Detalhes de um documento específico
  - `upload_pdf(file, metadata)` - Upload de PDF **(Admin)**
  - `get_ingest_status(task_id)` - Status da ingestão
  - `start_enrichment(document_id)` - Inicia enriquecimento **(Admin)**
  - `get_enrichment_status(task_id)` - Status do enriquecimento
  - `delete_document(document_id)` - Exclui documento **(Admin)**

- **Novos modelos de dados**:
  - `DocumentSummary` - Resumo de documento com progresso de enriquecimento
  - `DocumentsResponse` - Resposta paginada de lista de documentos
  - `UploadResponse` - Resposta de upload com task_id
  - `IngestStatus` - Status de ingestão (pending/processing/completed/failed)
  - `EnrichStatus` - Status de enriquecimento com progresso detalhado
  - `DeleteResponse` - Resposta de exclusão

- **Novos métodos HTTP internos**:
  - `HTTPClient.delete()` - Requisições DELETE
  - `HTTPClient.post_multipart()` - Upload de arquivos multipart/form-data

### Permissões

| Operação | Permissão |
|----------|-----------|
| Listar/consultar documentos | Todos |
| Ver status de tarefas | Todos |
| Upload, enriquecimento, exclusão | **Admin** |


## [0.7.0] - 2025-01-08

### Adicionado

- Método `stream()` no cliente HTTP interno para SSE (uso interno)

## [0.6.0] - 2025-01-08

### Adicionado

- **Integração Ollama** - RAG com modelos locais via Ollama:
  - Novo módulo `vectorgov.integrations.ollama`
  - `create_rag_pipeline()` - Cria pipeline RAG simples com Ollama
  - `VectorGovOllama` - Classe completa com respostas estruturadas
  - `OllamaResponse` - Resposta com answer, sources, latency, model
  - `check_ollama_available()` - Verifica se Ollama está rodando
  - `list_models()` - Lista modelos disponíveis no Ollama
  - `generate()` - Função de baixo nível para geração
  - `get_recommended_models()` - Lista modelos recomendados
  - `chat()` - Chat com histórico de mensagens
  - Exemplo `13_ollama_local.py` com 6 casos de uso
- Sem dependências extras necessárias (usa apenas urllib)
- Compatível com qualquer modelo do Ollama (qwen, llama, mistral, etc.)

### Alterado

- Documentação atualizada com seção Ollama

## [0.5.0] - 2025-01-08

### Adicionado

- **Integração HuggingFace Transformers** - RAG com modelos locais gratuitos:
  - Novo módulo `vectorgov.integrations.transformers`
  - `create_rag_pipeline()` - Cria pipeline RAG simples (função)
  - `VectorGovRAG` - Classe completa com histórico e fontes
  - `RAGResponse` - Resposta estruturada com answer, sources, latency
  - `format_prompt_for_transformers()` - Formata prompts para diferentes templates
  - `get_recommended_models()` - Lista modelos recomendados para português
  - `estimate_vram_usage()` - Estima uso de VRAM por modelo
  - Exemplo `12_transformers_local.py` com 6 casos de uso
  - Suporte a modelos quantizados (4-bit com bitsandbytes)
  - Suporte a CPU-only para ambientes sem GPU
- Extra de instalação: `pip install 'vectorgov[transformers]'`
- Documentação completa com tabela de modelos recomendados

### Alterado

- Módulo `all` agora inclui dependências Transformers (torch, accelerate)

## [0.4.0] - 2025-01-08

### Adicionado

- **Integração LangGraph** - Framework para construir agentes com estado:
  - Novo módulo `vectorgov.integrations.langgraph`
  - `create_vectorgov_tool()` - Cria ferramenta LangChain para agentes ReAct
  - `create_retrieval_node()` - Nó de retrieval para grafos customizados
  - `create_legal_rag_graph()` - Grafo RAG pré-configurado
  - `VectorGovState` - TypedDict para gerenciamento de estado
  - Exemplo `10_langgraph_react.py` com 3 casos de uso
- **Integração Google ADK** - Agent Development Kit do Google:
  - Novo módulo `vectorgov.integrations.google_adk`
  - `create_search_tool()` - Ferramenta de busca para agentes ADK
  - `create_list_documents_tool()` - Ferramenta para listar documentos
  - `create_get_article_tool()` - Ferramenta para obter artigo específico
  - `VectorGovToolset` - Classe que agrupa todas as ferramentas
  - `create_legal_agent()` - Helper para criar agente pré-configurado
  - Exemplo `11_google_adk_agent.py` com 4 casos de uso
- Extras de instalação:
  - `pip install 'vectorgov[langgraph]'`
  - `pip install 'vectorgov[google-adk]'`

### Alterado

- Módulo `all` agora inclui dependências LangGraph e Google ADK
- Documentação atualizada com seções de LangGraph e Google ADK

## [0.3.0] - 2025-01-08

### Adicionado

- **Servidor MCP** - Integração com Claude Desktop, Cursor e outras ferramentas MCP:
  - Novo módulo `vectorgov.mcp` com servidor MCP completo
  - Comando CLI `vectorgov-mcp` para executar o servidor
  - Suporte a `python -m vectorgov.mcp`
  - Ferramentas MCP:
    - `search_legislation` - Busca semântica em legislação
    - `list_available_documents` - Lista documentos disponíveis
    - `get_article_text` - Obtém texto de artigo específico
  - Recurso MCP `legislation://info` com informações da base
  - Documentação de configuração no Claude Desktop
- Extra de instalação: `pip install 'vectorgov[mcp]'`

### Alterado

- Módulo `all` agora inclui dependência MCP

## [0.2.0] - 2025-01-08

### Adicionado

- **Function Calling** - Integração com ferramentas de LLMs:
  - `vg.to_openai_tool()` - Ferramenta para OpenAI Function Calling
  - `vg.to_anthropic_tool()` - Ferramenta para Claude Tools
  - `vg.to_google_tool()` - Ferramenta para Gemini Function Calling
  - `vg.execute_tool_call()` - Executa tool_call de qualquer provedor
- **LangChain Integration** - Novo módulo `vectorgov.integrations.langchain`:
  - `VectorGovRetriever` - Retriever compatível com LangChain
  - `VectorGovTool` - Ferramenta para agentes LangChain
  - `to_langchain_documents()` - Converte resultados para Documents
- Novos exemplos:
  - `08_function_calling_openai.py` - Agente OpenAI com VectorGov como tool
  - `09_langchain_retriever.py` - Integração completa com LangChain
- Extras de instalação: `pip install 'vectorgov[langchain]'` ou `'vectorgov[all]'`

### Alterado

- Módulo `integrations` agora é a casa de todas as integrações com frameworks
- JSON Schema padronizado para Function Calling em `TOOL_SCHEMA`

## [0.1.2] - 2025-01-08

### Adicionado

- Exemplo completo de integração com Anthropic Claude (`examples/04_claude.py`)
- Instruções de instalação das bibliotecas de LLM no README (openai, google-generativeai, anthropic)

### Alterado

- Exemplo do Claude agora usa `system` parameter separado (formato correto da API)
- Melhorada documentação de integração com todos os LLMs

## [0.1.1] - 2025-01-08

### Alterado

- Atualizado exemplo do Google Gemini para usar `gemini-2.0-flash`
- Exemplo do Gemini agora usa `system_instruction` nativo
- Melhorada documentação de integração com LLMs

## [0.1.0] - 2025-01-07

### Adicionado

- Classe principal `VectorGov` para conexão com a API
- Método `search()` com suporte a:
  - Modos de busca: `fast`, `balanced`, `precise`
  - Parâmetro `top_k` (1-20)
  - Filtros por tipo, ano, órgão
- Classe `SearchResult` com:
  - Método `to_context()` para string formatada
  - Método `to_messages()` para OpenAI/Claude
  - Método `to_prompt()` para Gemini
- Formatters auxiliares:
  - `to_langchain_docs()` para LangChain
  - `to_llamaindex_nodes()` para LlamaIndex
  - `format_citations()` para citações formatadas
- System prompts pré-definidos: `default`, `concise`, `detailed`, `chatbot`
- Método `feedback()` para enviar like/dislike
- Exceções customizadas: `AuthError`, `RateLimitError`, `ValidationError`
- Suporte a variável de ambiente `VECTORGOV_API_KEY`
- Documentação completa com exemplos
- CI/CD com GitHub Actions

### Segurança

- API key validada no formato `vg_*`
- Retry automático com backoff exponencial
- Timeout configurável

[Unreleased]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.15.0...HEAD
[0.15.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.10.0...v0.12.0
[0.10.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/euteajudo/vectorgov-sdk/releases/tag/v0.1.0
