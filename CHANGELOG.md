# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

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

[Unreleased]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/euteajudo/vectorgov-sdk/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/euteajudo/vectorgov-sdk/releases/tag/v0.1.0
