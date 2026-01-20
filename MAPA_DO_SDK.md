# 🗺️ MAPA DO SDK VECTORGOV

> **Versão**: 0.13.0
> **Data**: Janeiro 2025
> **Objetivo**: Documentação completa da arquitetura e funcionamento do SDK Python VectorGov

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura de Alto Nível](#arquitetura-de-alto-nível)
3. [Estrutura de Arquivos](#estrutura-de-arquivos)
4. [Módulos Principais](#módulos-principais)
5. [Fluxo de Dados](#fluxo-de-dados)
6. [Integrações](#integrações)
7. [Modelos de Dados](#modelos-de-dados)
8. [Tratamento de Erros](#tratamento-de-erros)
9. [Configurações](#configurações)
10. [Exemplos de Uso](#exemplos-de-uso)
11. [Links Úteis e Documentação para LLMs](#links-úteis)

---

## 📖 Visão Geral

O VectorGov SDK é uma biblioteca Python que permite integração simples e eficiente com a API VectorGov para busca semântica em documentos jurídicos brasileiros.

### Características Principais

| Característica | Descrição |
|----------------|-----------|
| **Zero Dependências** | Cliente HTTP usando apenas `urllib` da biblioteca padrão |
| **Type Hints** | Tipagem completa para melhor experiência de desenvolvimento |
| **Integrações** | Suporte nativo para OpenAI, Anthropic, Google, LangChain, Ollama, Transformers |
| **MCP Server** | Servidor Model Context Protocol para Claude Desktop e Cursor |
| **Retry Automático** | Retry com backoff exponencial para resiliência |
| **Auditoria** | Logs e estatísticas de eventos de segurança (PII, injeções) |

### Modelo de Negócio

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MODELO VECTORGOV                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Desenvolvedor                   VectorGov                  LLM Escolhido  │
│   ┌─────────┐                    ┌─────────┐                ┌─────────────┐ │
│   │ Pergunta│───────────────────▶│  Busca  │                │  OpenAI     │ │
│   │         │                    │ Semântica│                │  Gemini     │ │
│   └─────────┘                    │ (Milvus) │                │  Claude     │ │
│                                  └────┬─────┘                │  Llama      │ │
│                                       │                      │  Qwen       │ │
│                                       │ Contexto             │  Ollama     │ │
│                                       │ Relevante            └──────┬──────┘ │
│                                       │                             │        │
│   ┌─────────┐                    ┌────▼─────┐                ┌──────▼──────┐ │
│   │Resposta │◀───────────────────│to_msgs() │────────────────│    LLM      │ │
│   │ Final   │                    │to_context│                │  Inference  │ │
│   └─────────┘                    └──────────┘                └─────────────┘ │
│                                                                             │
│   O SDK fornece CONTEXTO JURÍDICO, o desenvolvedor escolhe o LLM.          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARQUITETURA DO SDK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         CAMADA DE CLIENTE                           │   │
│   │                                                                     │   │
│   │   ┌─────────────┐    ┌──────────────┐    ┌───────────────────────┐ │   │
│   │   │  VectorGov  │    │   HTTPClient │    │     SDKConfig         │ │   │
│   │   │  (client.py)│───▶│  (_http.py)  │    │    (config.py)        │ │   │
│   │   │             │    │              │    │                       │ │   │
│   │   │ - search()  │    │ - request()  │    │ - base_url            │ │   │
│   │   │ - feedback()│    │ - get()      │    │ - timeout             │ │   │
│   │   │ - upload()  │    │ - stream()   │    │ - default_top_k       │ │   │
│   │   │ - upload()  │    │ - post()     │    │ - default_mode        │ │   │
│   │   └─────────────┘    └──────────────┘    └───────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│                                       │ HTTPS                               │
│                                       ▼                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         API VECTORGOV                               │   │
│   │                   https://vectorgov.io/api/v1                       │   │
│   │                                                                     │   │
│   │ /sdk/search  /sdk/documents  /sdk/feedback  /sdk/audit  /sdk/health  /sdk/tokens │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                       CAMADA DE INTEGRAÇÕES                         │   │
│   │                                                                     │   │
│   │   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │   │
│   │   │  tools.py  │ │langchain.py│ │langgraph.py│ │ google_adk.py  │  │   │
│   │   │            │ │            │ │            │ │                │  │   │
│   │   │ OpenAI     │ │ Retriever  │ │ ToolNode   │ │ ADK Toolset    │  │   │
│   │   │ Anthropic  │ │ Tool       │ │ RAG Graph  │ │ Agent Helper   │  │   │
│   │   │ Google     │ │ Docs       │ │ State      │ │                │  │   │
│   │   └────────────┘ └────────────┘ └────────────┘ └────────────────┘  │   │
│   │                                                                     │   │
│   │   ┌────────────┐ ┌────────────┐ ┌────────────────────────────────┐ │   │
│   │   │  ollama.py │ │transformers│ │         mcp/server.py          │ │   │
│   │   │            │ │    .py     │ │                                │ │   │
│   │   │ RAG Local  │ │ RAG Local  │ │ MCP Server para Claude Desktop │ │   │
│   │   │ Modelos    │ │ HuggingFace│ │ e Cursor IDE                   │ │   │
│   │   └────────────┘ └────────────┘ └────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos

```
vectorgov-sdk/
├── src/vectorgov/
│   │
│   ├── __init__.py              # Exports públicos do SDK
│   │   └── Exporta: VectorGov, SearchResult, Hit, Metadata, SearchMode,
│   │                exceções, formatters
│   │
│   ├── client.py                # Cliente principal (597 linhas)
│   │   └── class VectorGov:
│   │       ├── search()         # Busca semântica
│   │       ├── feedback()       # Envio de feedback
│   │       ├── store_response() # Salva resposta de LLM externo
│   │       ├── to_openai_tool() # Function calling OpenAI
│   │       ├── to_anthropic_tool()
│   │       ├── to_google_tool()
│   │       ├── execute_tool_call()
│   │       ├── list_documents() # Gestão de documentos
│   │       ├── get_document()
│   │       ├── upload_pdf()
│   │       ├── get_ingest_status()
│   │       ├── start_enrichment()
│   │       ├── get_enrichment_status()
│   │       ├── delete_document()
│   │       ├── get_audit_logs()    # Logs de auditoria
│   │       ├── get_audit_stats()   # Estatísticas de auditoria
│   │       ├── get_health()        # Status do SDK e guardrails
│   │       └── estimate_tokens()   # Estimativa de tokens (v0.13.0)
│   │
│   ├── _http.py                 # Cliente HTTP interno (265 linhas)
│   │   └── class HTTPClient:
│   │       ├── request()        # Requisição genérica
│   │       ├── get()            # GET
│   │       ├── post()           # POST
│   │       ├── delete()         # DELETE
│   │       ├── stream()         # Streaming SSE
│   │       └── post_multipart() # Upload de arquivos
│   │
│   ├── models.py                # Modelos de dados (425 linhas)
│   │   ├── class Metadata       # Metadados do documento
│   │   ├── class Hit            # Resultado individual
│   │   ├── class SearchResult   # Resultado completo
│   │   │   ├── to_context()     # Converte para string
│   │   │   ├── to_messages()    # Formato chat
│   │   │   └── to_prompt()      # Formato prompt único
│   │   ├── class DocumentSummary
│   │   ├── class DocumentsResponse
│   │   ├── class UploadResponse
│   │   ├── class IngestStatus
│   │   ├── class EnrichStatus
│   │   ├── class DeleteResponse
│   │   ├── class AuditLog          # Log de auditoria
│   │   ├── class AuditLogsResponse # Resposta paginada de logs
│   │   ├── class AuditStats        # Estatísticas agregadas
│   │   └── class TokenStats        # Estatísticas de tokens (v0.13.0)
│   │
│   ├── config.py                # Configurações (106 linhas)
│   │   ├── class SearchMode     # Enum: FAST, BALANCED, PRECISE
│   │   ├── class DocumentType   # Enum: LEI, DECRETO, IN...
│   │   ├── class SDKConfig      # Configuração global
│   │   ├── SYSTEM_PROMPTS       # Prompts pré-definidos
│   │   └── MODE_CONFIG          # Configuração por modo
│   │
│   ├── exceptions.py            # Exceções (80 linhas)
│   │   ├── class VectorGovError # Base
│   │   ├── class AuthError      # 401 - API key inválida
│   │   ├── class RateLimitError # 429 - Rate limit
│   │   ├── class ValidationError# 400 - Parâmetros inválidos
│   │   ├── class ServerError    # 500 - Erro interno
│   │   ├── class ConnectionError# Conexão falhou
│   │   └── class TimeoutError   # Timeout
│   │
│   ├── formatters.py            # Formatadores (180 linhas)
│   │   ├── to_langchain_docs()  # Converte para LangChain
│   │   ├── to_llamaindex_nodes()# Converte para LlamaIndex
│   │   ├── format_citations()   # Formata citações
│   │   └── create_rag_prompt()  # Cria prompt RAG
│   │
│   ├── integrations/
│   │   │
│   │   ├── __init__.py          # Exports de integrações
│   │   │
│   │   ├── tools.py             # Function Calling (196 linhas)
│   │   │   ├── TOOL_NAME        # Nome da ferramenta
│   │   │   ├── TOOL_DESCRIPTION # Descrição
│   │   │   ├── TOOL_SCHEMA      # JSON Schema
│   │   │   ├── to_openai_tool() # Formato OpenAI
│   │   │   ├── to_anthropic_tool()
│   │   │   ├── to_google_tool()
│   │   │   ├── parse_tool_arguments()
│   │   │   └── format_tool_response()
│   │   │
│   │   ├── langchain.py         # LangChain (294 linhas)
│   │   │   ├── class VectorGovRetriever  # BaseRetriever
│   │   │   ├── class VectorGovTool       # BaseTool
│   │   │   └── to_langchain_documents()
│   │   │
│   │   ├── langgraph.py         # LangGraph (415 linhas)
│   │   │   ├── class VectorGovState      # TypedDict para grafos
│   │   │   ├── create_vectorgov_tool()   # Tool para agentes
│   │   │   ├── create_retrieval_node()   # Nó de retrieval
│   │   │   └── create_legal_rag_graph()  # Grafo RAG completo
│   │   │
│   │   ├── google_adk.py        # Google ADK (433 linhas)
│   │   │   ├── create_search_tool()      # Ferramenta de busca
│   │   │   ├── create_list_documents_tool()
│   │   │   ├── create_get_article_tool()
│   │   │   ├── class VectorGovToolset    # Conjunto de ferramentas
│   │   │   └── create_legal_agent()      # Agente pré-configurado
│   │   │
│   │   ├── ollama.py            # Ollama (513 linhas)
│   │   │   ├── check_ollama_available()
│   │   │   ├── list_models()
│   │   │   ├── generate()               # Geração de texto
│   │   │   ├── create_rag_pipeline()    # Pipeline simples
│   │   │   ├── class VectorGovOllama    # Classe completa
│   │   │   └── get_recommended_models()
│   │   │
│   │   └── transformers.py      # HuggingFace (462 linhas)
│   │       ├── format_prompt_for_transformers()
│   │       ├── create_rag_pipeline()
│   │       ├── class VectorGovRAG       # Classe completa
│   │       ├── class RAGResponse        # Resposta estruturada
│   │       ├── get_recommended_models()
│   │       └── estimate_vram_usage()
│   │
│   └── mcp/
│       │
│       ├── __init__.py          # Exports MCP
│       │
│       ├── __main__.py          # Entry point CLI
│       │   └── Permite: python -m vectorgov.mcp
│       │
│       └── server.py            # Servidor MCP (347 linhas)
│           ├── create_server()  # Cria FastMCP
│           ├── run_server()     # Executa servidor
│           ├── main()           # Entry point
│           │
│           └── Tools expostas:
│               ├── search_legislation()
│               ├── list_available_documents()
│               └── get_article_text()
│
├── tests/
│   └── test_client.py           # Testes do cliente
│
├── examples/
│   ├── 01_basic.py              # Uso básico
│   ├── 02_openai.py             # Integração OpenAI
│   ├── 03_gemini.py             # Integração Google Gemini
│   ├── 04_claude.py             # Integração Anthropic Claude
│   ├── 08_function_calling_openai.py
│   ├── 09_langchain_retriever.py
│   ├── 10_langgraph_react.py
│   ├── 11_google_adk_agent.py
│   └── 12_transformers_local.py
│
├── pyproject.toml               # Configuração do pacote
├── README.md                    # Documentação principal
└── CHANGELOG.md                 # Histórico de versões
```

---

## 🔧 Módulos Principais

### 1. Cliente Principal (`client.py`)

O `VectorGov` é a classe principal do SDK, responsável por todas as interações com a API.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            class VectorGov                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INICIALIZAÇÃO                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ __init__(api_key, base_url, timeout, default_top_k, default_mode)   │   │
│  │                                                                     │   │
│  │ Parâmetros:                                                         │   │
│  │ - api_key: str       # Chave API (ou env VECTORGOV_API_KEY)        │   │
│  │ - base_url: str      # URL base (default: https://vectorgov.io)    │   │
│  │ - timeout: int       # Timeout em segundos (default: 30)           │   │
│  │ - default_top_k: int # Resultados padrão (default: 5)              │   │
│  │ - default_mode: str  # Modo padrão (default: balanced)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MÉTODOS DE BUSCA                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ search(query, top_k, mode, filters) -> SearchResult                 │   │
│  │                                                                     │   │
│  │ - query: str          # Pergunta (3-1000 caracteres)               │   │
│  │ - top_k: int          # 1-50 resultados                            │   │
│  │ - mode: SearchMode    # fast, balanced, precise                    │   │
│  │ - filters: dict       # tipo, ano, orgao                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FUNCTION CALLING                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ to_openai_tool() -> dict      # Formato OpenAI                     │   │
│  │ to_anthropic_tool() -> dict   # Formato Anthropic                  │   │
│  │ to_google_tool() -> dict      # Formato Gemini                     │   │
│  │ execute_tool_call(tool_call, mode) -> str                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  GESTÃO DE DOCUMENTOS                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ list_documents(page, limit) -> DocumentsResponse                   │   │
│  │ get_document(document_id) -> DocumentSummary                       │   │
│  │ upload_pdf(file_path, tipo, numero, ano) -> UploadResponse         │   │
│  │ get_ingest_status(task_id) -> IngestStatus                         │   │
│  │ start_enrichment(document_id) -> dict                              │   │
│  │ get_enrichment_status(task_id) -> EnrichStatus                     │   │
│  │ delete_document(document_id) -> DeleteResponse                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FEEDBACK E UTILITÁRIOS                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ feedback(query_id, like) -> bool                                   │   │
│  │ get_system_prompt(style) -> str                                    │   │
│  │ available_prompts -> list[str]                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AUDITORIA E MONITORAMENTO (v0.10.0)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ get_audit_logs(days, severity, event_type, limit, page)            │   │
│  │   -> AuditLogsResponse                                             │   │
│  │                                                                     │   │
│  │ - days: int          # Período em dias (default: 7)                │   │
│  │ - severity: str      # info, warning, critical                     │   │
│  │ - event_type: str    # pii_detected, injection_blocked, etc.       │   │
│  │ - limit: int         # Máximo de logs (default: 50)                │   │
│  │ - page: int          # Página para paginação                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ get_audit_stats(days) -> AuditStats                                │   │
│  │                                                                     │   │
│  │ Retorna estatísticas agregadas:                                    │   │
│  │ - total_events, blocked_count, warning_count                       │   │
│  │ - events_by_type, events_by_severity, events_by_category           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ESTIMATIVA DE TOKENS (v0.13.0)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ estimate_tokens(source, query, system_prompt) -> TokenStats        │   │
│  │                                                                     │   │
│  │ Estima tokens que serão usados em uma chamada LLM.                 │   │
│  │ A contagem é feita no servidor usando tiktoken (cl100k_base).      │   │
│  │                                                                     │   │
│  │ Parâmetros:                                                         │   │
│  │ - source: SearchResult | str  # Resultado de busca ou texto        │   │
│  │ - query: str                  # Query do usuário (opcional)        │   │
│  │ - system_prompt: str          # System prompt (opcional)           │   │
│  │                                                                     │   │
│  │ Retorna TokenStats com:                                            │   │
│  │ - context_tokens: int         # Tokens do contexto                 │   │
│  │ - system_tokens: int          # Tokens do system prompt            │   │
│  │ - query_tokens: int           # Tokens da query                    │   │
│  │ - total_tokens: int           # Total (context + system + query)   │   │
│  │ - hits_count: int             # Número de hits no contexto         │   │
│  │ - char_count: int             # Total de caracteres                │   │
│  │ - encoding: str               # Encoding usado (cl100k_base)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Cliente HTTP (`_http.py`)

Cliente HTTP minimalista sem dependências externas.

| Método | Descrição | Uso |
|--------|-----------|-----|
| `request(method, path, data, params)` | Requisição genérica | Base para outros métodos |
| `get(path, params)` | HTTP GET | Listagem, status |
| `post(path, data)` | HTTP POST | Busca, criação |
| `delete(path, params)` | HTTP DELETE | Exclusão |
| `post_multipart(path, files, data)` | Upload multipart | Upload de PDFs |

**Características**:
- Retry automático com backoff exponencial
- Timeout configurável
- Conversão automática de erros HTTP para exceções

### 3. Modelos de Dados (`models.py`)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MODELOS DE DADOS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BUSCA                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  SearchResult                                                         │ │
│  │  ├── query: str           # Pergunta original                        │ │
│  │  ├── hits: list[Hit]      # Lista de resultados                      │ │
│  │  ├── total: int           # Total encontrado                         │ │
│  │  ├── latency_ms: int      # Tempo de resposta                        │ │
│  │  ├── cached: bool         # Se veio do cache                         │ │
│  │  ├── query_id: str        # ID para feedback                         │ │
│  │  ├── mode: str            # Modo usado                               │ │
│  │  │                                                                   │ │
│  │  └── Métodos:                                                        │ │
│  │      ├── to_context(max_chars) -> str                                │ │
│  │      ├── to_messages(query, system_prompt) -> list[dict]             │ │
│  │      ├── to_prompt(query, system_prompt) -> str                      │ │
│  │      └── to_dict() -> dict                                           │ │
│  │                                                                       │ │
│  │  Hit                                                                  │ │
│  │  ├── text: str            # Texto do chunk                           │ │
│  │  ├── score: float         # Relevância (0-1)                         │ │
│  │  ├── source: str          # Fonte formatada                          │ │
│  │  ├── metadata: Metadata   # Metadados completos                      │ │
│  │  ├── chunk_id: str        # ID interno                               │ │
│  │  └── context: str         # Contexto adicional                       │ │
│  │                                                                       │ │
│  │  Metadata                                                             │ │
│  │  ├── document_type: str   # lei, decreto, in...                      │ │
│  │  ├── document_number: str # Número do documento                      │ │
│  │  ├── year: int            # Ano                                      │ │
│  │  ├── article: str         # Número do artigo                         │ │
│  │  ├── paragraph: str       # Parágrafo                                │ │
│  │  ├── item: str            # Inciso                                   │ │
│  │  └── orgao: str           # Órgão emissor                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  DOCUMENTOS                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  DocumentSummary          # Resumo de documento                      │ │
│  │  ├── document_id: str                                                │ │
│  │  ├── tipo_documento: str                                             │ │
│  │  ├── numero: str                                                     │ │
│  │  ├── ano: int                                                        │ │
│  │  ├── titulo: str                                                     │ │
│  │  ├── descricao: str                                                  │ │
│  │  ├── chunks_count: int                                               │ │
│  │  ├── enriched_count: int                                             │ │
│  │  ├── is_enriched: bool    # Property                                 │ │
│  │  └── enrichment_progress: float                                      │ │
│  │                                                                       │ │
│  │  IngestStatus / EnrichStatus / UploadResponse / DeleteResponse       │ │
│  │  (Status de operações assíncronas)                                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AUDITORIA (v0.10.0)                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  AuditLog                   # Log individual de evento                │ │
│  │  ├── id: str                # UUID do log                             │ │
│  │  ├── event_type: str        # pii_detected, injection_blocked, etc.   │ │
│  │  ├── event_category: str    # security, content, system               │ │
│  │  ├── severity: str          # info, warning, critical                 │ │
│  │  ├── query_text: str        # Query que gerou o evento                │ │
│  │  ├── detection_types: list  # Tipos de detecção (CPF, email, etc.)    │ │
│  │  ├── risk_score: float      # Score de risco (0-1)                    │ │
│  │  ├── action_taken: str      # allowed, blocked, sanitized             │ │
│  │  ├── endpoint: str          # Endpoint chamado                        │ │
│  │  ├── client_ip: str         # IP do cliente                           │ │
│  │  ├── created_at: str        # Timestamp ISO                           │ │
│  │  └── details: dict          # Detalhes adicionais                     │ │
│  │                                                                       │ │
│  │  AuditLogsResponse          # Resposta paginada de logs               │ │
│  │  ├── logs: list[AuditLog]   # Lista de logs                           │ │
│  │  ├── total: int             # Total de logs                           │ │
│  │  ├── page: int              # Página atual                            │ │
│  │  ├── pages: int             # Total de páginas                        │ │
│  │  └── limit: int             # Limite por página                       │ │
│  │                                                                       │ │
│  │  AuditStats                 # Estatísticas agregadas                  │ │
│  │  ├── total_events: int      # Total de eventos no período             │ │
│  │  ├── events_by_type: dict   # Contagem por tipo de evento             │ │
│  │  ├── events_by_severity: dict # Contagem por severidade               │ │
│  │  ├── events_by_category: dict # Contagem por categoria                │ │
│  │  ├── blocked_count: int     # Total de requisições bloqueadas         │ │
│  │  ├── warning_count: int     # Total de avisos                         │ │
│  │  └── period_days: int       # Período em dias                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TOKENS (v0.13.0)                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  TokenStats                  # Estatísticas de tokens                 │ │
│  │  ├── context_tokens: int    # Tokens do contexto (hits formatados)   │ │
│  │  ├── system_tokens: int     # Tokens do system prompt                │ │
│  │  ├── query_tokens: int      # Tokens da query do usuário             │ │
│  │  ├── total_tokens: int      # Total (context + system + query)       │ │
│  │  ├── hits_count: int        # Número de hits incluídos               │ │
│  │  ├── char_count: int        # Número total de caracteres             │ │
│  │  └── encoding: str          # Encoding (cl100k_base para GPT-4/Claude)│ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Dados

### Fluxo de Busca Simples

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE BUSCA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CLIENTE                           SDK                          API        │
│   ───────                          ─────                        ─────       │
│                                                                             │
│   vg.search("O que é ETP?")                                                 │
│           │                                                                 │
│           │ 1. Validação                                                    │
│           ├──────────────────▶ Valida query (3-1000 chars)                  │
│           │                    Valida top_k (1-50)                          │
│           │                    Valida mode (fast/balanced/precise)          │
│           │                                                                 │
│           │ 2. Configuração do Modo                                         │
│           ├──────────────────▶ MODE_CONFIG[mode]                            │
│           │                    use_hyde, use_reranker, use_cache            │
│           │                                                                 │
│           │ 3. Requisição HTTP                                              │
│           ├──────────────────▶ POST /sdk/search ───────────────────────────▶│
│           │                                                                 │
│           │                                     ◀─────── JSON Response ─────│
│           │                                                                 │
│           │ 4. Parse da Resposta                                            │
│           ├──────────────────▶ _parse_search_response()                     │
│           │                    Converte para SearchResult                   │
│           │                    Cria Hits e Metadatas                        │
│           │                                                                 │
│   ◀───────┤ 5. Retorno                                                      │
│           │    SearchResult com hits, total, latency...                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo com Function Calling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO FUNCTION CALLING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. DEFINIÇÃO DA FERRAMENTA                                                │
│   ────────────────────────────                                              │
│   tools = [vg.to_openai_tool()]                                             │
│                  │                                                          │
│                  ▼                                                          │
│   {                                                                         │
│     "type": "function",                                                     │
│     "function": {                                                           │
│       "name": "search_brazilian_legislation",                               │
│       "description": "Busca informações em legislação brasileira...",       │
│       "parameters": {                                                       │
│         "type": "object",                                                   │
│         "properties": {                                                     │
│           "query": {"type": "string"},                                      │
│           "filters": {...},                                                 │
│           "top_k": {"type": "integer", "minimum": 1, "maximum": 50}        │
│         },                                                                  │
│         "required": ["query"]                                               │
│       }                                                                     │
│     }                                                                       │
│   }                                                                         │
│                                                                             │
│   2. CHAMADA AO LLM                                                         │
│   ───────────────────                                                       │
│   response = openai.chat.completions.create(                                │
│       model="gpt-4o",                                                       │
│       messages=[{"role": "user", "content": "O que é ETP?"}],              │
│       tools=tools                                                           │
│   )                                                                         │
│                                                                             │
│   3. EXECUÇÃO DA FERRAMENTA                                                 │
│   ──────────────────────────                                                │
│   if response.choices[0].message.tool_calls:                                │
│       tool_call = response.choices[0].message.tool_calls[0]                 │
│       result = vg.execute_tool_call(tool_call)                              │
│                  │                                                          │
│                  ├──▶ _extract_tool_arguments(tool_call)                    │
│                  │    Extrai arguments do formato OpenAI/Anthropic/Google   │
│                  │                                                          │
│                  ├──▶ parse_tool_arguments(arguments)                       │
│                  │    Retorna (query, filters, top_k)                       │
│                  │                                                          │
│                  ├──▶ self.search(query, top_k, mode, filters)              │
│                  │    Executa busca normal                                  │
│                  │                                                          │
│                  └──▶ format_tool_response(result)                          │
│                       Formata para retornar ao LLM                          │
│                                                                             │
│   4. RESPOSTA FINAL                                                         │
│   ──────────────────                                                        │
│   response = openai.chat.completions.create(                                │
│       messages=[...previous, {"role": "tool", "content": result}]           │
│   )                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Integrações

### Tabela de Integrações

| Integração | Arquivo | Descrição | Instalação Extra |
|------------|---------|-----------|------------------|
| **OpenAI** | `tools.py` | Function calling GPT-4 | `pip install openai` |
| **Anthropic** | `tools.py` | Function calling Claude | `pip install anthropic` |
| **Google Gemini** | `tools.py` | Function calling Gemini | `pip install google-generativeai` |
| **LangChain** | `langchain.py` | Retriever e Tool | `pip install langchain-core` |
| **LangGraph** | `langgraph.py` | Grafos de estado | `pip install langgraph` |
| **Google ADK** | `google_adk.py` | Agent Development Kit | `pip install google-adk` |
| **Ollama** | `ollama.py` | Modelos locais | Ollama instalado |
| **Transformers** | `transformers.py` | HuggingFace | `pip install transformers` |
| **MCP** | `mcp/server.py` | Claude Desktop/Cursor | `pip install mcp` |

### Arquitetura de Integrações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRAÇÕES DO SDK                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LLMs COMERCIAIS (API)                                                      │
│  ─────────────────────                                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                     │
│  │   OpenAI      │ │  Anthropic    │ │   Google      │                     │
│  │   GPT-4       │ │    Claude     │ │   Gemini      │                     │
│  │               │ │               │ │               │                     │
│  │ to_openai_    │ │ to_anthropic_ │ │ to_google_    │                     │
│  │    tool()     │ │    tool()     │ │    tool()     │                     │
│  │               │ │               │ │               │                     │
│  │ execute_      │ │ execute_      │ │ execute_      │                     │
│  │ tool_call()   │ │ tool_call()   │ │ tool_call()   │                     │
│  └───────────────┘ └───────────────┘ └───────────────┘                     │
│                                                                             │
│  FRAMEWORKS DE AGENTES                                                      │
│  ─────────────────────                                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                     │
│  │  LangChain    │ │  LangGraph    │ │  Google ADK   │                     │
│  │               │ │               │ │               │                     │
│  │ VectorGov     │ │ create_       │ │ VectorGov     │                     │
│  │ Retriever     │ │ vectorgov_    │ │ Toolset       │                     │
│  │               │ │    tool()     │ │               │                     │
│  │ VectorGov     │ │               │ │ create_       │                     │
│  │ Tool          │ │ create_legal_ │ │ legal_agent() │                     │
│  │               │ │ rag_graph()   │ │               │                     │
│  └───────────────┘ └───────────────┘ └───────────────┘                     │
│                                                                             │
│  LLMs LOCAIS (GRATUITOS)                                                    │
│  ───────────────────────                                                    │
│  ┌───────────────┐ ┌───────────────┐                                       │
│  │    Ollama     │ │  Transformers │                                       │
│  │               │ │  (HuggingFace)│                                       │
│  │ VectorGov     │ │               │                                       │
│  │ Ollama        │ │ VectorGovRAG  │                                       │
│  │               │ │               │                                       │
│  │ create_rag_   │ │ create_rag_   │                                       │
│  │ pipeline()    │ │ pipeline()    │                                       │
│  └───────────────┘ └───────────────┘                                       │
│                                                                             │
│  INTEGRAÇÃO DIRETA (MCP)                                                    │
│  ───────────────────────                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         MCP SERVER                                    │ │
│  │                                                                       │ │
│  │   Claude Desktop ◀────▶ vectorgov-mcp ◀────▶ VectorGov API           │ │
│  │   Cursor IDE                                                          │ │
│  │                                                                       │ │
│  │   Tools: search_legislation, list_documents, get_article             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Modelos Recomendados (Ollama/Transformers)

| Modelo | RAM/VRAM | Qualidade | Português | Velocidade |
|--------|----------|-----------|-----------|------------|
| `qwen2.5:0.5b` | 1 GB | Básica | Bom | Muito rápido |
| `qwen2.5:3b` | 4-6 GB | Boa | Muito bom | Rápido |
| `qwen2.5:7b` | 8-14 GB | Muito boa | Excelente | Médio |
| `qwen3:8b` | 8-16 GB | Excelente | Excelente | Médio |
| `llama3.2:3b` | 4-6 GB | Boa | Bom | Rápido |
| `mistral:7b` | 8-14 GB | Boa | Bom | Médio |

---

## ❌ Tratamento de Erros

### Hierarquia de Exceções

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HIERARQUIA DE EXCEÇÕES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           VectorGovError (Base)                             │
│                                   │                                         │
│           ┌───────────────────────┼───────────────────────┐                 │
│           │                       │                       │                 │
│           ▼                       ▼                       ▼                 │
│     AuthError              ValidationError          ServerError             │
│     (401)                  (400)                    (500)                   │
│     API key inválida       Parâmetros errados       Erro interno           │
│           │                       │                       │                 │
│           │                       │                       │                 │
│           ▼                       ▼                       ▼                 │
│    RateLimitError         ConnectionError          TimeoutError            │
│    (429)                  Sem conexão              Timeout                  │
│    Excedeu limite         com servidor             na requisição           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tabela de Exceções

| Exceção | Código HTTP | Causa | Solução |
|---------|-------------|-------|---------|
| `AuthError` | 401 | API key inválida ou expirada | Verificar API key |
| `ValidationError` | 400 | Parâmetros inválidos | Verificar query, top_k, mode |
| `RateLimitError` | 429 | Rate limit excedido | Aguardar retry_after segundos |
| `ServerError` | 500 | Erro interno da API | Tentar novamente depois |
| `ConnectionError` | - | Falha de conexão | Verificar internet/URL |
| `TimeoutError` | - | Requisição demorou demais | Aumentar timeout |

### Exemplo de Tratamento

```python
from vectorgov import VectorGov
from vectorgov.exceptions import (
    AuthError,
    RateLimitError,
    ValidationError,
    ServerError,
    ConnectionError,
    TimeoutError,
)

vg = VectorGov(api_key="vg_xxx")

try:
    results = vg.search("O que é ETP?")
except AuthError:
    print("API key inválida")
except RateLimitError as e:
    print(f"Rate limit. Tente em {e.retry_after}s")
except ValidationError as e:
    print(f"Erro no campo {e.field}: {e.message}")
except ServerError:
    print("Erro no servidor. Tente depois.")
except ConnectionError:
    print("Sem conexão com o servidor")
except TimeoutError:
    print("Requisição demorou demais")
```

---

## ⚙️ Configurações

### SearchMode

| Modo | HyDE | Reranker | Cache | Latência | Uso |
|------|------|----------|-------|----------|-----|
| `FAST` | ❌ | ❌ | ✅ | ~2s | Chatbots |
| `BALANCED` | ❌ | ✅ | ✅ | ~5s | Uso geral |
| `PRECISE` | ✅ | ✅ | ✅ | ~15s | Análises críticas |

### System Prompts Pré-definidos

| Estilo | Uso | Características |
|--------|-----|-----------------|
| `default` | Uso geral | Objetivo, cita fontes |
| `concise` | Respostas curtas | Direto ao ponto |
| `detailed` | Análises profundas | Tópicos, exceções, resumo |
| `chatbot` | Assistentes virtuais | Linguagem acessível |

### SDKConfig

```python
@dataclass
class SDKConfig:
    base_url: str = "https://vectorgov.io/api/v1"
    timeout: int = 30
    default_top_k: int = 5
    default_mode: SearchMode = SearchMode.BALANCED
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_local_cache: bool = False  # Futuro
    cache_ttl: int = 300  # Futuro
```

---

## 📝 Exemplos de Uso

### Busca Básica

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")
results = vg.search("O que é ETP?")

print(f"Total: {results.total}")
for hit in results:
    print(f"[{hit.score:.2f}] {hit.source}")
    print(f"  {hit.text[:200]}...")
```

### Com OpenAI

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
openai = OpenAI()

results = vg.search("Critérios de julgamento")
messages = results.to_messages("Quais são os critérios de julgamento?")

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages
)
print(response.choices[0].message.content)
```

### Com LangChain

```python
from vectorgov.integrations.langchain import VectorGovRetriever
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

retriever = VectorGovRetriever(api_key="vg_xxx")
llm = ChatOpenAI(model="gpt-4o-mini")

qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
answer = qa.invoke("Quando o ETP pode ser dispensado?")
print(answer["result"])
```

### Com Ollama (Local)

```python
from vectorgov import VectorGov
from vectorgov.integrations.ollama import VectorGovOllama

vg = VectorGov(api_key="vg_xxx")
rag = VectorGovOllama(vg, model="qwen3:8b")

result = rag.ask("O que é ETP?")
print(result.answer)
print(f"Fontes: {result.sources}")
print(f"Latência: {result.latency_ms}ms")
```

### Com MCP (Claude Desktop)

```json
// claude_desktop_config.json
{
    "mcpServers": {
        "vectorgov": {
            "command": "uvx",
            "args": ["vectorgov-mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_xxx"
            }
        }
    }
}
```

### Estimativa de Tokens (v0.13.0)

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")
results = vg.search("O que é ETP?", top_k=5)

# Estima tokens que seriam usados com OpenAI/Claude
stats = vg.estimate_tokens(results)
print(f"Context: {stats.context_tokens} tokens")
print(f"System: {stats.system_tokens} tokens")
print(f"Query: {stats.query_tokens} tokens")
print(f"Total: {stats.total_tokens} tokens")

# Verificar se cabe na janela de contexto
GPT4_LIMIT = 128_000
if stats.total_tokens < GPT4_LIMIT:
    print("✓ Cabe no GPT-4")
else:
    print(f"✗ Excede limite ({stats.total_tokens} > {GPT4_LIMIT})")

# Estimar custo (preços Jan 2025)
input_cost = (stats.total_tokens / 1_000_000) * 2.50  # GPT-4o input
print(f"Custo estimado (input): ${input_cost:.6f}")
```

### Upload de Documento

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Upload
response = vg.upload_pdf(
    file_path="lei_14133.pdf",
    tipo_documento="LEI",
    numero="14133",
    ano=2021
)
print(f"Task ID: {response.task_id}")

# Monitorar ingestão
import time
while True:
    status = vg.get_ingest_status(response.task_id)
    print(f"Status: {status.status} ({status.progress}%)")
    if status.status in ["completed", "failed"]:
        break
    time.sleep(5)

# Iniciar enriquecimento
vg.start_enrichment(response.document_id)
```

---

## 📊 Métricas e Limites

### Limites da API

| Parâmetro | Mínimo | Máximo | Padrão |
|-----------|--------|--------|--------|
| `query` (caracteres) | 3 | 1000 | - |
| `top_k` | 1 | 50 | 5 |
| `timeout` | - | - | 30s |
| `limit` (listagem) | 1 | 100 | 20 |

### Latências Esperadas

| Modo | Sem Cache | Com Cache |
|------|-----------|-----------|
| FAST | ~2s | ~0.1s |
| BALANCED | ~5s | ~0.1s |
| PRECISE | ~15s | ~0.1s |

---

## 🔗 Links Úteis

- **PyPI**: https://pypi.org/project/vectorgov/
- **GitHub**: https://github.com/euteajudo/vectorgov-sdk
- **Documentação API**: https://vectorgov.io/docs
- **Portal**: https://vectorgov.io

### Documentação para LLMs

O VectorGov disponibiliza documentação estruturada para assistentes de IA:

| Recurso | URL | Descrição |
|---------|-----|-----------|
| **llms.txt** | https://vectorgov.io/llms.txt | Documentação completa do SDK em formato texto para LLMs (padrão [llmstxt.org](https://llmstxt.org/)) |
| **CLAUDE.md** | https://vectorgov.io/CLAUDE.md | Instruções específicas para Claude Code com exemplos de integração |
| **robots.txt** | https://vectorgov.io/robots.txt | Permite acesso de crawlers de IA (GPTBot, Claude-Web, etc.) |

Esses arquivos permitem que assistentes de IA aprendam automaticamente a usar o SDK VectorGov.

---

*Documentação atualizada em Janeiro de 2025*
