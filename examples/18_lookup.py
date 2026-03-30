"""
Exemplo 18: Consulta Direta por Referência (Lookup)

Busca determinística de dispositivos legais por referência textual.
Retorna texto exato com contexto (pai, filhos, irmãos).

Latência: < 1 segundo. Ideal para citações exatas.
"""

import os
from vectorgov import VectorGov

API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_sua_chave_aqui")


def main():
    vg = VectorGov(api_key=API_KEY)

    # --- Consulta única ---
    print("=== CONSULTA ÚNICA ===")
    ref = "Art. 75 da Lei 14.133/2021"
    print(f"Consultando: {ref}\n")

    result = vg.lookup(ref)

    if result.found:
        match = result.matches[0]
        print(f"Status: {result.status}")
        print(f"Texto: {match.text[:200]}...")
        print(f"Documento: {match.document_id}")
        print(f"Span: {match.span_id}")

        # Evidence (links para verificação)
        if match.evidence:
            ev = match.evidence
            print(f"\nEvidence:")
            print(f"  Highlight: {ev.get('highlight_url', 'N/A')}")
            print(f"  PDF: {ev.get('pdf_url', 'N/A')}")
            print(f"  Página: {ev.get('page_number', 'N/A')}")

        # Pai e irmãos
        if match.parent:
            print(f"\nArtigo pai: {match.parent.get('span_id', 'N/A')}")
        if match.siblings:
            print(f"Irmãos: {len(match.siblings)} dispositivos")
    else:
        print(f"Não encontrado: {result.status}")

    # --- Consulta em lote ---
    print("\n\n=== CONSULTA EM LOTE ===")
    refs = [
        "Art. 75 da Lei 14.133/2021",
        "Art. 6 da IN 65/2021",
        "Art. 3 do Decreto 10.947/2022",
    ]
    print(f"Consultando {len(refs)} referências...\n")

    result = vg.lookup(refs)

    for match in result.matches:
        status = "✓" if match.text else "✗"
        print(f"  {status} {match.span_id} ({match.document_id}): {(match.text or 'não encontrado')[:80]}...")

    # --- Contexto formatado ---
    print(f"\n=== CONTEXTO ===")
    print(result.to_context()[:400] + "...")


if __name__ == "__main__":
    main()
