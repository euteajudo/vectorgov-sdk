"""
Exemplo 5: Chatbot Completo

Este exemplo mostra como criar um chatbot interativo
com VectorGov + OpenAI.

Requisitos:
    pip install vectorgov openai
"""

import os
from vectorgov import VectorGov
from openai import OpenAI

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def create_chatbot():
    """Cria um chatbot com VectorGov + OpenAI."""

    vg = VectorGov(api_key=VECTORGOV_KEY)
    openai = OpenAI(api_key=OPENAI_KEY)

    # System prompt para o chatbot
    system_prompt = vg.get_system_prompt("chatbot")

    print("=" * 60)
    print("CHATBOT JURÍDICO - VectorGov")
    print("=" * 60)
    print("Digite suas perguntas sobre licitações e contratos públicos.")
    print("Digite 'sair' para encerrar.\n")

    while True:
        # Obter pergunta do usuário
        query = input("Você: ").strip()

        if query.lower() in ["sair", "exit", "quit"]:
            print("\nAté logo!")
            break

        if not query:
            continue

        # Buscar contexto (modo fast para chatbot)
        print("\n[Buscando...]")
        results = vg.search(query, mode="fast", top_k=3)

        # Gerar resposta
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Modelo mais rápido para chat
            messages=results.to_messages(query, system_prompt=system_prompt),
            temperature=0.5,
            max_tokens=500,
        )

        # Exibir resposta
        answer = response.choices[0].message.content
        print(f"\nAssistente: {answer}")
        print(f"\n[Fontes: {', '.join(hit.source for hit in results[:3])}]")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    create_chatbot()
