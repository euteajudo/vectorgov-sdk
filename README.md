# VectorGov SDK

SDK Python para acessar bases de conhecimento jurídico VectorGov.

Acesse informações de leis, decretos e instruções normativas brasileiras com 3 linhas de código.

[![PyPI version](https://badge.fury.io/py/vectorgov.svg)](https://badge.fury.io/py/vectorgov)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## SDKs Disponíveis

| Linguagem | Pacote | Repositório |
|-----------|--------|-------------|
| **Python** | [`pip install vectorgov`](https://pypi.org/project/vectorgov/) | Este repositório |
| **TypeScript/JavaScript** | [`npm install vectorgov`](https://www.npmjs.com/package/vectorgov) | [vectorgov-sdk-ts](https://github.com/euteajudo/vectorgov-sdk-ts) |

> **Usando TypeScript/JavaScript?** Veja a documentação completa do SDK TypeScript em [github.com/euteajudo/vectorgov-sdk-ts](https://github.com/euteajudo/vectorgov-sdk-ts)

---

## Índice

- [Instalação](#instalação)
  - [Instalação com Extras](#instalação-com-extras-opcionais)
- [Início Rápido](#início-rápido)
- **Modelos Comerciais (APIs Pagas)**
  - [OpenAI (GPT-4)](#openai)
  - [Google Gemini](#google-gemini)
  - [Anthropic Claude](#anthropic-claude)
  - [Respostas em Streaming](#-respostas-em-streaming)
- **Modelos Open-Source (Gratuitos)**
  - [Ollama (Recomendado)](#integração-com-ollama)
  - [HuggingFace Transformers](#integração-com-huggingface-transformers)
- **Frameworks de Agentes**
  - [Function Calling](#function-calling-agentes)
  - [LangChain](#integração-com-langchain)
  - [LangGraph](#integração-com-langgraph)
  - [Google ADK](#integração-com-google-adk)
- **Integrações**
  - [Servidor MCP](#servidor-mcp-claude-desktop-cursor-etc)
- **Configuração**
  - [Modos de Busca](#modos-de-busca)
  - [Smart Search](#smart-search-busca-inteligente)
  - [Busca Hibrida (Grafo)](#busca-hibrida-semântica--grafo)
  - [Lookup de Dispositivo](#lookup-de-dispositivo)
  - [Busca Textual e Filesystem](#busca-textual-e-filesystem)
  - [Citation Expansion](#citation-expansion-expansão-por-citação)
  - [Filtros](#filtros)
  - [Formatação de Resultados](#formatação-de-resultados)
  - [System Prompts](#system-prompts-customizados)
  - [Feedback](#feedback)
  - [Tratamento de Erros](#tratamento-de-erros)
- **Gerenciamento de Documentos**
  - [Permissoes](#permissões)
  - [Listar e Consultar](#listar-e-consultar-documentos)
  - [Upload e Ingestao (Admin)](#upload-e-ingestão-admin)
  - [Exclusao (Admin)](#exclusão-admin)
- **Documentação para LLMs**
  - [llms.txt](#llmstxt)
  - [CLAUDE.md](#claudemd)
- **Auditoria e Segurança**
  - [Auditoria e Segurança](#auditoria-e-segurança)
- [Obter sua API Key](#obter-sua-api-key)
- **Do Básico ao Avançado**
  - [Nível 1: O Mínimo Necessário](#nível-1-o-mínimo-necessário)
  - [Nível 2: Passando para seu LLM](#nível-2-passando-para-seu-llm)
  - [Nível 3: Feedback](#nível-3-melhorando-o-sistema-com-feedback)
  - [Nível 4: Filtros](#nível-4-refinando-com-filtros)
  - [Nível 5: Modos](#nível-5-controlando-performance-com-modos)
  - [Nível 6: Prompts](#nível-6-controlando-custos-com-prompts)
  - [Nível 7: Auditoria](#nível-7-rastreabilidade-e-auditoria)
  - [Nível 8: Integrações](#nível-8-integrações-avançadas)
  - [Exemplo Completo](#-exemplo-completo-tudo-junto)

---

## Instalação

## Requisitos

- Python **>= 3.10**

```bash
pip install vectorgov
```

### Instalação com Extras (Opcionais)

Algumas integrações requerem dependências adicionais. Instale conforme sua necessidade:

| Extra | Comando | Descrição |
|-------|---------|-----------|
| **LangChain** | `pip install 'vectorgov[langchain]'` | Retriever e Tool para LangChain |
| **LangGraph** | `pip install 'vectorgov[langgraph]'` | Ferramenta para agentes ReAct |
| **Google ADK** | `pip install 'vectorgov[google-adk]'` | Toolset para Google Agent Dev Kit |
| **Transformers** | `pip install 'vectorgov[transformers]'` | RAG com modelos HuggingFace locais |
| **MCP Server** | `pip install 'vectorgov[mcp]'` | Servidor MCP para Claude Desktop |
| **Tudo** | `pip install 'vectorgov[all]'` | Todas as dependências acima |

> **Nota:** A integração com **Ollama** não requer extras - usa apenas a biblioteca padrão do Python.

> **Nota:** Para usar **OpenAI**, **Gemini** ou **Claude**, instale as bibliotecas separadamente:
> ```bash
> pip install openai          # Para OpenAI GPT
> pip install google-generativeai  # Para Google Gemini
> pip install anthropic       # Para Anthropic Claude
> ```

## Início Rápido

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_sua_chave_aqui")

# Buscar legislação
results = vg.search("Quando o ETP pode ser dispensado?")

for hit in results:
    print(f"[{hit.score:.0%}] {hit.source}")
    print(f"  {hit.text[:200]}...")
    print()
```

Saída:
```
[92%] Lei 14.133/2021, Art. 72
  Art. 72. O estudo técnico preliminar será dispensado nos seguintes casos: I - nas
  contratações diretas enquadradas nas hipóteses dos incisos I e II do art. 75...

[87%] Decreto 10.947/2022, Art. 6
  Art. 6º O ETP poderá ser dispensado mediante justificativa do agente de contratação,
  quando se tratar de contratações de baixa complexidade...
```

### O que vem em cada resultado

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `hit.text` | `str` | Texto completo do artigo/parágrafo/inciso |
| `hit.score` | `float` | Relevância (0 a 1) |
| `hit.source` | `str` | Referência legível (ex: `"Lei 14.133/2021, Art. 72"`) |
| `hit.metadata` | `Metadata` | Tipo, número, ano, artigo, dispositivo |
| `hit.page_number` | `int\|None` | Página no PDF original |
| `hit.evidence_url` | `str\|None` | Link direto para evidência verificável |

### Passando para seu LLM (3 linhas)

```python
from openai import OpenAI

query = "Quando o ETP pode ser dispensado?"
results = vg.search(query)

# to_messages() formata contexto + query prontos para o LLM
response = OpenAI().chat.completions.create(
    model="gpt-4o-mini",
    messages=results.to_messages(query),
)
print(response.choices[0].message.content)
```

> Funciona com qualquer LLM: `to_messages()` retorna `list[dict]` compatível com OpenAI, Anthropic, Gemini, Ollama e outros.

---

# 💰 Modelos Comerciais (APIs Pagas)

Use LLMs de provedores comerciais para geração de respostas. Requer API key do provedor.

## OpenAI

```bash
pip install openai
```

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

## Google Gemini

```bash
pip install google-generativeai
```

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

## Anthropic Claude

```bash
pip install anthropic
```

```python
from vectorgov import VectorGov
from anthropic import Anthropic

vg = VectorGov(api_key="vg_xxx")
client = Anthropic(api_key="sk-ant-xxx")

query = "O que é ETP?"
results = vg.search(query)

# Monta o prompt
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

## 🌊 Respostas em Streaming

O VectorGov **não gera respostas** — ele fornece o **contexto jurídico** para seu LLM. Por isso, o streaming é configurado **no seu provedor de LLM**, não no VectorGov.

```
VectorGov                        Seu LLM
   │                                │
   │ vg.search("query")             │
   │ ─────────────────► ~1-2s       │
   │ retorna chunks                 │
   │                                │
   │ results.to_messages()          │
   │ ─────────────────►             │
   │                                │
   │                     llm.create(
   │                         messages=...,
   │                         stream=True  ◄── Configure aqui!
   │                     )
   │                                │
   │                     for chunk in response:
   │                         print(chunk)  ◄── Streaming!
```

### OpenAI com Streaming

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
openai_client = OpenAI()

# Busca contexto (instantâneo, ~1-2s)
results = vg.search("O que é ETP?")
messages = results.to_messages("O que é ETP?")

# Gera resposta com streaming
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    stream=True  # ✅ Habilita streaming
)

# Imprime tokens conforme chegam
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Google Gemini com Streaming

```python
from vectorgov import VectorGov
import google.generativeai as genai

vg = VectorGov(api_key="vg_xxx")
genai.configure(api_key="sua_google_key")

results = vg.search("O que é ETP?")
messages = results.to_messages("O que é ETP?")

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=messages[0]["content"]
)

# Gera resposta com streaming
response = model.generate_content(
    messages[1]["content"],
    stream=True  # ✅ Habilita streaming
)

# Imprime tokens conforme chegam
for chunk in response:
    print(chunk.text, end="", flush=True)
```

### Anthropic Claude com Streaming

```python
from vectorgov import VectorGov
from anthropic import Anthropic

vg = VectorGov(api_key="vg_xxx")
client = Anthropic()

results = vg.search("O que é ETP?")
messages = results.to_messages("O que é ETP?")

# Gera resposta com streaming
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=messages[0]["content"],
    messages=[{"role": "user", "content": messages[1]["content"]}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Ollama com Streaming

```python
from vectorgov import VectorGov
from vectorgov.integrations.ollama import VectorGovOllama

vg = VectorGov(api_key="vg_xxx")
rag = VectorGovOllama(vg, model="qwen3:8b")

# Streaming nativo
for chunk in rag.stream("O que é ETP?"):
    print(chunk, end="", flush=True)
```

### Resumo por Provedor

| Provedor | Como habilitar streaming |
|----------|-------------------------|
| **OpenAI** | `stream=True` no `chat.completions.create()` |
| **Google Gemini** | `stream=True` no `generate_content()` |
| **Anthropic Claude** | `client.messages.stream()` context manager |
| **Ollama** | `rag.stream()` ou `stream=True` na API |
| **LangChain** | `.stream()` em vez de `.invoke()` |
| **Servidor Local** | `stream=True` na API OpenAI-compatible |

> **Importante:** O VectorGov retorna o contexto em ~1-2 segundos (sem streaming necessário). O streaming é útil apenas na etapa de **geração de resposta pelo LLM**, que pode levar 5-30 segundos dependendo do modelo.

---

# 🆓 Modelos Open-Source (Gratuitos)

Use LLMs locais gratuitos para RAG sem custos de API. Ideal para desenvolvimento, prototipagem ou produção com controle total.

## Integração com Ollama

**Recomendado** - Forma mais simples de rodar LLMs localmente.

### Instalação

```bash
# 1. Instale o Ollama: https://ollama.ai/
# 2. Baixe um modelo
ollama pull qwen3:8b
```

Não precisa de dependências extras do Python!

### Pipeline RAG Simples

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

### Classe VectorGovOllama

```python
from vectorgov import VectorGov
from vectorgov.integrations.ollama import VectorGovOllama

vg = VectorGov(api_key="vg_xxx")
rag = VectorGovOllama(vg, model="qwen3:8b", top_k=5)

response = rag.ask("O que é ETP?")

print(response.answer)
print(response.sources)      # Lista de fontes
print(response.latency_ms)   # Latência total
print(response.model)        # Modelo usado
```

### Modelos Recomendados (Ollama)

| Modelo | RAM | Qualidade | Português | Comando |
|--------|-----|-----------|-----------|---------|
| `qwen2.5:0.5b` | 1GB | Básica | Bom | `ollama pull qwen2.5:0.5b` |
| `qwen2.5:3b` | 4GB | Boa | Muito Bom | `ollama pull qwen2.5:3b` |
| `qwen2.5:7b` | 8GB | Muito Boa | **Excelente** | `ollama pull qwen2.5:7b` |
| `qwen3:8b` | 8GB | **Excelente** | **Excelente** | `ollama pull qwen3:8b` |
| `llama3.2:3b` | 4GB | Boa | Bom | `ollama pull llama3.2:3b` |

```python
from vectorgov.integrations.ollama import list_models, get_recommended_models

# Lista modelos instalados
print(list_models())

# Lista modelos recomendados
for name, info in get_recommended_models().items():
    print(f"{name}: {info['description']}")
```

### Chat com Histórico

```python
from vectorgov.integrations.ollama import VectorGovOllama

rag = VectorGovOllama(vg, model="qwen3:8b")

messages = [
    {"role": "user", "content": "O que é ETP?"}
]

response = rag.chat(messages, use_rag=True)
print(response)

# Continua a conversa
messages.append({"role": "assistant", "content": response})
messages.append({"role": "user", "content": "E quando pode ser dispensado?"})

response2 = rag.chat(messages, use_rag=True)
print(response2)
```

---

## Integração com HuggingFace Transformers

Use modelos do HuggingFace Hub diretamente no Python.

### Instalação

```bash
pip install 'vectorgov[transformers]'
# ou
pip install vectorgov transformers torch accelerate
```

### Pipeline RAG Simples

```python
from vectorgov import VectorGov
from vectorgov.integrations.transformers import create_rag_pipeline
from transformers import pipeline

# Inicializa
vg = VectorGov(api_key="vg_xxx")
llm = pipeline("text-generation", model="Qwen/Qwen2.5-3B-Instruct", device_map="auto")

# Cria pipeline RAG
rag = create_rag_pipeline(vg, llm, top_k=5, max_new_tokens=512)

# Usa como função
resposta = rag("Quais os critérios de julgamento na licitação?")
print(resposta)
```

### Classe VectorGovRAG

```python
from vectorgov import VectorGov
from vectorgov.integrations.transformers import VectorGovRAG
from transformers import pipeline

vg = VectorGov(api_key="vg_xxx")
llm = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct", device_map="auto")

rag = VectorGovRAG(vg, llm, top_k=5, temperature=0.1)

response = rag.ask("O que é ETP?")

print(response.answer)
print(response.sources)      # Lista de fontes usadas
print(response.latency_ms)   # Tempo de busca
```

### Modelos Recomendados (HuggingFace)

| Modelo | VRAM | Qualidade | Português |
|--------|------|-----------|-----------|
| `meta-llama/Llama-3.2-1B-Instruct` | 2GB | Básica | Bom |
| `Qwen/Qwen2.5-3B-Instruct` | 6GB | Boa | **Excelente** |
| `meta-llama/Llama-3.2-3B-Instruct` | 6GB | Boa | Bom |
| `Qwen/Qwen2.5-7B-Instruct` | 14GB | Muito Boa | **Excelente** |
| `microsoft/Phi-3-mini-4k-instruct` | 4GB | Boa | Razoável |

```python
from vectorgov.integrations.transformers import get_recommended_models

# Lista modelos com detalhes
for name, info in get_recommended_models().items():
    print(f"{name}: {info['vram_gb']}GB, {info['portuguese']}")
```

### Rodando sem GPU (CPU)

```python
from transformers import pipeline
import torch

# Força CPU com modelo leve
llm = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B-Instruct",
    device="cpu",
    torch_dtype=torch.float32,
)
```

### Modelo Quantizado (4-bit)

```python
from transformers import pipeline, BitsAndBytesConfig
import torch

# Quantização 4-bit (usa ~4GB VRAM para modelo 7B)
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

---

# 🤖 Frameworks de Agentes

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
    messages=[{"role": "user", "content": "O que é ETP?"}],
    tools=[vg.to_anthropic_tool()],
)

# Processar tool_use se houver
for block in response.content:
    if block.type == "tool_use":
        result = vg.execute_tool_call(block)
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

---

## Integração com LangChain

```bash
pip install 'vectorgov[langchain]'
```

### VectorGovRetriever

```python
from vectorgov.integrations.langchain import VectorGovRetriever
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# Criar retriever
retriever = VectorGovRetriever(api_key="vg_xxx", top_k=5)

# Usar com RetrievalQA
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    retriever=retriever,
)

answer = qa.invoke("Quando o ETP pode ser dispensado?")
print(answer["result"])
```

### Com LCEL (LangChain Expression Language)

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

### VectorGovTool para Agentes

```python
from vectorgov.integrations.langchain import VectorGovTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI

tool = VectorGovTool(api_key="vg_xxx")
llm = ChatOpenAI(model="gpt-4o")

# Criar agente com a ferramenta
agent = create_openai_tools_agent(llm, [tool], prompt)
executor = AgentExecutor(agent=agent, tools=[tool])

result = executor.invoke({"input": "O que diz a lei sobre ETP?"})
```

---

## Integração com LangGraph

```bash
pip install 'vectorgov[langgraph]'
```

### ReAct Agent

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

### Grafo RAG Customizado

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

### Grafo RAG Pré-configurado

```python
from vectorgov.integrations.langgraph import create_legal_rag_graph
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
graph = create_legal_rag_graph(llm=llm, api_key="vg_xxx")

result = graph.invoke({"query": "Quais os critérios de julgamento?"})
print(result["response"])
```

---

## Integração com Google ADK

```bash
pip install 'vectorgov[google-adk]'
```

### Ferramenta de Busca

```python
from vectorgov.integrations.google_adk import create_search_tool

# Criar ferramenta
search = create_search_tool(api_key="vg_xxx", top_k=5)

# Testar diretamente (sem agente)
result = search("O que é ETP?")
print(result)
```

### Toolset Completo

```python
from vectorgov.integrations.google_adk import VectorGovToolset

toolset = VectorGovToolset(api_key="vg_xxx")

# Lista ferramentas disponíveis
for tool in toolset.get_tools():
    print(f"- {tool.__name__}")
# - search_brazilian_legislation
# - list_legal_documents
# - get_article_text

# Usar com agente ADK
from google.adk.agents import Agent

agent = Agent(
    name="legal_assistant",
    model="gemini-2.0-flash",
    tools=toolset.get_tools(),
)
```

### Agente ADK Pré-configurado

```python
from vectorgov.integrations.google_adk import create_legal_agent

agent = create_legal_agent(api_key="vg_xxx")

response = agent.run("Quais os critérios de julgamento na licitação?")
print(response)
```

---

# 🔌 Integrações

## Servidor MCP (Claude Desktop, Cursor, etc.)

O VectorGov pode funcionar como servidor MCP (Model Context Protocol), permitindo integração direta com Claude Desktop, Cursor, Windsurf e outras ferramentas compatíveis.

### Instalação

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

### Ferramentas Disponíveis

O servidor MCP expõe três ferramentas para Claude:

| Ferramenta | Descrição |
|------------|-----------|
| `search_legislation` | Busca semântica em legislação brasileira |
| `list_available_documents` | Lista documentos disponíveis na base |
| `get_article_text` | Obtém texto completo de um artigo específico |

---

# ⚙️ Configuração

## Modos de Busca

| Modo | Descrição | Latência | Cache Padrão | Uso Recomendado |
|------|-----------|----------|--------------|-----------------|
| `fast` | Busca rápida, sem reranking | ~2s | ❌ Desligado | Chatbots, alta escala |
| `balanced` | Busca com reranking | ~5s | ❌ Desligado | **Uso geral (default)** |
| `precise` | Busca com HyDE + reranking | ~15s | ❌ Desligado | Análises críticas |

> **Importante:** O modo de busca **não afeta** a quantidade de tokens enviados ao seu LLM. Todos os modos retornam o mesmo número de resultados (controlado por `top_k`). A diferença está na **qualidade** dos resultados:
> - **HyDE** (modo `precise`): Gera documentos hipotéticos para melhorar a busca - processamento extra no backend VectorGov
> - **Reranker** (modos `balanced` e `precise`): Reordena resultados por relevância - processamento extra no backend VectorGov
>
> Ou seja: você recebe resultados **mais relevantes**, não **mais resultados**.

> **Nota:** O cache está desabilitado por padrão em todos os modos para proteger sua privacidade.
> Veja a seção [Aviso de Privacidade](#️-aviso-de-privacidade---cache-compartilhado) para mais detalhes.

```python
# Busca rápida (chatbots)
results = vg.search("query", mode="fast")

# Busca balanceada (default)
results = vg.search("query", mode="balanced")

# Busca precisa (análises)
results = vg.search("query", mode="precise")

# Qualquer modo COM cache (trade-off: privacidade vs latência)
results = vg.search("query", mode="fast", use_cache=True)
```

## Smart Search (Busca Inteligente)

O `smart_search()` e um endpoint turnkey que executa o pipeline completo de analise juridica. O pipeline decide tudo: quantidade de chunks, estrategia de busca, expansao de citacoes. O cliente so faz a pergunta.

```python
# Uso basico - o pipeline decide tudo
result = vg.smart_search("Quais os criterios de julgamento na Lei 14.133?")

# Com cache habilitado
result = vg.smart_search("criterios de julgamento", use_cache=True)
```

**Parametros aceitos:**

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `query` | str | - | Pergunta (3 a 1000 caracteres) |
| `use_cache` | bool | `False` | Usar cache semantico |

> **Importante:** `smart_search()` nao aceita `top_k`, `mode`, `filters` ou qualquer outro parametro de controle. O pipeline toma todas as decisoes automaticamente. Enviar campos extras resulta em erro 422.

**Resposta:**

O retorno e um `SmartSearchResult` (herda de `SearchResult`), com todos os campos de curadoria e verificabilidade:

```python
result = vg.smart_search("criterios de julgamento")

for hit in result.hits:
    print(hit.source)             # "Lei 14.133/2021, Art. 33"
    print(hit.nota_especialista)  # Nota do especialista (curadoria)
    print(hit.evidence_url)       # Link para verificacao
    print(hit.document_url)       # Link para PDF com highlight

# Compativel com todos os metodos de formatacao
xml = result.to_xml("full")
messages = result.to_messages("Quais os criterios?", level="full")
schema = result.to_response_schema()
```

**Fallback para planos sem acesso:**

```python
try:
    result = vg.smart_search("query")
except TierError:
    # Fallback automatico para busca tradicional
    result = vg.search("query", mode="precise")
```

## Busca Hibrida (Semântica + Grafo)

O metodo `hybrid()` combina busca semantica com expansao via grafo de citacoes normativas. Retorna evidencias diretas e artigos citados.

```python
# Busca hibrida com expansao de grafo
result = vg.hybrid("Dispensa de licitacao por baixo valor")

# Evidencias diretas (busca semantica)
for hit in result.hits:
    print(f"{hit.source}: {hit.text[:100]}...")

# Expansao via grafo (artigos citados)
for node in result.graph_nodes:
    print(f"[hop={node.hop}] {node.source}: {node.text[:100]}...")

# Contexto formatado para LLM (inclui ambas secoes)
context = result.to_context()
messages = result.to_messages("Dispensa de licitacao por baixo valor")
```

**Parametros:**

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `query` | str | - | Pergunta (3-1000 caracteres) |
| `top_k` | int | 8 | Resultados diretos (1-20) |
| `hops` | int | 1 | Saltos no grafo (1-2) |
| `graph_expansion` | str | `"bidirectional"` | Direcao da expansao |
| `token_budget` | int | 3500 | Limite de tokens do contexto |

**Modelo retornado:** `HybridResult` (herda de `BaseResult`), com:
- `hits` — Evidencias diretas (lista de `Hit`)
- `graph_nodes` — Expansao via grafo (lista de `Hit` com `hop` e `graph_score`)
- `stats` — Estatisticas da busca (seeds, graph_nodes, tokens, truncated)

## Lookup de Dispositivo

O metodo `lookup()` resolve referencias textuais para o dispositivo normativo exato, incluindo contexto hierarquico (pai e irmaos).

```python
# Buscar dispositivo por referencia textual
result = vg.lookup("Art. 33 da Lei 14.133")

if result.status == "found":
    print(f"Encontrado: {result.match.text[:200]}...")

    # Chunk pai (artigo completo quando match e paragrafo/inciso)
    if result.parent:
        print(f"Pai: {result.parent.span_id}")

    # Irmaos (mesmo nivel hierarquico)
    for sib in result.siblings:
        marker = ">" if sib.is_current else " "
        print(f"  {marker} {sib.span_id}: {sib.text[:80]}...")

elif result.status == "ambiguous":
    print("Referencia ambigua. Candidatos:")
    for c in result.candidates:
        print(f"  - {c.document_id}: {c.text[:80]}...")
```

**Parametros:**

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `reference` | str | - | Referencia textual (ex: "Art. 33 da Lei 14.133") |
| `include_parent` | bool | `True` | Incluir chunk pai |
| `include_siblings` | bool | `True` | Incluir irmaos |

**Status possiveis:** `found`, `not_found`, `ambiguous`, `parse_failed`

## Busca Textual e Filesystem

Novos na v0.16.0 — 4 metodos complementares para busca deterministiica e leitura de textos canonicos.

### `grep()` — Busca textual exata

```python
result = vg.grep("dispensa de licitacao", max_results=5)
for m in result:
    print(f"{m.span_id}: {m.matched_line}")

# Filtrar por documento
result = vg.grep("art. 75", document_id="LEI-14133-2021")
```

### `filesystem_search()` — Indice curado

```python
# Modo auto detecta tipo da query
result = vg.filesystem_search("art. 75 da Lei 14.133")
for hit in result:
    print(f"[{hit.source}] {hit.breadcrumb}")
```

### `merged()` — Dual-path (hibrida + filesystem)

```python
result = vg.merged("prazo para impugnacao do edital", top_k=5)
for hit in result:
    print(f"[{','.join(hit.sources)}] {hit.breadcrumb}: {hit.score:.2f}")
print(f"Mutual: {result.mutual_count} hits em ambas fontes")
```

### `read_canonical()` — Texto canonico completo

```python
# Documento inteiro
doc = vg.read_canonical("LEI-14133-2021")
print(f"{doc.token_count} tokens")

# Dispositivo especifico
art = vg.read_canonical("LEI-14133-2021", span_id="ART-075")
print(art.text)
```

## Citation Expansion (Expansão por Citação)

Quando um artigo menciona outro dispositivo legal (ex: "conforme art. 18 da Lei 14.133"), o backend automaticamente busca e inclui esse chunk referenciado nos resultados. Isso acontece de forma transparente — não é preciso ativar nada.

### Como Acessar

```python
results = vg.search("O que é ETP?")

# Chunks expandidos (dicts vindos da API)
for ec in results.expanded_chunks:
    print(f"Citação: {ec.get('source_citation_raw', '?')}")
    print(f"Texto: {ec.get('text', '')[:100]}...")
    print(f"Fonte: {ec.get('document_id')}#{ec.get('span_id')}")
    print()

# Estatísticas de expansão
if results.expansion_stats:
    stats = results.expansion_stats
    print(f"Encontradas: {stats.get('citations_found', 0)}")
    print(f"Expandidas: {stats.get('expanded_chunks_count', 0)}")
    print(f"Tempo: {stats.get('expansion_time_ms', 0):.0f}ms")
```

### Campos do Chunk Expandido (`dict`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `text` | str | Texto completo do chunk expandido |
| `document_id` | str | ID do documento (ex: `LEI-14133-2021`) |
| `span_id` | str | ID do dispositivo (ex: `ART-018`) |
| `node_id` | str | ID canônico `leis:{doc}#{span}` |
| `device_type` | str | `article`, `paragraph`, `inciso`, `alinea` |
| `source_chunk_id` | str | ID do chunk que continha a citação |
| `source_citation_raw` | str | Texto original (ex: `art. 18 da Lei 14.133`) |

### Contexto Estruturado para LLM

`to_context()` já inclui os chunks expandidos numa seção separada:

```python
context = results.to_context()
# === EVIDÊNCIA DIRETA (resultados da busca) ===
# [1] Lei 14.133/2021, Art. 72
# Art. 72. O estudo técnico preliminar será dispensado...
#
# === TRECHOS CITADOS (expansão por citação) ===
# [XC-1] TRECHO CITADO (expansão por citação)
#   CITADO POR: IN-65-2021#ART-005
#   CITAÇÃO ORIGINAL: art. 18 da Lei 14.133
#   ...

# Para excluir chunks expandidos do contexto:
context = results.to_context(include_expanded=False)
```

### Quando é Útil

- **Análises jurídicas**: contexto completo das referências normativas
- **Cadeia de citações**: entender como artigos se relacionam
- **Respostas mais completas**: dispositivos referenciados aparecem automaticamente

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

O SDK inclui 4 prompts pré-definidos otimizados para diferentes casos de uso. Você também pode criar prompts personalizados para ter **controle total sobre tokens e custos**.

### Prompts Disponíveis

| Prompt | Tokens | Uso Recomendado |
|--------|--------|-----------------|
| `concise` | ~40 | Chatbots, alto volume, economia máxima |
| `chatbot` | ~60 | Atendimento ao público, linguagem acessível |
| `default` | ~95 | Uso geral, equilíbrio entre qualidade e custo |
| `detailed` | ~120 | Pareceres jurídicos, análises detalhadas |

### Conteúdo dos Prompts

<details>
<summary><b>default</b> (~95 tokens)</summary>

```text
Você é um assistente especializado em legislação brasileira, especialmente em licitações e contratos públicos.

Instruções:
1. Use APENAS as informações do contexto fornecido para responder
2. Se a informação não estiver no contexto, diga que não encontrou
3. Sempre cite as fontes usando o formato [Fonte: Lei X, Art. Y]
4. Seja objetivo e direto nas respostas
5. Use linguagem formal adequada ao contexto jurídico
```
</details>

<details>
<summary><b>concise</b> (~40 tokens) - Economia máxima</summary>

```text
Você é um assistente jurídico. Responda de forma concisa e direta usando apenas o contexto fornecido. Cite as fontes.
```
</details>

<details>
<summary><b>detailed</b> (~120 tokens) - Análises completas</summary>

```text
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
</details>

<details>
<summary><b>chatbot</b> (~60 tokens) - Linguagem acessível</summary>

```text
Você é um assistente virtual amigável especializado em licitações públicas.
Responda de forma clara e acessível, evitando jargão excessivo.
Baseie suas respostas apenas no contexto fornecido e cite as fontes.
```
</details>

### Impacto no Custo por LLM

Custo estimado **por requisição** (prompt + contexto ~1000 tokens + resposta ~500 tokens):

| LLM | `concise` | `default` | `detailed` |
|-----|-----------|-----------|------------|
| **GPT-4o** | ~$0.0077 | ~$0.0078 | ~$0.0079 |
| **GPT-4o-mini** | ~$0.00046 | ~$0.00047 | ~$0.00048 |
| **Claude Sonnet** | ~$0.0107 | ~$0.0108 | ~$0.0109 |
| **Gemini 1.5 Flash** | ~$0.00023 | ~$0.00023 | ~$0.00024 |

> **Nota:** O system prompt representa ~5-10% do custo total. O maior impacto vem do **contexto** (chunks) e da **resposta gerada**.

### Uso Básico

```python
# Usar prompt pré-definido
results = vg.search("query")
messages = results.to_messages(
    query="O que é ETP?",
    system_prompt=vg.get_system_prompt("detailed")
)

# Ver prompts disponíveis
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']

# Ver conteúdo de um prompt
print(vg.get_system_prompt("concise"))
```

### Prompt Personalizado (Controle Total)

Crie seu próprio prompt para ter controle total sobre tokens e comportamento:

```python
# Prompt ultra-curto para economia máxima (~15 tokens)
meu_prompt = "Responda usando apenas o contexto. Cite fontes."

messages = results.to_messages(
    query="O que é ETP?",
    system_prompt=meu_prompt
)

# Prompt especializado para seu domínio
prompt_pregao = """Você é um pregoeiro experiente.
Responda apenas sobre pregão eletrônico.
Cite artigos da Lei 14.133/2021."""

messages = results.to_messages(
    query="Qual o prazo para impugnação?",
    system_prompt=prompt_pregao
)

# Sem system prompt (só contexto + pergunta)
messages = results.to_messages(
    query="O que é ETP?",
    system_prompt=""
)
```

### Dicas para Otimizar Custos

1. **Chatbots de alto volume**: Use `concise` ou prompt personalizado mínimo
2. **Reduza o contexto**: `top_k=3` ao invés de 5 reduz ~40% dos tokens
3. **Modelos mais baratos**: GPT-4o-mini é 17x mais barato que GPT-4o
4. **Monitore tokens**: Use `tiktoken` para estimar custos antes de enviar

```python
import tiktoken

def estimar_tokens(messages, model="gpt-4o"):
    enc = tiktoken.encoding_for_model(model)
    return sum(len(enc.encode(m["content"])) for m in messages)

messages = results.to_messages("O que é ETP?")
print(f"Esta requisição usará ~{estimar_tokens(messages)} tokens de input")
```

📖 **[Guia Completo de System Prompts](docs/guides/system-prompts.md)** - Documentação detalhada com todos os cenários de uso.

## Feedback

Ajude a melhorar o sistema enviando feedback sobre a qualidade das respostas. O feedback é usado para:
- Melhorar o ranking de resultados
- Treinar modelos futuros (fine-tuning)
- Monitorar a qualidade do sistema

### Feedback Básico (Busca VectorGov)

```python
results = vg.search("O que é ETP?")

# Após verificar que o resultado foi útil
vg.feedback(results.query_id, like=True)

# Se o resultado não foi útil
vg.feedback(results.query_id, like=False)
```

### Feedback com LLM Externo (OpenAI, Gemini, Claude, etc.)

Quando você usa seu próprio LLM para gerar respostas, use `store_response()` para habilitar o feedback:

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
openai_client = OpenAI()

# 1. Busca contexto no VectorGov
query = "O que é ETP?"
results = vg.search(query)

# 2. Gera resposta com seu LLM
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=results.to_messages(query)
)
answer = response.choices[0].message.content

# 3. Salva a resposta no VectorGov para habilitar feedback
stored = vg.store_response(
    query=query,
    answer=answer,
    provider="OpenAI",
    model="gpt-4o",
    chunks_used=len(results)
)

# 4. Agora o feedback funciona!
vg.feedback(stored.query_hash, like=True)
```

### Parâmetros do store_response()

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `query` | str | ✅ | A pergunta original |
| `answer` | str | ✅ | A resposta gerada pelo LLM |
| `provider` | str | ✅ | Nome do provedor (OpenAI, Google, Anthropic) |
| `model` | str | ✅ | ID do modelo (gpt-4o, gemini-2.0-flash) |
| `chunks_used` | int | ❌ | Quantidade de chunks usados como contexto |
| `latency_ms` | float | ❌ | Latência total em ms |
| `retrieval_ms` | float | ❌ | Tempo de busca em ms |
| `generation_ms` | float | ❌ | Tempo de geração do LLM em ms |

### Retorno do store_response()

```python
stored = vg.store_response(...)

stored.success     # bool - Se foi salvo com sucesso
stored.query_hash  # str - Hash para usar em feedback()
stored.message     # str - Mensagem de status
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
    hit.text              # Texto do chunk
    hit.score             # Relevância (0-1)
    hit.source            # Fonte formatada ("Lei 14.133/2021, Art. 33")
    hit.metadata          # Metadados (tipo, numero, ano, artigo, dispositivo)
    hit.page_number       # Página no PDF original (int ou None)
    hit.evidence_url      # Link para evidência verificável (str ou None)
    hit.nota_especialista # Nota do especialista jurídico (str ou None)
    hit.chunk_id          # ID interno (para debugging)
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

---

# ⚠️ Aviso de Privacidade - Cache Compartilhado

## Entendendo o Cache Semântico

O VectorGov utiliza um **cache semântico compartilhado** entre todos os clientes da API. Isso significa:

| Aspecto | Comportamento |
|---------|---------------|
| **Suas perguntas** | Podem ser armazenadas no cache |
| **Suas respostas** | Podem ser servidas a outros clientes com perguntas similares |
| **Perguntas de outros** | Você pode receber respostas já geradas por outros clientes |

### Trade-off: Performance vs Privacidade

| Cache Habilitado | Cache Desabilitado |
|------------------|-------------------|
| ✅ Latência menor (~0.1s para cache hit) | ❌ Latência maior (~5-15s) |
| ✅ Resposta pode vir pré-validada | ❌ Sempre gera resposta nova |
| ❌ Perguntas visíveis a outros clientes | ✅ Total privacidade |
| ❌ Pode receber respostas de outros | ✅ Respostas exclusivas |

### Controle de Cache

Por padrão, o cache está **DESABILITADO** para proteger sua privacidade:

```python
# Padrão: SEM cache (privado)
results = vg.search("O que é ETP?")  # use_cache=False implícito

# Explicitamente habilitando cache (perda de privacidade)
results = vg.search("O que é ETP?", use_cache=True)
```

### Quando Habilitar o Cache?

| Use Cache | Não Use Cache |
|-----------|---------------|
| Perguntas genéricas sobre legislação | Perguntas com dados sensíveis |
| Alta escala de usuários (chatbots públicos) | Análises confidenciais |
| Demos e testes | Ambientes corporativos restritos |
| Quando latência é crítica | Quando privacidade é prioridade |

### Exemplo de Uso Consciente

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Pergunta genérica - pode usar cache
results = vg.search("Quais os critérios de julgamento?", use_cache=True)

# Pergunta específica com dados sensíveis - NÃO usar cache
results = vg.search("Contrato da empresa XYZ foi regular?", use_cache=False)
```

> **Nota:** O cache desabilitado não afeta a qualidade da resposta, apenas a latência.
> O sistema de duas fases garante alta precisão independente do cache.

---

## Documentação para LLMs

O VectorGov fornece documentação estruturada para facilitar a integração com assistentes de IA e LLMs.

### llms.txt

Seguindo o padrão [llmstxt.org](https://llmstxt.org/), disponibilizamos documentação otimizada para consumo por LLMs:

**URL:** [https://vectorgov.io/llms.txt](https://vectorgov.io/llms.txt)

Este arquivo contém:
- Visão geral do SDK e API
- Exemplos de código prontos para uso
- Documentação de todos os métodos (`search`, `hybrid`, `lookup`, `feedback`, `store_response`)
- Integrações com OpenAI, Gemini e Claude
- Modos de busca e parâmetros disponíveis
- Tratamento de erros

Assistentes de IA podem acessar este arquivo para aprender a usar o VectorGov automaticamente.

### CLAUDE.md

Instruções específicas para o Claude Code (CLI):

**URL:** [https://vectorgov.io/CLAUDE.md](https://vectorgov.io/CLAUDE.md)

Contém:
- Padrões de código recomendados
- Exemplos de integração com diferentes LLMs
- Boas práticas para uso do SDK
- Estrutura de resposta e tratamento de erros

### robots.txt

O arquivo `robots.txt` em [https://vectorgov.io/robots.txt](https://vectorgov.io/robots.txt) permite acesso de crawlers de IA:

```
User-agent: GPTBot
User-agent: ChatGPT-User
User-agent: Claude-Web
User-agent: anthropic-ai
User-agent: Googlebot
Allow: /llms.txt
Allow: /CLAUDE.md
```

---

## Obter sua API Key

### 1) Criar uma API key (site)

1. Faça login no VectorGov.
2. Acesse **API Keys**: `https://vectorgov.io/api-keys`
3. Clique em **Nova API Key**, informe um nome (ex.: "Meu app dev") e confirme.
4. **Copie e salve a chave completa** (ela é exibida uma única vez).

### 2) Testar no Playground (interface web)

1. Acesse o **Playground**: `https://vectorgov.io/playground`
2. Faça uma pergunta e ajuste as configurações (modo, top_k, cache).
3. Use a seção **Código equivalente** para copiar um exemplo (Python/TypeScript/cURL)
   e substitua `vg_sua_chave` pela sua API key.

### 3) Ver limite e acompanhar uso da API key

- Em `https://vectorgov.io/api-keys`, cada chave mostra:
  - **Status** (ativa/revogada)
  - **Rate limit** (requisições por minuto)
  - **Total de requests** (contador acumulado)
- Para detalhes do minuto atual, abra a configuração da chave e veja:
  - **Uso no minuto atual**
  - **Restantes no minuto**
- Para logs detalhados de chamadas, use **Uso da API** (quando disponível no seu menu).

## Documentação

- [Documentação](https://vectorgov.io/documentacao)
- [API Keys](https://vectorgov.io/api-keys)
- [Playground](https://vectorgov.io/playground)

## Suporte

- [GitHub Issues](https://github.com/euteajudo/vectorgov-sdk/issues)
- Email: suporte@vectorgov.io

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

# 📁 Gerenciamento de Documentos

O SDK permite gerenciar documentos na base de conhecimento. Algumas operações são restritas a **administradores**.

## Permissões

| Operação | Permissão | Método |
|----------|-----------|--------|
| Listar documentos | Todos | `list_documents()` |
| Ver detalhes | Todos | `get_document(id)` |
| Upload de PDF | Admin | `upload_pdf()` |
| Acompanhar ingestão | Admin | `get_ingest_status()` |
| Excluir documento | Admin | `delete_document()` |

## Listar e Consultar Documentos

Qualquer usuário autenticado pode listar e consultar documentos.

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Listar todos os documentos
docs = vg.list_documents()
print(f"Total: {docs.total} documentos")

for doc in docs.documents:
    print(f"- {doc.document_id}: {doc.tipo_documento} {doc.numero}/{doc.ano}")
    print(f"  Chunks: {doc.chunks_count}, Enriquecidos: {doc.enriched_count}")
    print(f"  Progresso: {doc.enrichment_progress:.0%}")

# Paginação
docs = vg.list_documents(page=2, limit=10)

# Detalhes de um documento específico
doc = vg.get_document("LEI-14133-2021")
print(f"Documento: {doc.titulo}")
print(f"Status: {'Enriquecido' if doc.is_enriched else 'Pendente'}")
```

## Upload e Ingestão (Admin)

```python
# Upload de PDF (máx 50 MB)
uploaded = vg.upload_pdf(
    file_path="lei_14133.pdf",
    tipo_documento="LEI",   # LEI, DECRETO, IN, PORTARIA, RESOLUCAO
    numero="14133",
    ano=2021,
)
print(f"Task: {uploaded.task_id}")

# Acompanhar progresso da ingestão
import time
while True:
    status = vg.get_ingest_status(uploaded.task_id)
    print(f"[{status.progress:.0%}] {status.status} - {status.message}")
    if status.status in ("completed", "failed"):
        break
    time.sleep(3)

print(f"Chunks criados: {status.chunks_created}")
```

## Exclusão (Admin)

```python
result = vg.delete_document("LEI-14133-2021")
print(result.message)  # "Documento removido com sucesso"
```

> **Nota:** `start_enrichment()` e `get_enrichment_status()` foram **descontinuados** em 31/01/2026.
> O sistema agora usa ingestão determinística (SpanParser + ArticleOrchestrator).

## Modelos de Resposta

### DocumentSummary

```python
@dataclass
class DocumentSummary:
    document_id: str      # Ex: "LEI-14133-2021"
    tipo_documento: str   # Ex: "LEI", "DECRETO", "IN"
    numero: str           # Ex: "14133"
    ano: int              # Ex: 2021
    titulo: str           # Título do documento
    descricao: str        # Descrição opcional
    chunks_count: int     # Total de chunks
    enriched_count: int   # Chunks enriquecidos

    # Propriedades calculadas
    is_enriched: bool           # True se todos chunks enriquecidos
    enrichment_progress: float  # 0.0 a 1.0
```

---

# Auditoria e Segurança

O VectorGov possui um sistema de guardrails que monitora e registra eventos de segurança. Usuários da SDK podem acessar logs de auditoria filtrados por sua API Key.

## Por que Auditoria é Importante?

| Caso de Uso | Descrição |
|-------------|-----------|
| **Compliance** | Atenda requisitos de LGPD, auditoria interna e governança |
| **Segurança** | Detecte tentativas de injeção, vazamento de PII e uso suspeito |
| **Debugging** | Investigue problemas de integração e erros de validação |
| **Monitoramento** | Acompanhe métricas de uso, latência e padrões de queries |
| **Billing** | Entenda o consumo da API para planejamento de custos |

## Privacidade: Seus Logs São Isolados

O VectorGov é uma plataforma **multi-tenant**. Isso significa que:

| Aspecto | Como Funciona |
|---------|---------------|
| **Isolamento** | Cada API Key só acessa seus próprios logs |
| **Filtro Automático** | O backend filtra por `api_key_id` automaticamente |
| **Sem Acesso Cruzado** | Impossível ver logs de outras organizações |
| **Dados Sensíveis** | Queries podem conter informações confidenciais |

```python
# Empresa A só vê logs da Empresa A
vg_a = VectorGov(api_key="vg_empresa_a_xxx")
logs_a = vg_a.get_audit_logs()  # Apenas logs da Empresa A

# Empresa B só vê logs da Empresa B
vg_b = VectorGov(api_key="vg_empresa_b_yyy")
logs_b = vg_b.get_audit_logs()  # Apenas logs da Empresa B
```

## Métodos Disponíveis

O SDK oferece 3 métodos para acessar dados de auditoria:

| Método | Função | Retorno |
|--------|--------|---------|
| `get_audit_logs()` | Lista eventos de auditoria com filtros | `AuditLogsResponse` |
| `get_audit_stats()` | Estatísticas agregadas de um período | `AuditStats` |
| `get_audit_event_types()` | Lista tipos de eventos disponíveis | `list[str]` |

---

## `get_audit_logs()` - Investigação e Compliance

### Por que é Importante?

| Cenário | Como o Método Ajuda |
|---------|---------------------|
| **Investigação de Incidentes** | Veja exatamente o que aconteceu, quando e qual query causou o problema |
| **Compliance LGPD** | Prove que dados pessoais foram detectados e tratados adequadamente |
| **Debugging** | Identifique queries mal formadas ou que causam erros de validação |
| **Auditoria Interna** | Documente uso da API para relatórios de governança |

### O que Cada Campo Retornado Significa

| Campo | Significado | Ação Recomendada |
|-------|-------------|------------------|
| `event_type` | Tipo do evento (ex: `pii_detected`) | Filtre por tipos críticos |
| `severity` | Gravidade (`info`, `warning`, `critical`) | Monitore `critical` em tempo real |
| `risk_score` | Score de risco de 0.0 a 1.0 | Investigue scores > 0.7 |
| `action_taken` | O que o sistema fez (`logged`, `blocked`, `warned`) | Revise ações `blocked` |
| `query_text` | Query que gerou o evento (truncada) | Use para reproduzir problemas |
| `detection_types` | O que foi detectado (ex: `["cpf", "email"]`) | Identifique padrões de PII |

### Exemplo de Uso

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Listar logs da sua API Key
logs = vg.get_audit_logs(
    limit=50,
    severity="warning",         # Opcional: info, warning, critical
    event_type="pii_detected",  # Opcional: filtrar por tipo
    start_date="2025-01-01",    # Opcional: data início
    end_date="2025-01-18"       # Opcional: data fim
)

for log in logs.logs:
    print(f"[{log.severity}] {log.event_type}: {log.query_text}")
    print(f"  Ação: {log.action_taken}")
    print(f"  Risk Score: {log.risk_score}")
    print(f"  Data: {log.created_at}")
```

---

## `get_audit_stats()` - Visão Gerencial e Tendências

### Por que é Importante?

| Cenário | Como o Método Ajuda |
|---------|---------------------|
| **Dashboard Executivo** | Mostre métricas de segurança para stakeholders |
| **Identificação de Tendências** | Detecte aumento de tentativas de injection |
| **Planejamento de Capacidade** | Entenda volume de uso para sizing |
| **KPIs de Segurança** | Acompanhe taxa de bloqueios vs requisições totais |

### Métricas Retornadas

| Campo | Significado | Meta Ideal |
|-------|-------------|------------|
| `total_events` | Total de eventos no período | Crescimento controlado |
| `blocked_count` | Requisições bloqueadas | Próximo de 0 |
| `warning_count` | Avisos gerados | Monitorar tendência |
| `events_by_type` | Distribuição por tipo | Maioria deve ser `search_completed` |
| `events_by_severity` | Distribuição por gravidade | Maioria deve ser `info` |

### Exemplo de Uso

```python
# Obter estatísticas dos últimos 30 dias
stats = vg.get_audit_stats(days=30)

print(f"Total de eventos: {stats.total_events}")
print(f"Bloqueados: {stats.blocked_count}")
print(f"Alertas: {stats.warning_count}")

# Por tipo de evento
print("\nPor tipo:")
for event_type, count in stats.events_by_type.items():
    print(f"  {event_type}: {count}")

# Por severidade
print("\nPor severidade:")
for severity, count in stats.events_by_severity.items():
    print(f"  {severity}: {count}")
```

---

## `get_audit_event_types()` - Descoberta e Integração

### Por que é Importante?

| Cenário | Como o Método Ajuda |
|---------|---------------------|
| **Construir Interfaces** | Popular dropdowns de filtro dinamicamente |
| **Manter Compatibilidade** | Descobrir novos tipos de eventos adicionados |
| **Documentação** | Gerar docs automáticos dos eventos possíveis |
| **Validação** | Verificar se um tipo de evento existe antes de filtrar |

### Exemplo de Uso

```python
# Listar todos os tipos de eventos disponíveis
event_types = vg.get_audit_event_types()

print("Tipos de eventos disponíveis:")
for event_type in event_types:
    print(f"  - {event_type}")

# Usar para popular um dropdown de filtro
# event_types = ['pii_detected', 'injection_blocked', 'search_completed', ...]
```

---

## Eventos Monitorados

| Evento | Categoria | Descrição |
|--------|-----------|-----------|
| `pii_detected` | security | Dados pessoais detectados na query |
| `injection_detected` | security | Tentativa de prompt injection detectada |
| `injection_blocked` | security | Prompt injection bloqueado |
| `low_relevance_query` | validation | Query com baixa relevância para o contexto |
| `citation_invalid` | validation | Citação não encontrada nos chunks |
| `circuit_breaker_open` | performance | Circuit breaker aberto (serviço indisponível) |
| `circuit_breaker_close` | performance | Circuit breaker fechado (serviço restaurado) |

## Modelos de Resposta

### AuditLog

```python
@dataclass
class AuditLog:
    id: str
    event_type: str           # pii_detected, injection_blocked, etc
    event_category: str       # security, performance, validation
    severity: str             # info, warning, critical
    query_text: str | None    # Query que gerou o evento
    detection_types: list[str]  # Tipos de detecção (ex: ["cpf", "email"])
    risk_score: float | None  # Score de risco (0.0 a 1.0)
    action_taken: str | None  # Ação tomada (blocked, allowed, logged)
    endpoint: str | None      # Endpoint chamado
    created_at: str           # Timestamp ISO
    details: dict             # Detalhes adicionais
```

### AuditLogsResponse

```python
@dataclass
class AuditLogsResponse:
    logs: list[AuditLog]
    total: int
    page: int
    pages: int
    limit: int
```

### AuditStats

```python
@dataclass
class AuditStats:
    total_events: int
    events_by_type: dict[str, int]
    events_by_severity: dict[str, int]
    events_by_category: dict[str, int]
    blocked_count: int
    warning_count: int
    period_days: int
```

## Boas Práticas de Segurança

1. **Monitore regularmente**: Verifique logs de auditoria periodicamente
2. **Configure alertas**: Use `severity="critical"` para eventos importantes
3. **Evite PII nas queries**: Não inclua CPF, email ou dados pessoais nas perguntas
4. **Respeite rate limits**: Muitos bloqueios podem indicar uso inadequado
5. **Reporte falsos positivos**: Entre em contato se detectores estiverem incorretos

---

# 🚀 Do Básico ao Avançado: Construindo sua Integração

Esta seção mostra a **progressão natural** de uso do VectorGov SDK, começando pelo mínimo necessário e adicionando features conforme sua necessidade cresce.

## Nível 1: O Mínimo Necessário

**Tudo que você precisa para começar:** uma API key e o método `search()`.

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_sua_chave")
results = vg.search("O que é ETP?")

for hit in results:
    print(f"[{hit.score:.0%}] {hit.source}")
    print(f"  {hit.text[:200]}...")
```

✅ **Isso já funciona!** Você recebe os chunks mais relevantes da legislação brasileira, com score de relevância e referência da fonte.

---

## Nível 2: Passando para seu LLM

**Quer usar o contexto com seu próprio LLM?** Use `to_messages()`:

```python
from vectorgov import VectorGov
from openai import OpenAI

vg = VectorGov(api_key="vg_xxx")
openai = OpenAI()

results = vg.search("O que é ETP?")

# Converte para formato de mensagens (funciona com OpenAI, Claude, Gemini)
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=results.to_messages("O que é ETP?")
)

print(response.choices[0].message.content)
```

✅ Agora você tem RAG funcionando com qualquer LLM de sua escolha.

---

## Nível 3: Melhorando o Sistema com Feedback

**Quer ajudar a melhorar os resultados?** Envie feedback:

```python
results = vg.search("O que é ETP?")

# ... usa os resultados ...

# Feedback positivo
vg.feedback(results.query_id, like=True)

# Ou negativo
vg.feedback(results.query_id, like=False)
```

Se estiver usando LLM externo, salve a resposta primeiro:

```python
# Gera resposta com seu LLM
answer = openai.chat.completions.create(...).choices[0].message.content

# Salva no VectorGov para habilitar feedback
stored = vg.store_response(
    query="O que é ETP?",
    answer=answer,
    provider="OpenAI",
    model="gpt-4o"
)

# Agora pode enviar feedback
vg.feedback(stored.query_hash, like=True)
```

✅ Seu feedback melhora o sistema para todos.

---

## Nível 4: Refinando com Filtros

**Quer buscar em documentos específicos?** Use filtros:

```python
# Apenas leis
results = vg.search("licitação", filters={"tipo": "lei"})

# Apenas de 2021
results = vg.search("pregão", filters={"ano": 2021})

# Múltiplos filtros
results = vg.search("contratação direta", filters={
    "tipo": "in",
    "ano": 2022,
    "orgao": "seges"
})
```

✅ Resultados mais precisos para seu caso de uso.

---

## Nível 5: Controlando Performance com Modos

**Precisa de mais velocidade ou precisão?** Escolha o modo:

```python
# Rápido: chatbots, alta escala (~2s)
results = vg.search("query", mode="fast")

# Balanceado: uso geral (~5s) - DEFAULT
results = vg.search("query", mode="balanced")

# Preciso: análises críticas (~15s)
results = vg.search("query", mode="precise")

# Com cache para queries genéricas (trade-off: privacidade)
results = vg.search("query", mode="fast", use_cache=True)
```

✅ Otimize para seu caso: latência vs precisão vs custo.

---

## Nível 6: Controlando Custos com Prompts

**Quer economizar tokens no LLM?** Personalize o prompt:

```python
# Prompt mínimo (~15 tokens) - economia máxima
results = vg.search("O que é ETP?")
messages = results.to_messages(
    "O que é ETP?",
    system_prompt="Responda usando o contexto. Cite fontes."
)

# Ou use prompts pré-definidos
messages = results.to_messages(
    "O que é ETP?",
    system_prompt=vg.get_system_prompt("concise")  # ~40 tokens
)

# Ver opções disponíveis
print(vg.available_prompts)  # ['default', 'concise', 'detailed', 'chatbot']
```

✅ Economia de até 80 tokens por requisição = ~$0.80/10.000 req no GPT-4o.

---

## Nível 7: Rastreabilidade e Auditoria

**Precisa monitorar o uso?** Acesse os logs de auditoria:

```python
# Logs dos últimos 7 dias
logs = vg.get_audit_logs(days=7)

for log in logs.logs:
    print(f"[{log.severity}] {log.event_type}")

# Estatísticas agregadas
stats = vg.get_audit_stats(days=30)
print(f"Total: {stats.total_events} eventos")
print(f"Bloqueados: {stats.blocked_count}")
```

✅ Visibilidade completa sobre o uso e segurança.

---

## Nível 8: Integrações Avançadas

**Quer usar com frameworks de agentes?** Escolha sua integração:

### LangChain
```python
from vectorgov.integrations.langchain import VectorGovRetriever
retriever = VectorGovRetriever(api_key="vg_xxx")
```

### LangGraph
```python
from vectorgov.integrations.langgraph import create_vectorgov_tool
tool = create_vectorgov_tool(api_key="vg_xxx")
```

### Function Calling
```python
# OpenAI
tools = [vg.to_openai_tool()]

# Anthropic
tools = [vg.to_anthropic_tool()]

# Google
tools = [vg.to_google_tool()]
```

### MCP (Claude Desktop, Cursor)
```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "vectorgov-mcp",
            "env": {"VECTORGOV_API_KEY": "vg_xxx"}
        }
    }
}
```

✅ VectorGov se integra com qualquer stack de IA.

---

## 🎯 Exemplo Completo: Tudo Junto

Aqui está um exemplo de **produção real** que usa todas as features em um único fluxo:

```python
"""
Aplicação RAG Completa com VectorGov
Inclui: filtros, modos, prompts, feedback, auditoria
"""

from vectorgov import VectorGov, VectorGovError, RateLimitError
from openai import OpenAI
import time

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

vg = VectorGov(
    api_key="vg_xxx",
    timeout=60,
    default_top_k=5,
)
openai_client = OpenAI()

# =============================================================================
# FUNÇÃO PRINCIPAL RAG
# =============================================================================

def responder_pergunta(
    query: str,
    filtros: dict = None,
    modo: str = "balanced",
    prompt_tipo: str = "default",
    usar_cache: bool = False,
) -> dict:
    """
    Fluxo RAG completo com todas as features.

    Args:
        query: Pergunta do usuário
        filtros: Filtros de busca (tipo, ano, orgao)
        modo: fast, balanced ou precise
        prompt_tipo: default, concise, detailed, chatbot
        usar_cache: Se deve usar cache compartilhado

    Returns:
        dict com answer, sources, query_hash, latency
    """
    start_time = time.time()

    try:
        # -----------------------------------------------------------------
        # 1. BUSCA COM FILTROS E MODO
        # -----------------------------------------------------------------
        results = vg.search(
            query,
            mode=modo,
            filters=filtros,
            use_cache=usar_cache,
        )

        if not results.hits:
            return {
                "answer": "Não encontrei informações relevantes para sua pergunta.",
                "sources": [],
                "query_hash": None,
                "latency_ms": (time.time() - start_time) * 1000,
            }

        # -----------------------------------------------------------------
        # 2. MONTA PROMPT COM CONTROLE DE TOKENS
        # -----------------------------------------------------------------
        system_prompt = vg.get_system_prompt(prompt_tipo)
        messages = results.to_messages(query, system_prompt=system_prompt)

        # -----------------------------------------------------------------
        # 3. GERA RESPOSTA COM LLM
        # -----------------------------------------------------------------
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Mais barato para alto volume
            messages=messages,
            temperature=0.1,  # Mais determinístico para respostas jurídicas
        )
        answer = response.choices[0].message.content

        # -----------------------------------------------------------------
        # 4. SALVA RESPOSTA PARA HABILITAR FEEDBACK
        # -----------------------------------------------------------------
        stored = vg.store_response(
            query=query,
            answer=answer,
            provider="OpenAI",
            model="gpt-4o-mini",
            chunks_used=len(results.hits),
        )

        # -----------------------------------------------------------------
        # 5. RETORNA RESULTADO ESTRUTURADO
        # -----------------------------------------------------------------
        return {
            "answer": answer,
            "sources": [hit.source for hit in results.hits],
            "query_hash": stored.query_hash,  # Para feedback posterior
            "latency_ms": (time.time() - start_time) * 1000,
            "cached": results.cached,
            "mode": modo,
        }

    except RateLimitError as e:
        return {
            "error": f"Rate limit. Tente novamente em {e.retry_after}s",
            "retry_after": e.retry_after,
        }

    except VectorGovError as e:
        return {
            "error": f"Erro VectorGov: {e.message}",
        }

# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Pergunta simples
    resultado = responder_pergunta("O que é ETP?")
    print(f"Resposta: {resultado['answer'][:200]}...")
    print(f"Fontes: {resultado['sources']}")
    print(f"Latência: {resultado['latency_ms']:.0f}ms")

    # Pergunta com filtros e modo preciso
    resultado = responder_pergunta(
        query="Quando o ETP pode ser dispensado?",
        filtros={"tipo": "in", "ano": 2022},
        modo="precise",
        prompt_tipo="detailed",
    )

    # Enviar feedback (após usuário avaliar)
    if resultado.get("query_hash"):
        vg.feedback(resultado["query_hash"], like=True)
        print("Feedback enviado!")

    # Verificar logs de auditoria
    stats = vg.get_audit_stats(days=7)
    print(f"\nEstatísticas da semana:")
    print(f"  Total de eventos: {stats.total_events}")
    print(f"  Bloqueados: {stats.blocked_count}")
```

### O que esse exemplo demonstra:

| Feature | Linha | Descrição |
|---------|-------|-----------|
| **Busca básica** | `vg.search()` | O mínimo necessário |
| **Modos** | `mode="balanced"` | Controle de latência/precisão |
| **Filtros** | `filters={...}` | Refinamento de busca |
| **Cache** | `use_cache=False` | Trade-off privacidade/velocidade |
| **Prompts** | `vg.get_system_prompt()` | Controle de tokens/custos |
| **to_messages()** | `results.to_messages()` | Integração com qualquer LLM |
| **store_response()** | `vg.store_response()` | Habilita feedback para LLM externo |
| **Feedback** | `vg.feedback()` | Melhora o sistema |
| **Auditoria** | `vg.get_audit_stats()` | Rastreabilidade |
| **Tratamento de erros** | `try/except` | Robustez em produção |

---

## 📊 Resumo: Qual Feature Usar Quando?

| Necessidade | Feature | Exemplo |
|-------------|---------|---------|
| Buscar legislação | `search()` | `vg.search("query")` |
| Busca + grafo de citações | `hybrid()` | `vg.hybrid("query", hops=2)` |
| Busca sem configuração | `smart_search()` | `vg.smart_search("query")` |
| Buscar artigo específico | `lookup()` | `vg.lookup("Art. 75 da Lei 14.133")` |
| Usar com LLM | `to_messages()` | `results.to_messages(query)` |
| Melhorar resultados | `feedback()` | `vg.feedback(query_id, like=True)` |
| Busca específica | `filters` | `filters={"tipo": "lei"}` |
| Mais velocidade | `mode="fast"` | Chatbots, alto volume |
| Mais precisão | `mode="precise"` | Análises críticas |
| Economia de tokens | `system_prompt` | Prompt personalizado |
| LLM externo + feedback | `store_response()` | Salva resposta para feedback |
| Monitoramento | `get_audit_logs()` | Logs de segurança |
| Agentes IA | `to_openai_tool()` | Function calling |
| Claude Desktop | MCP Server | `vectorgov-mcp` |

---

> **Dica:** Comece simples com `search()` e vá adicionando features conforme sua aplicação evolui. Não precisa usar tudo desde o início!
