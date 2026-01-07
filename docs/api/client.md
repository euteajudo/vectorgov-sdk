# Cliente VectorGov

A classe principal para interagir com a API VectorGov.

## Inicialização

```python
from vectorgov import VectorGov

# Básico
vg = VectorGov(api_key="vg_xxx")

# Com configurações
vg = VectorGov(
    api_key="vg_xxx",
    base_url="https://vectorgov.io/api/v1",
    timeout=30,
    default_top_k=5,
    default_mode="balanced",
)
```

### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `api_key` | `str` | `None` | Chave de API. Usa `VECTORGOV_API_KEY` se não informada |
| `base_url` | `str` | `"https://vectorgov.io/api/v1"` | URL base da API |
| `timeout` | `int` | `30` | Timeout em segundos |
| `default_top_k` | `int` | `5` | Quantidade padrão de resultados |
| `default_mode` | `str` | `"balanced"` | Modo de busca padrão |

## Métodos

### search()

Busca informações na base de conhecimento.

```python
results = vg.search(
    query="O que é ETP?",
    top_k=5,
    mode="balanced",
    filters={"tipo": "lei", "ano": 2021},
)
```

#### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | - | Texto da consulta (obrigatório) |
| `top_k` | `int` | `5` | Quantidade de resultados (1-20) |
| `mode` | `str` | `"balanced"` | Modo: `fast`, `balanced`, `precise` |
| `filters` | `dict` | `None` | Filtros opcionais |

#### Filtros Disponíveis

| Filtro | Tipo | Exemplo | Descrição |
|--------|------|---------|-----------|
| `tipo` | `str` | `"lei"` | Tipo do documento |
| `ano` | `int` | `2021` | Ano do documento |
| `orgao` | `str` | `"seges"` | Órgão emissor |

#### Retorno

Retorna um objeto `SearchResult`.

### feedback()

Envia feedback sobre um resultado de busca.

```python
vg.feedback(results.query_id, like=True)
```

#### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `query_id` | `str` | ID da query (de `results.query_id`) |
| `like` | `bool` | `True` para positivo, `False` para negativo |

#### Retorno

`True` se o feedback foi registrado com sucesso.

### get_system_prompt()

Retorna um system prompt pré-definido.

```python
prompt = vg.get_system_prompt("detailed")
```

#### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `style` | `str` | `"default"` | Estilo do prompt |

#### Estilos Disponíveis

| Estilo | Descrição |
|--------|-----------|
| `default` | Balanceado, formal, cita fontes |
| `concise` | Respostas curtas e diretas |
| `detailed` | Análise profunda, estruturada |
| `chatbot` | Tom amigável, acessível |

### available_prompts

Propriedade que lista os estilos de prompt disponíveis.

```python
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']
```

## Exemplo Completo

```python
from vectorgov import VectorGov

# Inicializar
vg = VectorGov(api_key="vg_xxx")

# Buscar
results = vg.search(
    "Quando o ETP pode ser dispensado?",
    mode="precise",
    top_k=5,
    filters={"tipo": "in"},
)

# Usar resultados
print(f"Total: {results.total}")
print(f"Latência: {results.latency_ms}ms")

for hit in results:
    print(f"- {hit.source}: {hit.text[:100]}...")

# Feedback
vg.feedback(results.query_id, like=True)
```
