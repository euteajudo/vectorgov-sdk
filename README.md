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

O VectorGov foi projetado para você usar o LLM de sua preferência. Instale a biblioteca do provedor desejado:

```bash
# OpenAI
pip install openai

# Google Gemini
pip install google-generativeai

# Anthropic Claude
pip install anthropic
```

### OpenAI

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

## Integração com LangChain

Instale as dependências:

```bash
pip install 'vectorgov[langchain]'
# ou
pip install vectorgov langchain langchain-core
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

## Integração com LangGraph

LangGraph é o framework da LangChain para construir agentes com estado. O VectorGov integra nativamente.

### Instalação

```bash
pip install 'vectorgov[langgraph]'
# ou
pip install vectorgov langgraph langchain-openai
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

## Integração com Google ADK

O Google ADK (Agent Development Kit) é o framework do Google para construir agentes de IA.

### Instalação

```bash
pip install 'vectorgov[google-adk]'
# ou
pip install vectorgov google-adk
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

### Agente Customizado

```python
from vectorgov.integrations.google_adk import create_search_tool
from google.adk.agents import Agent

search = create_search_tool(
    api_key="vg_xxx",
    top_k=10,
    mode="precise",
)

agent = Agent(
    name="licitacao_expert",
    model="gemini-2.0-flash",
    instruction="""Você é um especialista em licitações públicas.
Consulte sempre a legislação antes de responder.
Cite artigos específicos nas suas respostas.""",
    tools=[search],
)

response = agent.run("Como funciona o sistema de registro de preços?")
print(response)
```

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

### Exemplo de Uso no Claude

Após configurar o servidor, você pode perguntar ao Claude:

> "Quais os critérios de julgamento previstos na Lei 14.133?"

O Claude automaticamente usará a ferramenta `search_legislation` para buscar a informação na base VectorGov.

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
