"""
Exemplo 6: Filtros Avançados

Este exemplo mostra como usar filtros para refinar buscas.
"""

import os
from vectorgov import VectorGov

API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")


def main():
    vg = VectorGov(api_key=API_KEY)

    print("=" * 60)
    print("DEMONSTRAÇÃO DE FILTROS")
    print("=" * 60)

    # 1. Filtrar por tipo de documento
    print("\n[1] Apenas LEIS:")
    results = vg.search(
        "critérios de julgamento",
        filters={"tipo": "lei"},
        top_k=3,
    )
    for hit in results:
        print(f"    - {hit.source}")

    # 2. Filtrar por ano
    print("\n[2] Documentos de 2021:")
    results = vg.search(
        "estudo técnico preliminar",
        filters={"ano": 2021},
        top_k=3,
    )
    for hit in results:
        print(f"    - {hit.source}")

    # 3. Filtrar por tipo + ano
    print("\n[3] Instruções Normativas de 2022:")
    results = vg.search(
        "ETP",
        filters={"tipo": "in", "ano": 2022},
        top_k=3,
    )
    for hit in results:
        print(f"    - {hit.source}")

    # 4. Filtrar por órgão
    print("\n[4] Documentos da SEGES:")
    results = vg.search(
        "pesquisa de preços",
        filters={"orgao": "seges"},
        top_k=3,
    )
    for hit in results:
        print(f"    - {hit.source}")


if __name__ == "__main__":
    main()
