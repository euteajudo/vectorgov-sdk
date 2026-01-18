# VectorGov SDK

SDK Python para acessar bases de conhecimento jurídico VectorGov.

Acesse informações de leis, decretos e instruções normativas brasileiras com 3 linhas de código.

[![PyPI version](https://badge.fury.io/py/vectorgov.svg)](https://badge.fury.io/py/vectorgov)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
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
- [Streaming (Tempo Real)](#streaming-tempo-real)
- **Modelos Comerciais (APIs Pagas)**
  - [OpenAI (GPT-4)](#openai)
  - [Google Gemini](#google-gemini)
  - [Anthropic Claude](#anthropic-claude)
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
  - [Filtros](#filtros)
  - [Formatação de Resultados](#formatação-de-resultados)
  - [System Prompts](#system-prompts-customizados)
  - [Feedback](#feedback)
  - [Tratamento de Erros](#tratamento-de-erros)
- **Gerenciamento de Documentos**
  - [Permissoes](#permissões)
  - [Listar e Consultar](#listar-e-consultar-documentos)
  - [Upload e Ingestao (Admin)](#upload-e-ingestão-admin)
  - [Enriquecimento (Admin)](#enriquecimento-admin)
  - [Exclusao (Admin)](#exclusão-admin)
- **Documentação para LLMs**
  - [llms.txt](#llmstxt)
  - [CLAUDE.md](#claudemd)
- [Obter sua API Key](#obter-sua-api-key)

---

## Instalação

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

# Conectar à API
vg = VectorGov(api_key="vg_sua_chave_aqui")

# Buscar informações
results = vg.search("Quando o ETP pode ser dispensado?")

# Ver resultados
for hit in results:
    print(f"{hit.source}: {hit.text}")
```

> **Nota:** O SDK retorna o **texto completo** de cada chunk em `hit.text`. Não há limite de caracteres - você recebe todo o conteúdo do artigo/parágrafo/inciso recuperado.

---

## Streaming (Tempo Real)

Obtenha respostas em tempo real com o método `ask_stream()`. Ideal para interfaces de chat interativas.

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

for chunk in vg.ask_stream("O que é ETP?"):
    if chunk.type == "token":
        # Exibe cada token conforme é gerado
        print(chunk.content, end="", flush=True)
    elif chunk.type == "retrieval":
        # Notificação de busca concluída
        print(f"[Recuperados {chunk.chunks} documentos em {chunk.time_ms}ms]")
    elif chunk.type == "complete":
        # Resposta completa com citações
        print(f"\n\n📚 Fontes: {len(chunk.citations)} citações")
```

### Tipos de Eventos

| Evento | Descrição | Campos |
|--------|-----------|--------|
| `start` | Início do processamento | `query` |
| `retrieval` | Busca concluída | `chunks`, `time_ms` |
| `token` | Token da resposta | `content` |
| `complete` | Resposta finalizada | `citations`, `query_hash` |
| `error` | Erro no processamento | `message` |

### Exemplo com Interface

```python
import sys

for chunk in vg.ask_stream("Quando o ETP pode ser dispensado?"):
    if chunk.type == "start":
        print("🔍 Buscando...", file=sys.stderr)
    elif chunk.type == "retrieval":
        print(f"📄 {chunk.chunks} documentos encontrados", file=sys.stderr)
    elif chunk.type == "token":
        print(chunk.content, end="", flush=True)
    elif chunk.type == "complete":
        print(f"\n\n---\n📚 {len(chunk.citations)} citações", file=sys.stderr)
    elif chunk.type == "error":
        print(f"❌ Erro: {chunk.message}", file=sys.stderr)
        break
```

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
- Documentação de todos os métodos (`search`, `ask`, `feedback`, `store_response`)
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

---

# 📁 Gerenciamento de Documentos

O SDK permite gerenciar documentos na base de conhecimento. Algumas operações são restritas a **administradores**.

## Permissões

| Operação | Permissão | Método |
|----------|-----------|--------|
| Listar documentos | Todos | `list_documents()` |
| Ver detalhes | Todos | `get_document(id)` |
| Ver status ingestão | Todos | `get_ingest_status(task_id)` |
| Ver status enriquecimento | Todos | `get_enrichment_status(task_id)` |
| **Upload de PDF** | **Admin** | `upload_pdf()` |
| **Iniciar enriquecimento** | **Admin** | `start_enrichment()` |
| **Excluir documento** | **Admin** | `delete_document()` |

> **Nota:** Para obter permissões de administrador, entre em contato com o suporte.

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

> **Requer permissão de administrador**

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_admin_xxx")  # API key com permissão admin

# Upload de PDF
with open("lei_exemplo.pdf", "rb") as f:
    result = vg.upload_pdf(
        file=f,
        tipo_documento="LEI",
        numero="99999",
        ano=2024,
        titulo="Lei de Exemplo",
        descricao="Descrição opcional"
    )

print(f"Upload: {result.message}")
print(f"Document ID: {result.document_id}")
print(f"Task ID: {result.task_id}")

# Acompanhar status da ingestão
status = vg.get_ingest_status(result.task_id)
print(f"Status: {status.status}")  # pending, processing, completed, failed
print(f"Progresso: {status.progress}%")
print(f"Chunks criados: {status.chunks_created}")
```

### Polling de Status

```python
import time

task_id = result.task_id

while True:
    status = vg.get_ingest_status(task_id)
    print(f"Status: {status.status} ({status.progress}%)")
    
    if status.status in ("completed", "failed"):
        break
    
    time.sleep(5)  # Aguarda 5 segundos

if status.status == "completed":
    print(f"Ingestão concluída! {status.chunks_created} chunks criados")
else:
    print(f"Erro: {status.message}")
```

## Enriquecimento (Admin)

> **Requer permissão de administrador**

O enriquecimento adiciona contexto semântico aos chunks (resumos, perguntas sintéticas, etc.), melhorando a qualidade da busca.

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_admin_xxx")

# Iniciar enriquecimento de um documento
result = vg.start_enrichment("LEI-14133-2021")
print(f"Task ID: {result.task_id}")

# Acompanhar progresso
status = vg.get_enrichment_status(result.task_id)
print(f"Status: {status.status}")
print(f"Progresso: {status.progress:.0%}")
print(f"Chunks enriquecidos: {status.chunks_enriched}")
print(f"Chunks pendentes: {status.chunks_pending}")
print(f"Erros: {status.chunks_failed}")

# Polling até concluir
import time

while status.status not in ("completed", "error"):
    time.sleep(10)
    status = vg.get_enrichment_status(result.task_id)
    print(f"Progresso: {status.progress:.0%} ({status.chunks_enriched}/{status.chunks_enriched + status.chunks_pending})")

print("Enriquecimento concluído!")
```

## Exclusão (Admin)

> **Requer permissão de administrador**

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_admin_xxx")

# Excluir documento
result = vg.delete_document("LEI-99999-2024")

if result.success:
    print(f"Documento excluído: {result.message}")
else:
    print(f"Erro: {result.message}")
```

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

### IngestStatus

```python
@dataclass
class IngestStatus:
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int         # 0 a 100
    message: str
    document_id: str      # Disponível após conclusão
    chunks_created: int
```

### EnrichStatus

```python
@dataclass
class EnrichStatus:
    task_id: str
    status: Literal["pending", "processing", "completed", "error", "not_found"]
    progress: float       # 0.0 a 1.0
    chunks_enriched: int
    chunks_pending: int
    chunks_failed: int
    errors: list[str]     # Lista de erros, se houver
```
