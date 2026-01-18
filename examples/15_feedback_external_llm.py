"""
Exemplo 15: Feedback para respostas de LLMs externos

Este exemplo demonstra como salvar respostas de LLMs externos (OpenAI, Gemini, etc.)
no cache do VectorGov para habilitar o sistema de feedback (like/dislike).

Isso permite:
1. Coletar feedback dos usuários sobre qualquer LLM
2. Contribuir para o treinamento de modelos futuros
3. Rastrear a qualidade das respostas ao longo do tempo

Requisitos:
    pip install vectorgov openai
"""

import os
import time
from vectorgov import VectorGov
from openai import OpenAI

# Configuração
vg = VectorGov(api_key=os.environ.get("VECTORGOV_API_KEY"))
openai_client = OpenAI()


def main():
    query = "O que é o Estudo Técnico Preliminar (ETP)?"

    print(f"Pergunta: {query}\n")

    # 1. Busca no VectorGov
    print("1. Buscando contexto no VectorGov...")
    start_search = time.time()
    results = vg.search(query, top_k=5)
    search_time = (time.time() - start_search) * 1000
    print(f"   Encontrados: {len(results)} documentos ({search_time:.0f}ms)\n")

    # 2. Gera resposta com OpenAI
    print("2. Gerando resposta com OpenAI GPT-4o...")
    start_gen = time.time()
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=results.to_messages(query),
        temperature=0.7,
        max_tokens=500,
    )
    gen_time = (time.time() - start_gen) * 1000
    answer = response.choices[0].message.content
    print(f"   Resposta gerada ({gen_time:.0f}ms)\n")
    print("-" * 60)
    print(answer)
    print("-" * 60 + "\n")

    # 3. Salva a resposta no VectorGov para feedback
    print("3. Salvando resposta no VectorGov para feedback...")
    stored = vg.store_response(
        query=query,
        answer=answer,
        provider="OpenAI",
        model="gpt-4o",
        chunks_used=len(results),
        latency_ms=search_time + gen_time,
        retrieval_ms=search_time,
        generation_ms=gen_time,
    )

    if stored.success:
        print(f"   Sucesso! query_hash: {stored.query_hash}\n")
    else:
        print(f"   Erro: {stored.message}\n")
        return

    # 4. Simula feedback do usuário
    print("4. Enviando feedback positivo (like)...")
    feedback_ok = vg.feedback(stored.query_hash, like=True)
    if feedback_ok:
        print("   Feedback registrado com sucesso!")
    else:
        print("   Erro ao registrar feedback")

    print("\n" + "=" * 60)
    print("Fluxo completo:")
    print(f"  - Busca: {search_time:.0f}ms")
    print(f"  - Geração (OpenAI): {gen_time:.0f}ms")
    print(f"  - Total: {search_time + gen_time:.0f}ms")
    print(f"  - query_hash para feedback: {stored.query_hash}")
    print("=" * 60)


if __name__ == "__main__":
    main()
