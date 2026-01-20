"""
Exemplo 14: Contagem de Tokens

Este exemplo demonstra como estimar o número de tokens que serão enviados
para o LLM, útil para:
- Estimar custos de API
- Verificar se o contexto cabe na janela de contexto do modelo
- Otimizar o número de resultados retornados

A contagem de tokens é feita no servidor VectorGov usando tiktoken,
garantindo precisão sem necessidade de dependências extras no cliente.

Requisitos:
    pip install vectorgov
"""

import os
from vectorgov import VectorGov, TokenStats

# Configuração
api_key = os.getenv("VECTORGOV_API_KEY", "vg_sua_chave")
vg = VectorGov(api_key=api_key)

# =============================================================================
# EXEMPLO 1: Estimar tokens de um SearchResult
# =============================================================================

print("=" * 60)
print("EXEMPLO 1: Estimar tokens de um SearchResult")
print("=" * 60)

results = vg.search("O que é ETP?", top_k=5)

# Estima tokens que serão usados no to_messages()
stats = vg.estimate_tokens(results)

print(f"Query: {results.query}")
print(f"Hits retornados: {stats.hits_count}")
print(f"Caracteres: {stats.char_count:,}")
print(f"Tokens do contexto: {stats.context_tokens:,}")
print(f"Tokens do system prompt: {stats.system_tokens:,}")
print(f"Tokens da query: {stats.query_tokens:,}")
print(f"Tokens total: {stats.total_tokens:,}")
print(f"Encoding: {stats.encoding}")

# Verificar se cabe na janela de contexto
MODEL_LIMITS = {
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
    "gpt-3.5-turbo": 16_385,
    "claude-sonnet-4": 200_000,
    "gemini-2.0-flash": 1_000_000,
}

print("\nCompatibilidade com modelos:")
for model, limit in MODEL_LIMITS.items():
    status = "✓ OK" if stats.total_tokens < limit else "✗ EXCEDE"
    print(f"  {model}: {status} ({stats.total_tokens:,}/{limit:,})")


# =============================================================================
# EXEMPLO 2: Estimar tokens de um texto simples
# =============================================================================

print("\n" + "=" * 60)
print("EXEMPLO 2: Estimar tokens de um texto simples")
print("=" * 60)

texto = """
O Estudo Técnico Preliminar (ETP) é um documento constitutivo da primeira
etapa do planejamento de uma contratação pública. Ele deve conter a descrição
da necessidade da contratação, fundamentada em estudo técnico.
"""

stats = vg.estimate_tokens(texto)
print(f"Texto: {texto[:100]}...")
print(f"Caracteres: {stats.char_count:,}")
print(f"Tokens: {stats.total_tokens:,}")


# =============================================================================
# EXEMPLO 3: Estimar tokens com system prompt customizado
# =============================================================================

print("\n" + "=" * 60)
print("EXEMPLO 3: Com system prompt customizado")
print("=" * 60)

# System prompt mais detalhado
custom_prompt = vg.get_system_prompt("detailed")

stats = vg.estimate_tokens(results, system_prompt=custom_prompt)
print(f"Com system prompt 'detailed':")
print(f"  Tokens do system: {stats.system_tokens:,}")
print(f"  Tokens do contexto: {stats.context_tokens:,}")
print(f"  Total: {stats.total_tokens:,}")

# Comparar com prompt padrão
stats_default = vg.estimate_tokens(results)
print(f"\nCom system prompt padrão:")
print(f"  Tokens do system: {stats_default.system_tokens:,}")
print(f"  Total: {stats_default.total_tokens:,}")

print(f"\nDiferença: +{stats.total_tokens - stats_default.total_tokens} tokens")


# =============================================================================
# EXEMPLO 4: Otimizando para caber em um limite
# =============================================================================

print("\n" + "=" * 60)
print("EXEMPLO 4: Otimizando para limite de tokens")
print("=" * 60)

# Supondo limite de 4000 tokens para o contexto
MAX_CONTEXT_TOKENS = 4000

# Buscar mais resultados
results_full = vg.search("O que é ETP?", top_k=10)
stats = vg.estimate_tokens(results_full)
print(f"Com {stats.hits_count} hits: {stats.total_tokens:,} tokens")

if stats.total_tokens > MAX_CONTEXT_TOKENS:
    print(f"Excede limite de {MAX_CONTEXT_TOKENS:,}. Reduzindo...")

    # Estratégia: buscar menos resultados
    for k in range(10, 0, -1):
        results_reduced = vg.search("O que é ETP?", top_k=k)
        stats = vg.estimate_tokens(results_reduced)
        if stats.total_tokens <= MAX_CONTEXT_TOKENS:
            print(f"Com top_k={k}: {stats.total_tokens:,} tokens ✓")
            break
    else:
        print("Não foi possível reduzir para o limite")


# =============================================================================
# EXEMPLO 5: Estimativa de custo por query
# =============================================================================

print("\n" + "=" * 60)
print("EXEMPLO 5: Estimativa de custo")
print("=" * 60)

# Preços por 1M tokens (janeiro 2025 - verificar preços atuais)
PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}

stats = vg.estimate_tokens(results)
estimated_output = 500  # Tokens de resposta esperados

print(f"Input tokens: {stats.total_tokens:,}")
print(f"Output tokens (estimado): {estimated_output:,}")
print(f"\nCusto estimado por query:")

for model, prices in PRICES.items():
    input_cost = (stats.total_tokens / 1_000_000) * prices["input"]
    output_cost = (estimated_output / 1_000_000) * prices["output"]
    total_cost = input_cost + output_cost
    print(f"  {model}: ${total_cost:.6f} (input: ${input_cost:.6f}, output: ${output_cost:.6f})")


# =============================================================================
# EXEMPLO 6: Uso com OpenAI
# =============================================================================

print("\n" + "=" * 60)
print("EXEMPLO 6: Verificar antes de enviar ao OpenAI")
print("=" * 60)

# Simula verificação antes de enviar
GPT4O_LIMIT = 128_000

stats = vg.estimate_tokens(results)
print(f"Tokens a enviar: {stats.total_tokens:,}")

if stats.total_tokens < GPT4O_LIMIT:
    print("✓ Seguro para enviar ao GPT-4o")

    # Exemplo de como seria o envio:
    # messages = results.to_messages("Explique o que é ETP")
    # response = openai.chat.completions.create(
    #     model="gpt-4o",
    #     messages=messages
    # )
else:
    print(f"✗ Excede limite do GPT-4o ({GPT4O_LIMIT:,} tokens)")
    print("  Considere reduzir top_k ou usar max_chars no to_context()")


print("\n" + "=" * 60)
print("FIM DOS EXEMPLOS")
print("=" * 60)
