"""
Exemplo 7: Comparação de Modos de Busca

Este exemplo compara os três modos de busca disponíveis:
- fast: Mais rápido, sem reranking
- balanced: Equilíbrio (padrão)
- precise: Mais preciso, com HyDE + reranking
"""

import os
from vectorgov import VectorGov, SearchMode

API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")


def main():
    vg = VectorGov(api_key=API_KEY)

    query = "Quais são as hipóteses de dispensa de licitação?"

    print("=" * 60)
    print("COMPARAÇÃO DE MODOS DE BUSCA")
    print("=" * 60)
    print(f"Query: {query}\n")

    # Testar cada modo
    modes = [
        (SearchMode.FAST, "Rápido - Chatbots, alta escala"),
        (SearchMode.BALANCED, "Balanceado - Uso geral (default)"),
        (SearchMode.PRECISE, "Preciso - Análises críticas"),
    ]

    for mode, description in modes:
        print(f"\n[{mode.value.upper()}] {description}")
        print("-" * 40)

        results = vg.search(query, mode=mode, top_k=3)

        print(f"Latência: {results.latency_ms}ms")
        print(f"Cache: {'Sim' if results.cached else 'Não'}")
        print("Top 3 resultados:")

        for i, hit in enumerate(results[:3], 1):
            print(f"  {i}. {hit.source} (score: {hit.score:.3f})")

    # Recomendações
    print("\n" + "=" * 60)
    print("RECOMENDAÇÕES DE USO:")
    print("=" * 60)
    print("""
    FAST (2-3s):
    - Chatbots em tempo real
    - Aplicações de alta escala
    - Quando velocidade é prioridade

    BALANCED (5-8s):
    - APIs de consulta
    - Assistentes virtuais
    - Uso geral

    PRECISE (15-20s):
    - Pareceres técnicos
    - Análises jurídicas
    - Quando precisão é crítica
    """)


if __name__ == "__main__":
    main()
