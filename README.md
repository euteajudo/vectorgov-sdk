# VectorGov SDK

SDK Python para acessar bases de conhecimento jurídico VectorGov.

Acesse informações de leis, decretos e instruções normativas brasileiras com 3 linhas de código.

[![PyPI version](https://badge.fury.io/py/vectorgov.svg)](https://badge.fury.io/py/vectorgov)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Instalação

```bash
pip install vectorgov
```

## Início Rápido

```python
from vectorgov import VectorGov

# Conectar à API
vg = VectorGov(api_key="vg_sua_chave_aqui")

# Buscar informações
results = vg.search("Quando o ETP pode ser dispensado?")

# Ver resultados
for hit in results:
    print(f"{hit.source}: {hit.text[:200]}...")
```

## Integração com LLMs

### OpenAI

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
openai = OpenAI()

# Buscar contexto
query = "Quais os critérios de julgamento na licitação?"
results = vg.search(query)

# Gerar resposta
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=results.to_messages(query)
)

print(response.choices[0].message.content)
```

### Google Gemini

```python
from vectorgov import VectorGov
import google.generativeai as genai

vg = VectorGov(api_key="vg_xxx")
genai.configure(api_key="sua_google_key")

query = "O que é ETP?"
results = vg.search(query)

# Monta o prompt
messages = results.to_messages(query)
system_prompt = messages[0]["content"]
user_prompt = messages[1]["content"]

# Cria o modelo com system instruction
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_prompt
)

response = model.generate_content(user_prompt)
print(response.text)
```

### Anthropic Claude

```python
from vectorgov import VectorGov
from anthropic import Anthropic

vg = VectorGov(api_key="vg_xxx")
client = Anthropic()

query = "Quais documentos compõem o ETP?"
results = vg.search(query)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=results.to_messages(query)
)

print(response.content[0].text)
```

## Modos de Busca

| Modo | Descrição | Latência | Uso Recomendado |
|------|-----------|----------|-----------------|
| `fast` | Busca rápida, sem reranking | ~2s | Chatbots, alta escala |
| `balanced` | Busca com reranking | ~5s | **Uso geral (default)** |
| `precise` | Busca com HyDE + reranking | ~15s | Análises críticas |

```python
# Busca rápida (chatbots)
results = vg.search("query", mode="fast")

# Busca balanceada (default)
results = vg.search("query", mode="balanced")

# Busca precisa (análises)
results = vg.search("query", mode="precise")
```

## Filtros

```python
# Filtrar por tipo de documento
results = vg.search("licitação", filters={"tipo": "lei"})

# Filtrar por ano
results = vg.search("pregão", filters={"ano": 2021})

# Múltiplos filtros
results = vg.search("contratação direta", filters={
    "tipo": "in",
    "ano": 2022,
    "orgao": "seges"
})
```

## Formatação de Resultados

```python
results = vg.search("O que é ETP?")

# String simples para contexto
context = results.to_context()
print(context)
# [1] Lei 14.133/2021, Art. 3
# O Estudo Técnico Preliminar - ETP é documento...
#
# [2] IN 58/2022, Art. 6
# O ETP deve conter...

# Mensagens para chat (OpenAI, Anthropic)
messages = results.to_messages("O que é ETP?")
# [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

# Prompt único (Gemini)
prompt = results.to_prompt("O que é ETP?")
```

## System Prompts Customizados

```python
# Usar prompt pré-definido
results = vg.search("query")
messages = results.to_messages(
    system_prompt=vg.get_system_prompt("detailed")
)

# Prompts disponíveis
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']

# Prompt totalmente customizado
custom_prompt = """Você é um advogado especialista em licitações.
Responda de forma técnica e cite artigos específicos."""

messages = results.to_messages(system_prompt=custom_prompt)
```

## Feedback

Ajude a melhorar o sistema enviando feedback:

```python
results = vg.search("O que é ETP?")

# Após verificar que o resultado foi útil
vg.feedback(results.query_id, like=True)

# Se o resultado não foi útil
vg.feedback(results.query_id, like=False)
```

## Propriedades do Resultado

```python
results = vg.search("query")

# Informações gerais
results.query        # Query original
results.total        # Quantidade de resultados
results.latency_ms   # Tempo de resposta (ms)
results.cached       # Se veio do cache
results.query_id     # ID para feedback
results.mode         # Modo utilizado

# Iterar resultados
for hit in results:
    hit.text         # Texto do chunk
    hit.score        # Relevância (0-1)
    hit.source       # Fonte formatada
    hit.metadata     # Metadados completos
```

## Tratamento de Erros

```python
from vectorgov import (
    VectorGov,
    VectorGovError,
    AuthError,
    RateLimitError,
    ValidationError,
)

try:
    results = vg.search("query")
except AuthError:
    print("API key inválida ou expirada")
except RateLimitError as e:
    print(f"Rate limit. Tente em {e.retry_after}s")
except ValidationError as e:
    print(f"Erro no campo {e.field}: {e.message}")
except VectorGovError as e:
    print(f"Erro: {e.message}")
```

## Variáveis de Ambiente

```bash
# API key pode ser definida via ambiente
export VECTORGOV_API_KEY=vg_sua_chave_aqui
```

```python
# Usa automaticamente a variável de ambiente
vg = VectorGov()
```

## Configuração Avançada

```python
vg = VectorGov(
    api_key="vg_xxx",
    base_url="https://vectorgov.io/api/v1",  # URL customizada
    timeout=60,                               # Timeout em segundos
    default_top_k=10,                         # Resultados padrão
    default_mode="precise",                   # Modo padrão
)
```

## Obter sua API Key

1. Acesse [vectorgov.io/playground](https://vectorgov.io/playground)
2. Crie uma conta ou faça login
3. Gere sua API key na seção "Configurações"

## Documentação

- [Documentação Completa](https://docs.vectorgov.io)
- [Exemplos](https://github.com/vectorgov/vectorgov-python/tree/main/examples)
- [Referência da API](https://docs.vectorgov.io/api-reference)

## Suporte

- [GitHub Issues](https://github.com/vectorgov/vectorgov-python/issues)
- Email: suporte@vectorgov.io

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
