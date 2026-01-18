# VectorGov SDK - Referência Completa para Desenvolvedores e LLMs

> **Versão:** 0.6.0 | **Python:** 3.9+ | **Licença:** MIT

Esta documentação é uma referência completa e autocontida do VectorGov SDK, projetada para ser compartilhada com LLMs (ChatGPT, Claude, Gemini, etc.) para auxiliar no desenvolvimento de aplicações que utilizam busca semântica em legislação brasileira.

---

## Índice

- [Visão Geral](#visão-geral)
- [Instalação](#instalação)
- [Início Rápido](#início-rápido)
- [Cliente Principal (VectorGov)](#cliente-principal-vectorgov)
- [Modelos de Dados](#modelos-de-dados)
- [Modos de Busca](#modos-de-busca)
- [Integração com LLMs](#integração-com-llms)
  - [OpenAI GPT](#openai-gpt)
  - [Google Gemini](#google-gemini)
  - [Anthropic Claude](#anthropic-claude)
- [Modelos Locais (Open-Source)](#modelos-locais-open-source)
  - [Ollama](#ollama)
  - [HuggingFace Transformers](#huggingface-transformers)
- [Function Calling (Agentes)](#function-calling-agentes)
- [Frameworks de Agentes](#frameworks-de-agentes)
  - [LangChain](#langchain)
  - [LangGraph](#langgraph)
  - [Google ADK](#google-adk)
- [Servidor MCP](#servidor-mcp)
- [Tratamento de Erros](#tratamento-de-erros)
- [System Prompts](#system-prompts)
- [Referência Completa da API](#referência-completa-da-api)

---

## Visão Geral

O VectorGov SDK é uma biblioteca Python para acessar bases de conhecimento jurídico brasileiras via busca semântica. Permite integrar facilmente informações de leis, decretos e instruções normativas em aplicações de IA.

### Principais Funcionalidades

| Funcionalidade | Descrição |
|---------------|-----------|
| **Busca Semântica** | Encontra informações relevantes por significado, não apenas palavras-chave |
| **Múltiplos Modos** | `fast` (2s), `balanced` (5s), `precise` (15s) |
| **Integração com LLMs** | Formatação pronta para OpenAI, Gemini, Claude |
| **Function Calling** | Suporte nativo a ferramentas de agentes |
| **Modelos Locais** | Integração com Ollama e Transformers |
| **MCP Server** | Compatível com Claude Desktop, Cursor, Windsurf |

### Documentos Disponíveis na Base

| Documento | Tipo | Ano | Descrição |
|-----------|------|-----|-----------|
| Lei 14.133 | LEI | 2021 | Nova Lei de Licitações e Contratos |
| IN SEGES 58 | IN | 2022 | Estudo Técnico Preliminar (ETP) |
| IN SEGES 65 | IN | 2021 | Pesquisa de Preços |
| IN SEGES 81 | IN | 2022 | Termo de Referência |

---

## Instalação

### Instalação Básica

```bash
pip install vectorgov
```

### Instalação com Extras

| Extra | Comando | Descrição |
|-------|---------|-----------|
| LangChain | `pip install 'vectorgov[langchain]'` | Retriever e Tool para LangChain |
| LangGraph | `pip install 'vectorgov[langgraph]'` | Ferramenta para agentes ReAct |
| Google ADK | `pip install 'vectorgov[google-adk]'` | Toolset para Google Agent Dev Kit |
| Transformers | `pip install 'vectorgov[transformers]'` | RAG com modelos HuggingFace locais |
| MCP Server | `pip install 'vectorgov[mcp]'` | Servidor MCP para Claude Desktop |
| Tudo | `pip install 'vectorgov[all]'` | Todas as dependências acima |

### Dependências de LLMs (separadas)

```bash
pip install openai              # Para OpenAI GPT
pip install google-generativeai # Para Google Gemini
pip install anthropic           # Para Anthropic Claude
```

> **Nota:** A integração com Ollama não requer dependências extras - usa apenas a biblioteca padrão do Python.

---

## Início Rápido

```python
from vectorgov import VectorGov

# Inicializar (API key via parâmetro ou variável VECTORGOV_API_KEY)
vg = VectorGov(api_key="vg_sua_chave_aqui")

# Buscar informações
results = vg.search("O que é o Estudo Técnico Preliminar (ETP)?")

# Exibir resultados
print(f"Total: {results.total}")
print(f"Latência: {results.latency_ms}ms")

for hit in results:
    print(f"[{hit.score:.0%}] {hit.source}")
    print(hit.text[:200])
```

### Saída Esperada

```
Total: 5
Latência: 1234ms
[95%] IN 58/2022, Art. 1
O Estudo Técnico Preliminar - ETP é documento constitutivo da primeira etapa...
```

---

## Cliente Principal (VectorGov)

### Construtor

```python
from vectorgov import VectorGov

vg = VectorGov(
    api_key="vg_xxx",                          # Obrigatório (ou VECTORGOV_API_KEY)
    base_url="https://vectorgov.io/api/v1",    # URL da API (padrão)
    timeout=30,                                 # Timeout em segundos
    default_top_k=5,                           # Resultados padrão (1-20)
    default_mode="balanced",                   # Modo padrão
)
```

#### Parâmetros do Construtor

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `api_key` | `str` | `None` | Chave de API (formato: `vg_*`). Usa `VECTORGOV_API_KEY` se não informada |
| `base_url` | `str` | `"https://vectorgov.io/api/v1"` | URL base da API |
| `timeout` | `int` | `30` | Timeout para requisições em segundos |
| `default_top_k` | `int` | `5` | Quantidade padrão de resultados (1-20) |
| `default_mode` | `str\|SearchMode` | `"balanced"` | Modo de busca padrão |

### Método search()

```python
results = vg.search(
    query="Quando o ETP pode ser dispensado?",
    top_k=5,                    # Quantidade de resultados (1-20)
    mode="balanced",            # fast, balanced, precise
    filters={                   # Filtros opcionais
        "tipo": "in",           # lei, decreto, in, portaria
        "ano": 2022,            # Ano do documento
        "orgao": "seges",       # Órgão emissor
    },
)
```

#### Parâmetros do search()

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | - | Texto da consulta (3-1000 caracteres) **Obrigatório** |
| `top_k` | `int` | `5` | Quantidade de resultados (1-20) |
| `mode` | `str\|SearchMode` | `"balanced"` | Modo de busca |
| `filters` | `dict` | `None` | Filtros opcionais |

#### Filtros Disponíveis

| Filtro | Tipo | Valores | Exemplo |
|--------|------|---------|---------|
| `tipo` | `str` | `lei`, `decreto`, `in`, `portaria`, `resolucao` | `{"tipo": "lei"}` |
| `ano` | `int` | Ano do documento | `{"ano": 2021}` |
| `orgao` | `str` | Órgão emissor | `{"orgao": "seges"}` |

### Método feedback()

```python
# Após verificar que o resultado foi útil
vg.feedback(results.query_id, like=True)

# Se o resultado não foi útil
vg.feedback(results.query_id, like=False)
```

### Método get_system_prompt()

```python
prompt = vg.get_system_prompt("detailed")
# Estilos disponíveis: 'default', 'concise', 'detailed', 'chatbot'
```

### Propriedade available_prompts

```python
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']
```

---

## Modelos de Dados

### SearchResult

Resultado completo de uma busca.

```python
results = vg.search("query")

# Propriedades
results.query        # str: Query original
results.hits         # list[Hit]: Lista de resultados
results.total        # int: Quantidade total
results.latency_ms   # int: Tempo de resposta (ms)
results.cached       # bool: Se veio do cache
results.query_id     # str: ID para feedback
results.mode         # str: Modo utilizado
results.timestamp    # datetime: Timestamp da busca

# Iteração
for hit in results:
    print(hit.source)

# Indexação
first_hit = results[0]
count = len(results)
```

#### Métodos do SearchResult

##### to_context()

Converte resultados em string formatada para contexto.

```python
context = results.to_context(max_chars=4000)
print(context)
# [1] Lei 14.133/2021, Art. 33
# Os critérios de julgamento serão...
#
# [2] Lei 14.133/2021, Art. 36
# O julgamento por técnica e preço...
```

##### to_messages()

Converte para formato de mensagens (OpenAI/Anthropic).

```python
messages = results.to_messages(
    query="Critérios de julgamento",      # Opcional (usa results.query)
    system_prompt="Você é um advogado...", # Opcional
    max_context_chars=4000,                # Limite de contexto
)
# Retorna:
# [
#     {"role": "system", "content": "..."},
#     {"role": "user", "content": "Contexto:\n...\n\nPergunta: ..."}
# ]
```

##### to_prompt()

Converte para prompt único (Gemini e similares).

```python
prompt = results.to_prompt(
    query="O que é ETP?",
    system_prompt="...",
    max_context_chars=4000,
)
# Retorna string única com system prompt, contexto e pergunta
```

##### to_dict()

Converte para dicionário serializável.

```python
data = results.to_dict()
# {"query": "...", "hits": [...], "total": 5, ...}
```

### Hit

Um resultado individual da busca.

```python
for hit in results:
    hit.text         # str: Texto do chunk
    hit.score        # float: Relevância (0-1)
    hit.source       # str: Fonte formatada ("Lei 14.133/2021, Art. 33")
    hit.metadata     # Metadata: Metadados completos
    hit.chunk_id     # str: ID interno (debug)
    hit.context      # str: Contexto adicional
```

### Metadata

Metadados de um documento.

```python
meta = hit.metadata

meta.document_type   # str: Tipo (lei, decreto, in)
meta.document_number # str: Número do documento
meta.year            # int: Ano
meta.article         # str: Número do artigo
meta.paragraph       # str: Número do parágrafo
meta.item            # str: Número do inciso
meta.orgao           # str: Órgão emissor
meta.extra           # dict: Metadados adicionais
```

---

## Modos de Busca

| Modo | Latência | HyDE | Reranker | Uso Recomendado |
|------|----------|------|----------|-----------------|
| `fast` | ~2s | ❌ | ❌ | Chatbots, alta escala |
| `balanced` | ~5s | ❌ | ✅ | **Uso geral (default)** |
| `precise` | ~15s | ✅ | ✅ | Análises críticas |

```python
from vectorgov import SearchMode

# Usando string
results = vg.search("query", mode="fast")

# Usando enum
results = vg.search("query", mode=SearchMode.PRECISE)
```

### SearchMode Enum

```python
from vectorgov import SearchMode

SearchMode.FAST      # "fast"
SearchMode.BALANCED  # "balanced"
SearchMode.PRECISE   # "precise"
```

---

## Integração com LLMs

### OpenAI GPT

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
openai_client = OpenAI(api_key="sk-xxx")

# Buscar contexto
query = "Quais os critérios de julgamento na licitação?"
results = vg.search(query)

# Gerar resposta
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
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
client = Anthropic(api_key="sk-ant-xxx")

query = "O que é ETP?"
results = vg.search(query)
messages = results.to_messages(query)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=messages[0]["content"],  # System prompt separado
    messages=[{"role": "user", "content": messages[1]["content"]}]
)

print(response.content[0].text)
```

---

## Modelos Locais (Open-Source)

### Ollama

**Recomendado** - Forma mais simples de rodar LLMs localmente. Não requer dependências extras.

#### Instalação do Ollama

```bash
# 1. Instale o Ollama: https://ollama.ai/
# 2. Baixe um modelo
ollama pull qwen3:8b
```

#### Pipeline RAG Simples

```python
from vectorgov import VectorGov
from vectorgov.integrations.ollama import create_rag_pipeline

vg = VectorGov(api_key="vg_xxx")

# Cria pipeline RAG com Ollama
rag = create_rag_pipeline(vg, model="qwen3:8b")

# Usa como função
resposta = rag("Quais os critérios de julgamento na licitação?")
print(resposta)
```

#### Classe VectorGovOllama

```python
from vectorgov import VectorGov
from vectorgov.integrations.ollama import VectorGovOllama, OllamaResponse

vg = VectorGov(api_key="vg_xxx")
rag = VectorGovOllama(
    vg,
    model="qwen3:8b",
    top_k=5,
    temperature=0.1,
    max_tokens=512,
)

response: OllamaResponse = rag.ask("O que é ETP?")

print(response.answer)       # Resposta gerada
print(response.sources)      # Lista de fontes
print(response.latency_ms)   # Latência total
print(response.model)        # Modelo usado
print(response.cached)       # Se busca veio do cache
```

#### Chat com Histórico

```python
messages = [{"role": "user", "content": "O que é ETP?"}]

response = rag.chat(messages, use_rag=True)
print(response)

# Continua a conversa
messages.append({"role": "assistant", "content": response})
messages.append({"role": "user", "content": "E quando pode ser dispensado?"})

response2 = rag.chat(messages, use_rag=True)
```

#### Funções Auxiliares do Ollama

```python
from vectorgov.integrations.ollama import (
    check_ollama_available,  # Verifica se Ollama está rodando
    list_models,             # Lista modelos instalados
    get_recommended_models,  # Lista modelos recomendados
    generate,                # Geração de baixo nível
)

# Verificar disponibilidade
if check_ollama_available():
    models = list_models()
    print(f"Modelos: {models}")

# Modelos recomendados
for name, info in get_recommended_models().items():
    print(f"{name}: {info['description']} (RAM: {info['ram_gb']}GB)")
```

#### Modelos Recomendados (Ollama)

| Modelo | RAM | Qualidade | Português | Comando |
|--------|-----|-----------|-----------|---------|
| `qwen2.5:0.5b` | 1GB | Básica | Bom | `ollama pull qwen2.5:0.5b` |
| `qwen2.5:3b` | 4GB | Boa | Muito Bom | `ollama pull qwen2.5:3b` |
| `qwen2.5:7b` | 8GB | Muito Boa | **Excelente** | `ollama pull qwen2.5:7b` |
| `qwen3:8b` | 8GB | **Excelente** | **Excelente** | `ollama pull qwen3:8b` |
| `llama3.2:3b` | 4GB | Boa | Bom | `ollama pull llama3.2:3b` |
| `mistral:7b` | 8GB | Boa | Bom | `ollama pull mistral:7b` |

### HuggingFace Transformers

```bash
pip install 'vectorgov[transformers]'
# ou
pip install vectorgov transformers torch accelerate
```

#### Pipeline RAG Simples

```python
from vectorgov import VectorGov
from vectorgov.integrations.transformers import create_rag_pipeline
from transformers import pipeline

vg = VectorGov(api_key="vg_xxx")
llm = pipeline("text-generation", model="Qwen/Qwen2.5-3B-Instruct", device_map="auto")

rag = create_rag_pipeline(vg, llm, top_k=5, max_new_tokens=512)

resposta = rag("Quais os critérios de julgamento na licitação?")
print(resposta)
```

#### Classe VectorGovRAG

```python
from vectorgov import VectorGov
from vectorgov.integrations.transformers import VectorGovRAG, RAGResponse
from transformers import pipeline

vg = VectorGov(api_key="vg_xxx")
llm = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct", device_map="auto")

rag = VectorGovRAG(vg, llm, top_k=5, temperature=0.1)

response: RAGResponse = rag.ask("O que é ETP?")

print(response.answer)       # Resposta
print(response.sources)      # Fontes
print(response.latency_ms)   # Latência de busca
print(response.cached)       # Se veio do cache
```

#### Rodando sem GPU (CPU)

```python
from transformers import pipeline
import torch

llm = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B-Instruct",
    device="cpu",
    torch_dtype=torch.float32,
)
```

#### Modelo Quantizado (4-bit)

```python
from transformers import pipeline, BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
)

llm = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-7B-Instruct",
    model_kwargs={"quantization_config": quantization_config},
    device_map="auto",
)
```

#### Modelos Recomendados (HuggingFace)

| Modelo | VRAM | Qualidade | Português |
|--------|------|-----------|-----------|
| `meta-llama/Llama-3.2-1B-Instruct` | 2GB | Básica | Bom |
| `Qwen/Qwen2.5-3B-Instruct` | 6GB | Boa | **Excelente** |
| `meta-llama/Llama-3.2-3B-Instruct` | 6GB | Boa | Bom |
| `Qwen/Qwen2.5-7B-Instruct` | 14GB | Muito Boa | **Excelente** |
| `microsoft/Phi-3-mini-4k-instruct` | 4GB | Boa | Razoável |

---

## Function Calling (Agentes)

O VectorGov pode ser usado como ferramenta em agentes de IA. O LLM decide automaticamente quando consultar a legislação.

### OpenAI Function Calling

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
client = OpenAI()

# Primeira chamada - GPT decide se precisa consultar legislação
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Quais os critérios de julgamento?"}],
    tools=[vg.to_openai_tool()],  # Registra VectorGov como ferramenta
    tool_choice="auto",
)

# Se GPT quiser usar a ferramenta
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    result = vg.execute_tool_call(tool_call)  # Executa busca

    # Segunda chamada com o resultado
    final = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Quais os critérios de julgamento?"},
            response.choices[0].message,
            {"role": "tool", "tool_call_id": tool_call.id, "content": result},
        ],
    )
    print(final.choices[0].message.content)
```

### Anthropic Claude Tools

```python
from vectorgov import VectorGov
from anthropic import Anthropic

vg = VectorGov(api_key="vg_xxx")
client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "O que é ETP?"}],
    tools=[vg.to_anthropic_tool()],
)

# Processar tool_use se houver
for block in response.content:
    if block.type == "tool_use":
        result = vg.execute_tool_call(block)
        # Continuar conversa com resultado...
```

### Google Gemini Function Calling

```python
from vectorgov import VectorGov
import google.generativeai as genai

vg = VectorGov(api_key="vg_xxx")
genai.configure(api_key="sua_key")

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=[vg.to_google_tool()],
)

response = model.generate_content("O que é ETP?")
```

### Métodos de Function Calling

| Método | Descrição |
|--------|-----------|
| `vg.to_openai_tool()` | Retorna ferramenta no formato OpenAI |
| `vg.to_anthropic_tool()` | Retorna ferramenta no formato Anthropic |
| `vg.to_google_tool()` | Retorna ferramenta no formato Google |
| `vg.execute_tool_call(tool_call)` | Executa tool_call de qualquer provedor |

---

## Frameworks de Agentes

### LangChain

```bash
pip install 'vectorgov[langchain]'
```

#### VectorGovRetriever

```python
from vectorgov.integrations.langchain import VectorGovRetriever
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# Criar retriever
retriever = VectorGovRetriever(
    api_key="vg_xxx",
    top_k=5,
    mode="balanced",
    filters={"tipo": "lei"},  # Filtros padrão
)

# Usar com RetrievalQA
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    retriever=retriever,
)

answer = qa.invoke("Quando o ETP pode ser dispensado?")
print(answer["result"])
```

#### Com LCEL (LangChain Expression Language)

```python
from vectorgov.integrations.langchain import VectorGovRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

retriever = VectorGovRetriever(api_key="vg_xxx")
llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_template("""
Contexto: {context}

Pergunta: {question}
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

answer = chain.invoke("O que é ETP?")
```

#### VectorGovTool para Agentes

```python
from vectorgov.integrations.langchain import VectorGovTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

tool = VectorGovTool(api_key="vg_xxx")
llm = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente jurídico."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_openai_tools_agent(llm, [tool], prompt)
executor = AgentExecutor(agent=agent, tools=[tool])

result = executor.invoke({"input": "O que diz a lei sobre ETP?"})
```

### LangGraph

```bash
pip install 'vectorgov[langgraph]'
```

#### ReAct Agent

```python
from vectorgov.integrations.langgraph import create_vectorgov_tool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Criar ferramenta VectorGov
tool = create_vectorgov_tool(api_key="vg_xxx", top_k=5)

# Criar agente ReAct
llm = ChatOpenAI(model="gpt-4o-mini")
agent = create_react_agent(llm, tools=[tool])

# Executar
result = agent.invoke({"messages": [("user", "O que é ETP?")]})
print(result["messages"][-1].content)
```

#### Grafo RAG Customizado

```python
from vectorgov.integrations.langgraph import create_retrieval_node, VectorGovState
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# Nó de retrieval VectorGov
retrieval_node = create_retrieval_node(api_key="vg_xxx", top_k=5)

# Nó de geração
def generate(state: VectorGovState) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini")
    context = state.get("context", "")
    query = state.get("query", "")
    response = llm.invoke(f"Contexto: {context}\n\nPergunta: {query}")
    return {"response": response.content}

# Construir grafo
builder = StateGraph(dict)
builder.add_node("retrieve", retrieval_node)
builder.add_node("generate", generate)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

graph = builder.compile()

# Executar
result = graph.invoke({"query": "Quando o ETP pode ser dispensado?"})
print(result["response"])
```

#### Grafo RAG Pré-configurado

```python
from vectorgov.integrations.langgraph import create_legal_rag_graph
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
graph = create_legal_rag_graph(llm=llm, api_key="vg_xxx")

result = graph.invoke({"query": "Quais os critérios de julgamento?"})
print(result["response"])
```

#### VectorGovState

```python
from vectorgov.integrations.langgraph import VectorGovState
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class VectorGovState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    documents: list
    context: str
    sources: list[str]
```

### Google ADK

```bash
pip install 'vectorgov[google-adk]'
```

#### Ferramenta de Busca

```python
from vectorgov.integrations.google_adk import create_search_tool

# Criar ferramenta
search = create_search_tool(api_key="vg_xxx", top_k=5)

# Testar diretamente (sem agente)
result = search("O que é ETP?")
print(result)
```

#### Toolset Completo

```python
from vectorgov.integrations.google_adk import VectorGovToolset

toolset = VectorGovToolset(api_key="vg_xxx")

# Lista ferramentas disponíveis
for tool in toolset.get_tools():
    print(f"- {tool.__name__}")
# - search_brazilian_legislation
# - list_available_documents
# - get_article_text

# Usar com agente ADK
from google.adk.agents import Agent

agent = Agent(
    name="legal_assistant",
    model="gemini-2.0-flash",
    tools=toolset.get_tools(),
)
```

#### Agente ADK Pré-configurado

```python
from vectorgov.integrations.google_adk import create_legal_agent

agent = create_legal_agent(api_key="vg_xxx")
response = agent.run("Quais os critérios de julgamento na licitação?")
print(response)
```

---

## Servidor MCP

O VectorGov pode funcionar como servidor MCP (Model Context Protocol), permitindo integração direta com Claude Desktop, Cursor, Windsurf e outras ferramentas compatíveis.

```bash
pip install 'vectorgov[mcp]'
```

### Configuração no Claude Desktop

Adicione ao arquivo `claude_desktop_config.json`:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "uvx",
            "args": ["vectorgov-mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

Ou se instalou via pip:

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "vectorgov-mcp",
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

### Executar Manualmente

```bash
# Via uvx (sem instalar)
uvx vectorgov-mcp

# Via pip (após instalar)
vectorgov-mcp

# Via Python
python -m vectorgov.mcp
```

### Ferramentas MCP Disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `search_legislation` | Busca semântica em legislação brasileira |
| `list_available_documents` | Lista documentos disponíveis na base |
| `get_article_text` | Obtém texto completo de um artigo específico |

---

## Tratamento de Erros

### Exceções Disponíveis

```python
from vectorgov import (
    VectorGovError,      # Exceção base
    AuthError,           # API key inválida/expirada (401)
    RateLimitError,      # Rate limit excedido (429)
    ValidationError,     # Parâmetros inválidos (400)
    ServerError,         # Erro interno do servidor (500)
    ConnectionError,     # Erro de conexão
    TimeoutError,        # Timeout na requisição
)
```

### Exemplo de Tratamento

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

### Atributos das Exceções

| Exceção | Atributos |
|---------|-----------|
| `VectorGovError` | `message`, `status_code`, `response` |
| `AuthError` | `message` (status_code=401) |
| `RateLimitError` | `message`, `retry_after` (status_code=429) |
| `ValidationError` | `message`, `field` (status_code=400) |

---

## System Prompts

### Prompts Pré-definidos

| Estilo | Descrição |
|--------|-----------|
| `default` | Balanceado, formal, cita fontes |
| `concise` | Respostas curtas e diretas |
| `detailed` | Análise profunda, estruturada |
| `chatbot` | Tom amigável, acessível |

### Uso de Prompts

```python
# Usar prompt pré-definido
results = vg.search("query")
messages = results.to_messages(
    system_prompt=vg.get_system_prompt("detailed")
)

# Listar prompts disponíveis
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']

# Prompt totalmente customizado
custom_prompt = """Você é um advogado especialista em licitações.
Responda de forma técnica e cite artigos específicos."""

messages = results.to_messages(system_prompt=custom_prompt)
```

### Conteúdo dos Prompts

#### default

```
Você é um assistente especializado em legislação brasileira, especialmente em licitações e contratos públicos.

Instruções:
1. Use APENAS as informações do contexto fornecido para responder
2. Se a informação não estiver no contexto, diga que não encontrou
3. Sempre cite as fontes usando o formato [Fonte: Lei X, Art. Y]
4. Seja objetivo e direto nas respostas
5. Use linguagem formal adequada ao contexto jurídico
```

#### concise

```
Você é um assistente jurídico. Responda de forma concisa e direta usando apenas o contexto fornecido. Cite as fontes.
```

#### detailed

```
Você é um especialista em direito administrativo brasileiro.

Ao responder:
1. Analise cuidadosamente todo o contexto fornecido
2. Estruture a resposta em tópicos quando apropriado
3. Cite TODAS as fontes relevantes no formato [Lei X/Ano, Art. Y, §Z]
4. Explique termos técnicos quando necessário
5. Se houver divergências ou exceções, mencione-as
6. Conclua com um resumo prático quando aplicável

Use SOMENTE informações do contexto. Não invente ou extrapole.
```

#### chatbot

```
Você é um assistente virtual amigável especializado em licitações públicas.
Responda de forma clara e acessível, evitando jargão excessivo.
Baseie suas respostas apenas no contexto fornecido e cite as fontes.
```

---

## Referência Completa da API

### Exports do Módulo Principal

```python
from vectorgov import (
    # Cliente principal
    VectorGov,
    
    # Modelos
    SearchResult,
    Hit,
    Metadata,
    
    # Configuração
    SearchMode,
    SYSTEM_PROMPTS,
    
    # Exceções
    VectorGovError,
    AuthError,
    RateLimitError,
    ValidationError,
    ServerError,
    ConnectionError,
    TimeoutError,
    
    # Formatters
    to_langchain_docs,
    to_llamaindex_nodes,
    format_citations,
    create_rag_prompt,
)
```

### Integrações Disponíveis

| Módulo | Exports | Requisitos |
|--------|---------|------------|
| `vectorgov.integrations.langchain` | `VectorGovRetriever`, `VectorGovTool`, `to_langchain_documents` | `langchain`, `langchain-core` |
| `vectorgov.integrations.langgraph` | `VectorGovState`, `create_vectorgov_tool`, `create_retrieval_node`, `create_legal_rag_graph` | `langgraph`, `langchain-core` |
| `vectorgov.integrations.google_adk` | `create_search_tool`, `create_list_documents_tool`, `create_get_article_tool`, `VectorGovToolset`, `create_legal_agent` | `google-adk` |
| `vectorgov.integrations.ollama` | `create_rag_pipeline`, `VectorGovOllama`, `OllamaResponse`, `check_ollama_available`, `list_models`, `generate`, `get_recommended_models` | Nenhum (usa urllib) |
| `vectorgov.integrations.transformers` | `create_rag_pipeline`, `VectorGovRAG`, `RAGResponse`, `format_prompt_for_transformers`, `get_recommended_models`, `estimate_vram_usage` | `transformers`, `torch`, `accelerate` |
| `vectorgov.mcp` | `create_server`, `run_server`, `main` | `mcp` |

---

## Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `VECTORGOV_API_KEY` | Chave de API (formato: `vg_*`) |

```bash
# Definir via ambiente
export VECTORGOV_API_KEY=vg_sua_chave_aqui
```

```python
# Usa automaticamente a variável de ambiente
vg = VectorGov()  # Não precisa passar api_key
```

---

## Exemplos Completos

### Chatbot com Histórico (Ollama)

```python
from vectorgov import VectorGov
from vectorgov.integrations.ollama import VectorGovOllama

vg = VectorGov(api_key="vg_xxx")
rag = VectorGovOllama(vg, model="qwen3:8b")

messages = []

while True:
    user_input = input("Você: ")
    if user_input.lower() in ["sair", "exit", "quit"]:
        break
    
    messages.append({"role": "user", "content": user_input})
    response = rag.chat(messages, use_rag=True)
    messages.append({"role": "assistant", "content": response})
    
    print(f"Assistente: {response}")
```

### API REST com FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vectorgov import VectorGov, VectorGovError

app = FastAPI()
vg = VectorGov()

class Query(BaseModel):
    question: str
    top_k: int = 5
    mode: str = "balanced"

@app.post("/search")
async def search(query: Query):
    try:
        results = vg.search(
            query=query.question,
            top_k=query.top_k,
            mode=query.mode,
        )
        return results.to_dict()
    except VectorGovError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
```

### Pipeline RAG com Streaming (OpenAI)

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
client = OpenAI()

query = "O que é ETP?"
results = vg.search(query)

stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=results.to_messages(query),
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Changelog Resumido

| Versão | Data | Principais Mudanças |
|--------|------|---------------------|
| 0.6.0 | 2025-01-08 | Integração Ollama (RAG local sem dependências) |
| 0.5.0 | 2025-01-08 | Integração HuggingFace Transformers |
| 0.4.0 | 2025-01-08 | LangGraph + Google ADK |
| 0.3.0 | 2025-01-08 | Servidor MCP |
| 0.2.0 | 2025-01-08 | Function Calling + LangChain |
| 0.1.0 | 2025-01-07 | Release inicial |

---

## Suporte

- **GitHub Issues**: https://github.com/euteajudo/vectorgov-sdk/issues
- **Email**: suporte@vectorgov.io
- **Documentação**: https://docs.vectorgov.io
- **Playground**: https://vectorgov.io/playground

---

## Licença

MIT License - veja [LICENSE](https://github.com/euteajudo/vectorgov-sdk/blob/main/LICENSE) para detalhes.

---

> **Última atualização:** Janeiro 2025 | **Versão do SDK:** 0.6.0
