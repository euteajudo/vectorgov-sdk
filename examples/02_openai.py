"""
Exemplo 2: Integração com OpenAI

Este exemplo mostra como usar o VectorGov com GPT-4.

Requisitos:
    pip install vectorgov openai
"""

import os
from vectorgov import VectorGov
from openai import OpenAI

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def main():
    # Inicializar clientes
    vg = VectorGov(api_key=VECTORGOV_KEY)
    openai = OpenAI(api_key=OPENAI_KEY)

    # Pergunta do usuário
    query = "Quais são os critérios de julgamento em uma licitação?"

    print(f"Pergunta: {query}")
    print("\n[1/2] Buscando contexto no VectorGov...")

    # Buscar contexto relevante
    results = vg.search(query, mode="balanced", top_k=5)

    print(f"      Encontrados {results.total} resultados em {results.latency_ms}ms")
    print("\n[2/2] Gerando resposta com GPT-4...")

    # Gerar resposta com OpenAI
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=results.to_messages(query),
        temperature=0.3,
        max_tokens=1000,
    )

    # Exibir resposta
    print("\n" + "=" * 60)
    print("RESPOSTA:")
    print("=" * 60)
    print(response.choices[0].message.content)

    # Enviar feedback (opcional)
    print("\n[Enviando feedback positivo...]")
    vg.feedback(results.query_id, like=True)
    print("Feedback enviado!")


if __name__ == "__main__":
    main()
