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

## Modos de Busca

| Modo | Latência | Uso |
|------|----------|-----|
| `fast` | ~2s | Chatbots |
| `balanced` | ~5s | Uso geral |
| `precise` | ~15s | Análises |

```python
results = vg.search("query", mode="precise")
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

## Próximos Passos

- [System Prompts](guides/system-prompts.md) - Controle tokens e custos
- [Modos de Busca](guides/search-modes.md) - Detalhes dos modos
- [Integração com LLMs](guides/llm-integration.md) - Exemplos avançados

## Suporte

- [GitHub Issues](https://github.com/vectorgov/vectorgov-sdk/issues)
- Email: suporte@vectorgov.io
