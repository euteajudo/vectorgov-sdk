"""
Exemplo 16: Smart Search (Busca Completa com Análise Jurídica)

Pipeline inteligente de 3 estágios com análise de completude.
Retorna análise de completude, raciocínio jurídico e nível de confiança.
Ideal para perguntas complexas que envolvem múltiplas normas.

Requer plano Premium.
"""

import os
from vectorgov import VectorGov

API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_sua_chave_aqui")


def main():
    vg = VectorGov(api_key=API_KEY)

    query = "Quais são as hipóteses de dispensa de licitação por valor?"
    print(f"Smart Search: {query}\n")

    result = vg.smart_search(query)

    # --- Raciocínio jurídico do Juiz ---
    print("=== ANÁLISE JURÍDICA ===")
    print(f"Confiança: {result.confianca}")  # ALTO | MEDIO | BAIXO
    print(f"Normas presentes: {', '.join(result.normas_presentes)}")
    print(f"Tentativas: {result.tentativas}")
    print(f"Latência: {result.latency_ms}ms")
    print(f"\nRaciocínio:\n{result.raciocinio[:500]}...")

    # --- Dispositivos encontrados ---
    print(f"\n=== DISPOSITIVOS ({result.total} resultados) ===")
    for i, hit in enumerate(result, 1):
        print(f"[{i}] {hit.source}")
        print(f"    {hit.text[:150]}...")

    # --- Usar com LLM externo ---
    print("\n=== CONTEXTO PARA LLM ===")
    context = result.to_context()
    print(context[:300] + "...")

    # Exemplo com OpenAI:
    # messages = result.to_messages(query, system_prompt="Responda em português.")
    # response = openai.chat.completions.create(model="gpt-4o", messages=messages)


if __name__ == "__main__":
    main()
