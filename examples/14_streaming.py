"""
Exemplo 14: Streaming de Respostas em Tempo Real

Demonstra como usar o método ask_stream() para obter
respostas em tempo real, ideal para interfaces de chat.

Requisitos:
    pip install vectorgov

Uso:
    python 14_streaming.py

"""

import os
import sys

from vectorgov import VectorGov


def main():
    # Inicializa cliente
    api_key = os.environ.get("VECTORGOV_API_KEY")
    if not api_key:
        print("Defina VECTORGOV_API_KEY ou edite este arquivo")
        return

    vg = VectorGov(api_key=api_key)

    print("=" * 60)
    print("EXEMPLO 1: Streaming Básico")
    print("=" * 60)
    print()

    query = "O que é ETP?"
    print(f"Pergunta: {query}\n")
    print("Resposta: ", end="")

    for chunk in vg.ask_stream(query):
        if chunk.type == "token":
            print(chunk.content, end="", flush=True)
        elif chunk.type == "complete":
            print(f"\n\n[Concluído com {len(chunk.citations or [])} citações]")

    print()
    print("=" * 60)
    print("EXEMPLO 2: Streaming com Todos os Eventos")
    print("=" * 60)
    print()

    query = "Quando o ETP pode ser dispensado?"
    print(f"Pergunta: {query}\n")

    for chunk in vg.ask_stream(query, top_k=3, mode="balanced"):
        if chunk.type == "start":
            print(f"[INÍCIO] Query: {chunk.query}", file=sys.stderr)

        elif chunk.type == "retrieval":
            print(
                f"[RETRIEVAL] {chunk.chunks} documentos em {chunk.time_ms:.0f}ms",
                file=sys.stderr,
            )

        elif chunk.type == "token":
            print(chunk.content, end="", flush=True)

        elif chunk.type == "complete":
            print("\n")
            print("[COMPLETO]", file=sys.stderr)
            if chunk.citations:
                print(f"  Citações: {len(chunk.citations)}", file=sys.stderr)
                for i, cit in enumerate(chunk.citations[:3], 1):
                    source = cit.get("source", "?")
                    print(f"    {i}. {source}", file=sys.stderr)
            if chunk.query_hash:
                print(f"  Query Hash: {chunk.query_hash[:16]}...", file=sys.stderr)

        elif chunk.type == "error":
            print(f"\n[ERRO] {chunk.message}", file=sys.stderr)
            break

    print()
    print("=" * 60)
    print("EXEMPLO 3: Streaming para Interface de Chat")
    print("=" * 60)
    print()

    # Simula uma interface de chat simples
    query = "Quais os critérios de julgamento na licitação?"

    print(f"Usuário: {query}")
    print()
    print("Assistente: ", end="")

    tokens_received = 0
    citations_count = 0

    for chunk in vg.ask_stream(query, mode="fast"):
        if chunk.type == "token":
            print(chunk.content, end="", flush=True)
            tokens_received += 1

        elif chunk.type == "complete":
            citations_count = len(chunk.citations or [])
            # Envia feedback positivo automaticamente
            if chunk.query_hash:
                try:
                    vg.feedback(chunk.query_hash, like=True)
                except Exception:
                    pass  # Ignora erros de feedback

    print("\n")
    print(f"[{tokens_received} tokens, {citations_count} citações]")

    print()
    print("=" * 60)
    print("Streaming concluído!")
    print("=" * 60)


if __name__ == "__main__":
    main()
