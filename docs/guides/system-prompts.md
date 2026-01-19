# System Prompts - Guia Completo

> **Controle total sobre como o LLM responde suas perguntas**

O VectorGov SDK oferece prompts pré-definidos otimizados para diferentes casos de uso, mas você também pode criar seus próprios prompts personalizados para ter controle total sobre tokens e custos.

---

## Como Funciona

Quando você usa `to_messages()`, o SDK combina:

1. **System Prompt** → Instruções para o LLM (você controla)
2. **Contexto** → Documentos relevantes da busca (VectorGov fornece)
3. **Pergunta do usuário** → Sua query

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPOSIÇÃO DA MENSAGEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  System Prompt (você escolhe)     ~50-130 tokens                │
│  ────────────────────────────────────────────────               │
│  "Você é um assistente especializado..."                        │
│                                                                 │
│  +                                                              │
│                                                                 │
│  Contexto (VectorGov)             ~500-2000 tokens              │
│  ────────────────────────────────────────────────               │
│  "Art. 5º O estudo técnico preliminar..."                       │
│  "Art. 14 O ETP poderá ser dispensado..."                       │
│                                                                 │
│  +                                                              │
│                                                                 │
│  Pergunta do usuário              ~10-50 tokens                 │
│  ────────────────────────────────────────────────               │
│  "O que é ETP e quando pode ser dispensado?"                    │
│                                                                 │
│  =                                                              │
│                                                                 │
│  TOTAL INPUT                      ~560-2180 tokens              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prompts Pré-definidos

O SDK inclui 4 prompts otimizados. Use `vg.available_prompts` para listar e `vg.get_system_prompt("nome")` para obter o conteúdo.

### 1. `default` - Uso Geral

**Tokens:** ~95 tokens | **Caracteres:** 340

```text
Você é um assistente especializado em legislação brasileira, especialmente em licitações e contratos públicos.

Instruções:
1. Use APENAS as informações do contexto fornecido para responder
2. Se a informação não estiver no contexto, diga que não encontrou
3. Sempre cite as fontes usando o formato [Fonte: Lei X, Art. Y]
4. Seja objetivo e direto nas respostas
5. Use linguagem formal adequada ao contexto jurídico
```

**Quando usar:** Consultas gerais, documentação, relatórios internos.

---

### 2. `concise` - Respostas Curtas

**Tokens:** ~40 tokens | **Caracteres:** 130

```text
Você é um assistente jurídico. Responda de forma concisa e direta usando apenas o contexto fornecido. Cite as fontes.
```

**Quando usar:** Chatbots, respostas rápidas, alto volume de requisições.

**Economia:** ~55 tokens a menos que `default` por requisição.

---

### 3. `detailed` - Análises Completas

**Tokens:** ~120 tokens | **Caracteres:** 430

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

**Quando usar:** Pareceres, análises jurídicas, due diligence.

**Custo extra:** ~25 tokens a mais que `default`.

---

### 4. `chatbot` - Linguagem Acessível

**Tokens:** ~60 tokens | **Caracteres:** 200

```text
Você é um assistente virtual amigável especializado em licitações públicas.
Responda de forma clara e acessível, evitando jargão excessivo.
Baseie suas respostas apenas no contexto fornecido e cite as fontes.
```

**Quando usar:** Atendimento ao público, portais de transparência, FAQs.

---

## Comparativo de Tokens

| Prompt | Tokens | vs Default | Melhor Para |
|--------|--------|------------|-------------|
| `concise` | ~40 | -55 tokens | Chatbots, alto volume |
| `chatbot` | ~60 | -35 tokens | Atendimento público |
| `default` | ~95 | baseline | Uso geral |
| `detailed` | ~120 | +25 tokens | Análises jurídicas |

---

## Impacto no Custo por LLM

### Custo do System Prompt (apenas)

Considerando preços de Janeiro/2025:

| LLM | Preço Input | `concise` | `default` | `detailed` |
|-----|-------------|-----------|-----------|------------|
| **GPT-4o** | $2.50/1M | $0.0001 | $0.00024 | $0.0003 |
| **GPT-4o-mini** | $0.15/1M | $0.000006 | $0.000014 | $0.000018 |
| **Claude Sonnet** | $3.00/1M | $0.00012 | $0.000285 | $0.00036 |
| **Gemini 1.5 Flash** | $0.075/1M | $0.000003 | $0.0000071 | $0.000009 |

### Custo Total Estimado por Requisição

Considerando: System Prompt + Contexto (~1000 tokens) + Pergunta (~30 tokens) + Resposta (~500 tokens output)

| LLM | `concise` | `default` | `detailed` | Economia concise→detailed |
|-----|-----------|-----------|------------|---------------------------|
| **GPT-4o** | $0.0077 | $0.0078 | $0.0079 | ~$0.20/1000 req |
| **GPT-4o-mini** | $0.00046 | $0.00047 | $0.00048 | ~$0.02/1000 req |
| **Claude Sonnet** | $0.0107 | $0.0108 | $0.0109 | ~$0.20/1000 req |
| **Gemini 1.5 Flash** | $0.00023 | $0.00023 | $0.00024 | ~$0.01/1000 req |

> **Conclusão:** O system prompt representa ~5-10% do custo total. O maior impacto vem do **contexto** (chunks retornados) e da **resposta gerada**.

---

## Estimativa de Custos em Escala

### 10.000 requisições/mês

| LLM | Prompt `concise` | Prompt `detailed` |
|-----|------------------|-------------------|
| GPT-4o | ~$77/mês | ~$79/mês |
| GPT-4o-mini | ~$4.60/mês | ~$4.80/mês |
| Claude Sonnet | ~$107/mês | ~$109/mês |
| Gemini 1.5 Flash | ~$2.30/mês | ~$2.40/mês |

### 100.000 requisições/mês

| LLM | Prompt `concise` | Prompt `detailed` |
|-----|------------------|-------------------|
| GPT-4o | ~$770/mês | ~$790/mês |
| GPT-4o-mini | ~$46/mês | ~$48/mês |
| Claude Sonnet | ~$1,070/mês | ~$1,090/mês |
| Gemini 1.5 Flash | ~$23/mês | ~$24/mês |

---

## Criando Prompts Personalizados

Você tem **controle total** para criar seus próprios prompts:

### Exemplo: Prompt Minimalista (economia máxima)

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")
results = vg.search("O que é ETP?")

# Prompt ultra-curto (~15 tokens)
meu_prompt = "Responda usando apenas o contexto. Cite fontes."

messages = results.to_messages(
    query="O que é ETP?",
    system_prompt=meu_prompt
)

# Use com seu LLM
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
)
```

**Economia:** ~80 tokens a menos que `default` = **~$0.80/10.000 requisições** no GPT-4o.

---

### Exemplo: Prompt para Domínio Específico

```python
# Prompt especializado em pregões (~100 tokens)
prompt_pregao = """Você é um pregoeiro experiente.

Regras:
1. Responda apenas sobre pregão eletrônico e presencial
2. Cite artigos da Lei 14.133/2021 e Lei 10.520/2002
3. Se a pergunta não for sobre pregão, diga que não pode ajudar
4. Formato: resposta direta + citação legal"""

messages = results.to_messages(
    query="Qual o prazo para impugnação no pregão?",
    system_prompt=prompt_pregao
)
```

---

### Exemplo: Prompt Bilíngue

```python
# Para sistemas que precisam responder em inglês
prompt_en = """You are a legal assistant specialized in Brazilian public procurement law.

Instructions:
1. Answer in English
2. Use only the provided context
3. Cite sources as [Law X, Art. Y]
4. Explain Brazilian legal terms when needed"""

messages = results.to_messages(
    query="What is ETP in Brazilian procurement?",
    system_prompt=prompt_en
)
```

---

## Dicas para Otimizar Custos

### 1. Escolha o Prompt Certo

| Cenário | Prompt Recomendado |
|---------|-------------------|
| Chatbot de alto volume | `concise` ou personalizado mínimo |
| Portal de transparência | `chatbot` |
| Uso interno | `default` |
| Parecer jurídico | `detailed` |

### 2. Reduza o Contexto (top_k)

```python
# Menos chunks = menos tokens = menor custo
results = vg.search("query", top_k=3)  # ao invés de 5
```

| top_k | Tokens contexto (aprox) | Redução |
|-------|------------------------|---------|
| 5 | ~1500 tokens | baseline |
| 3 | ~900 tokens | -40% |
| 2 | ~600 tokens | -60% |

### 3. Use Modelos Mais Baratos para Casos Simples

```python
# Perguntas simples → GPT-4o-mini ou Gemini Flash
if is_simple_query(query):
    model = "gpt-4o-mini"  # 17x mais barato que GPT-4o
else:
    model = "gpt-4o"
```

### 4. Monitore Tokens Consumidos

```python
import tiktoken

def count_tokens(messages, model="gpt-4o"):
    enc = tiktoken.encoding_for_model(model)
    return sum(len(enc.encode(m["content"])) for m in messages)

messages = results.to_messages("O que é ETP?")
tokens = count_tokens(messages)
print(f"Esta requisição consumirá ~{tokens} tokens de input")
```

---

## Referência Rápida

```python
from vectorgov import VectorGov

vg = VectorGov(api_key="vg_xxx")

# Ver prompts disponíveis
print(vg.available_prompts)
# ['default', 'concise', 'detailed', 'chatbot']

# Ver conteúdo de um prompt
print(vg.get_system_prompt("concise"))

# Usar prompt pré-definido
messages = results.to_messages(
    query="...",
    system_prompt=vg.get_system_prompt("detailed")
)

# Usar prompt personalizado
messages = results.to_messages(
    query="...",
    system_prompt="Seu prompt aqui..."
)

# Sem system prompt (só contexto + pergunta)
messages = results.to_messages(
    query="...",
    system_prompt=""
)
```

---

## FAQ

### O VectorGov cobra pelos tokens do prompt?

**Não.** O VectorGov cobra apenas pela **busca semântica**. Os tokens do prompt são processados pelo **seu LLM** (OpenAI, Gemini, Claude), e você paga diretamente para eles.

### Posso usar o VectorGov sem system prompt?

**Sim.** Passe `system_prompt=""` e o LLM receberá apenas o contexto e a pergunta. Útil quando você já tem instruções no nível da aplicação.

### Qual o tamanho máximo do prompt personalizado?

**Não há limite no SDK.** O limite é do seu LLM (geralmente 4K-128K tokens de contexto total).

### O prompt afeta a qualidade da resposta?

**Sim, significativamente.** Prompts mais detalhados geralmente produzem respostas melhores, mas com custo maior. Teste diferentes prompts para encontrar o equilíbrio ideal para seu caso de uso.

---

## Próximos Passos

- [Modos de Busca](./search-modes.md) - Controle latência vs precisão
- [Integração com LLMs](./llm-integration.md) - Exemplos completos
- [Referência da API](../api/client.md) - Documentação técnica
