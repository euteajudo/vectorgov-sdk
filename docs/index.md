# VectorGov SDK

Bem-vindo à documentação do VectorGov SDK!

## O que é o VectorGov?

VectorGov é uma plataforma de busca semântica para documentos jurídicos brasileiros. Com nosso SDK, você pode:

- **Buscar** informações em leis, decretos e instruções normativas
- **Integrar** facilmente com qualquer LLM (OpenAI, Gemini, Claude, etc.)
- **Construir** assistentes jurídicos inteligentes em minutos

## Instalação

```bash
pip install vectorgov
```

## Início Rápido

```python
from vectorgov import VectorGov

# Conectar
vg = VectorGov(api_key="vg_sua_chave")

# Buscar
results = vg.search("O que é ETP?")

# Usar
print(results.to_context())
```

## Integração com LLMs

=== "OpenAI"

    ```python
    from vectorgov import VectorGov
    from openai import OpenAI

    vg = VectorGov(api_key="vg_xxx")
    openai = OpenAI()

    results = vg.search("Critérios de julgamento")

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=results.to_messages("Critérios de julgamento")
    )
    ```

=== "Gemini"

    ```python
    from vectorgov import VectorGov
    import google.generativeai as genai

    vg = VectorGov(api_key="vg_xxx")
    genai.configure(api_key="...")

    results = vg.search("Critérios de julgamento")
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(
        results.to_prompt("Critérios de julgamento")
    )
    ```

=== "Claude"

    ```python
    from vectorgov import VectorGov
    from anthropic import Anthropic

    vg = VectorGov(api_key="vg_xxx")
    client = Anthropic()

    results = vg.search("Critérios de julgamento")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=results.to_messages("Critérios de julgamento")
    )
    ```

## Metodos de Busca

| Metodo | Latencia | Melhor para |
|--------|----------|-------------|
| `search()` | 2-7s | Buscas semanticas simples |
| `smart_search()` | 5-18s | Analise juridica completa (Premium) |
| `hybrid()` | 3-10s | Normas relacionadas, cadeia regulatoria |
| `lookup()` | < 1s | Referencia exata ("Art. 75 da Lei X") |
| `grep()` | < 1s | Busca textual exata, palavras-chave |
| `filesystem_search()` | < 1s | Indice curado, referencias legais |
| `merged()` | 2-5s | Busca dual-path (semantica + filesystem) |
| `read_canonical()` | < 1s | Texto canonico completo |

```python
# Busca semantica
results = vg.search("O que e ETP?", mode="precise")

# Busca textual exata
matches = vg.grep("dispensa de licitacao")

# Busca dual-path (maxima cobertura)
results = vg.merged("prazo para impugnacao do edital")

# Texto canonico completo
doc = vg.read_canonical("LEI-14133-2021", span_id="ART-075")
```

## System Prompts

Controle como o LLM responde suas perguntas:

```python
# Usar prompt pré-definido
messages = results.to_messages(
    query="O que é ETP?",
    system_prompt=vg.get_system_prompt("detailed")
)

# Ou criar seu próprio
messages = results.to_messages(
    query="O que é ETP?",
    system_prompt="Seu prompt personalizado aqui..."
)

# Ver prompts disponíveis
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']
```

📖 **[Guia Completo de System Prompts](guides/system-prompts.md)** - Conteúdo dos prompts, estimativa de tokens e impacto no custo.

## Observabilidade e Auditoria

Monitore o uso da API, detecte problemas de segurança e atenda requisitos de compliance:

```python
# Estatísticas dos últimos 30 dias
stats = vg.get_audit_stats(days=30)
print(f"Total eventos: {stats.total_events}")
print(f"Bloqueados: {stats.blocked_count}")

# Listar logs de segurança
logs = vg.get_audit_logs(severity="warning", limit=50)
for log in logs.logs:
    print(f"{log.event_type}: {log.action_taken}")
```

📖 **[Guia Completo de Observabilidade e Auditoria](guides/observability-audit.md)** - Métodos, tipos de eventos, exemplos de monitoramento e compliance.

## Próximos Passos

- [System Prompts](guides/system-prompts.md) - Controle tokens e custos
- [Observabilidade e Auditoria](guides/observability-audit.md) - Monitoramento e compliance
- [Modos de Busca](guides/search-modes.md) - Detalhes dos modos
- [Integração com LLMs](guides/llm-integration.md) - Exemplos avançados

## Suporte

- [GitHub Issues](https://github.com/vectorgov/vectorgov-sdk/issues)
- Email: suporte@vectorgov.io
