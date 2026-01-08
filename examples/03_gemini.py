"""
Exemplo 3: Integração com Google Gemini

Este exemplo mostra como usar o VectorGov com Gemini.

Requisitos:
    pip install vectorgov google-generativeai
"""

import os
from vectorgov import VectorGov
import google.generativeai as genai

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")


def main():
    # Configurar Gemini
    genai.configure(api_key=GOOGLE_KEY)

    # Inicializar VectorGov
    vg = VectorGov(api_key=VECTORGOV_KEY)

    # Pergunta
    query = "Quando o ETP pode ser dispensado?"

    print(f"Pergunta: {query}")
    print("\n[1/2] Buscando contexto no VectorGov...")

    # Buscar contexto (modo precise para análise detalhada)
    results = vg.search(query, mode="precise")

    print(f"      Encontrados {results.total} resultados em {results.latency_ms}ms")
    print("\n[2/2] Gerando resposta com Gemini...")

    # Monta o prompt
    messages = results.to_messages(query)
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]

    # Gerar resposta com system instruction nativo
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1000,
        ),
    )
    response = model.generate_content(user_prompt)

    # Exibir resposta
    print("\n" + "=" * 60)
    print("RESPOSTA:")
    print("=" * 60)
    print(response.text)


if __name__ == "__main__":
    main()
