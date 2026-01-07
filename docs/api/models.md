# Modelos

Classes de dados retornadas pela API.

## SearchResult

Resultado completo de uma busca.

### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `query` | `str` | Query original |
| `hits` | `list[Hit]` | Lista de resultados |
| `total` | `int` | Quantidade total |
| `latency_ms` | `int` | Tempo de resposta (ms) |
| `cached` | `bool` | Se veio do cache |
| `query_id` | `str` | ID para feedback |
| `mode` | `str` | Modo utilizado |
| `timestamp` | `datetime` | Timestamp da busca |

### Métodos

#### to_context()

Converte os resultados em uma string de contexto.

```python
context = results.to_context(max_chars=4000)
```

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `max_chars` | `int` | `None` | Limite de caracteres |

**Retorno:**

```
[1] Lei 14.133/2021, Art. 33
Os critérios de julgamento serão...

[2] Lei 14.133/2021, Art. 36
O julgamento por técnica e preço...
```

#### to_messages()

Converte para formato de mensagens (OpenAI/Claude).

```python
messages = results.to_messages(
    query="Critérios de julgamento",
    system_prompt="Você é um assistente jurídico...",
    max_context_chars=4000,
)
```

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | `self.query` | Pergunta |
| `system_prompt` | `str` | Prompt padrão | System prompt |
| `max_context_chars` | `int` | `None` | Limite de contexto |

**Retorno:**

```python
[
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Contexto:\n...\n\nPergunta: ..."}
]
```

#### to_prompt()

Converte para um prompt único (Gemini).

```python
prompt = results.to_prompt(
    query="Critérios de julgamento",
    system_prompt="...",
)
```

**Parâmetros:** Mesmos de `to_messages()`.

**Retorno:** String única com system prompt, contexto e pergunta.

#### to_dict()

Converte para dicionário.

```python
data = results.to_dict()
```

### Iteração

`SearchResult` suporta iteração e indexação:

```python
# Iterar
for hit in results:
    print(hit.source)

# Indexar
first = results[0]

# Quantidade
print(len(results))
```

---

## Hit

Um resultado individual da busca.

### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `text` | `str` | Texto do chunk |
| `score` | `float` | Relevância (0-1) |
| `source` | `str` | Fonte formatada |
| `metadata` | `Metadata` | Metadados completos |
| `chunk_id` | `str` | ID interno (debug) |
| `context` | `str` | Contexto adicional |

### Exemplo

```python
for hit in results:
    print(f"Fonte: {hit.source}")
    print(f"Score: {hit.score:.2%}")
    print(f"Texto: {hit.text[:200]}...")
    print(f"Tipo: {hit.metadata.document_type}")
```

---

## Metadata

Metadados de um documento.

### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `document_type` | `str` | Tipo (lei, decreto, in) |
| `document_number` | `str` | Número do documento |
| `year` | `int` | Ano |
| `article` | `str` | Número do artigo |
| `paragraph` | `str` | Número do parágrafo |
| `item` | `str` | Número do inciso |
| `orgao` | `str` | Órgão emissor |
| `extra` | `dict` | Metadados adicionais |

### Exemplo

```python
meta = hit.metadata

print(f"Documento: {meta.document_type} {meta.document_number}/{meta.year}")
print(f"Artigo: {meta.article}")
print(f"Órgão: {meta.orgao}")
```

---

## SearchMode

Enum com os modos de busca disponíveis.

```python
from vectorgov import SearchMode

# Usar enum
results = vg.search("query", mode=SearchMode.PRECISE)

# Ou string
results = vg.search("query", mode="precise")
```

### Valores

| Valor | Descrição |
|-------|-----------|
| `SearchMode.FAST` | Mais rápido (~2s) |
| `SearchMode.BALANCED` | Balanceado (~5s) |
| `SearchMode.PRECISE` | Mais preciso (~15s) |
