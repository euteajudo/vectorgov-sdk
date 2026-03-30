"""
Exemplo 17: Busca Híbrida com Expansão por Grafo

Combina busca semântica com navegação por relações
normativas no grafo: CITA, REGULAMENTA, COMPLEMENTA, EXCEPCIONA.

Ideal para encontrar normas relacionadas e cadeias regulatórias.
"""

import os
from vectorgov import VectorGov

API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_sua_chave_aqui")


def main():
    vg = VectorGov(api_key=API_KEY)

    query = "Quais os critérios de julgamento na licitação?"
    print(f"Hybrid Search: {query}\n")

    result = vg.hybrid(
        query,
        top_k=5,
        hops=2,                          # até 2 saltos no grafo
        graph_expansion="bidirectional",  # segue citações em ambas direções
        token_budget=3000,               # limite de tokens no contexto
    )

    # --- Evidências diretas (busca semântica) ---
    print(f"=== EVIDÊNCIAS DIRETAS ({len(result.direct_evidence)} resultados) ===")
    for i, hit in enumerate(result.direct_evidence, 1):
        print(f"[{i}] {hit.source} (score: {hit.score:.2%})")
        print(f"    {hit.text[:150]}...")

    # --- Expansão via grafo (artigos citados) ---
    print(f"\n=== EXPANSÃO VIA GRAFO ({len(result.graph_expansion)} nós) ===")
    for i, node in enumerate(result.graph_expansion, 1):
        hop = node.get("hop", "?")
        freq = node.get("frequency", "?")
        text = node.get("text", "")[:150]
        source = node.get("source", node.get("node_id", ""))
        print(f"[G{i}] {source} (hop={hop}, citado {freq}x)")
        print(f"     {text}...")

    # --- Estatísticas ---
    print(f"\n=== STATS ===")
    print(f"Seeds (busca semântica): {result.stats.get('seeds_count', '?')}")
    print(f"Graph nodes: {result.stats.get('graph_nodes', '?')}")
    print(f"Tokens usados: {result.stats.get('total_tokens', '?')}")
    print(f"Latência: {result.latency_ms}ms")

    # --- Contexto formatado para LLM ---
    print(f"\n=== CONTEXTO ===")
    print(result.to_context()[:400] + "...")


if __name__ == "__main__":
    main()
