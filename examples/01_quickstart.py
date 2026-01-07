"""
Exemplo 1: Início Rápido

Este exemplo mostra o uso básico do VectorGov SDK.
"""

import os
from vectorgov import VectorGov

# Obter API key do ambiente ou usar uma de teste
API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_sua_chave_aqui")


def main():
    # 1. Inicializar cliente
    print("Conectando ao VectorGov...")
    vg = VectorGov(api_key=API_KEY)

    # 2. Fazer uma busca simples
    query = "O que é o Estudo Técnico Preliminar (ETP)?"
    print(f"\nBuscando: {query}")

    results = vg.search(query)

    # 3. Exibir informações da busca
    print(f"\nResultados encontrados: {results.total}")
    print(f"Tempo de resposta: {results.latency_ms}ms")
    print(f"Cache: {'Sim' if results.cached else 'Não'}")
    print(f"Modo: {results.mode}")
    print("-" * 60)

    # 4. Iterar pelos resultados
    for i, hit in enumerate(results, 1):
        print(f"\n[{i}] {hit.source}")
        print(f"    Relevância: {hit.score:.2%}")
        print(f"    Texto: {hit.text[:200]}...")

    # 5. Obter contexto formatado
    print("\n" + "=" * 60)
    print("CONTEXTO FORMATADO (para usar com LLMs):")
    print("=" * 60)
    print(results.to_context())


if __name__ == "__main__":
    main()
