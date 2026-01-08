# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

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

[Unreleased]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/euteajudo/vectorgov-sdk/releases/tag/v0.1.0
