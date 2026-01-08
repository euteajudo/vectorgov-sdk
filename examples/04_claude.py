"""
Exemplo 4: Integração com Anthropic Claude

Este exemplo mostra como usar o VectorGov com Claude.

Requisitos:
    pip install vectorgov anthropic
"""

import os
from vectorgov import VectorGov
from anthropic import Anthropic

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")


def main():
    # Inicializar clientes
    vg = VectorGov(api_key=VECTORGOV_KEY)
    client = Anthropic(api_key=ANTHROPIC_KEY)

    # Pergunta
    query = "Quais documentos devem compor o Estudo Técnico Preliminar?"

    print(f"Pergunta: {query}")
    print("\n[1/2] Buscando contexto no VectorGov...")

    # Buscar contexto (modo precise para análise detalhada)
    results = vg.search(query, mode="precise")

    print(f"      Encontrados {results.total} resultados em {results.latency_ms}ms")
    print("\n[2/2] Gerando resposta com Claude...")

    # Monta o prompt
    messages = results.to_messages(query)

    # Gerar resposta com Claude
    # Nota: Claude usa o parâmetro 'system' separado das messages
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=messages[0]["content"],  # System prompt separado
        messages=[{"role": "user", "content": messages[1]["content"]}],
    )

    # Exibir resposta
    print("\n" + "=" * 60)
    print("RESPOSTA:")
    print("=" * 60)
    print(response.content[0].text)


if __name__ == "__main__":
    main()
