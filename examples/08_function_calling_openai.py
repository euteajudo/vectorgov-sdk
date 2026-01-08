"""
Exemplo 8: Function Calling com OpenAI

Este exemplo mostra como usar o VectorGov como ferramenta (tool) com OpenAI.
O LLM decide automaticamente quando precisa consultar a legislação.

Requisitos:
    pip install vectorgov openai
"""

import os
from vectorgov import VectorGov
from openai import OpenAI

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def main():
    # Inicializar clientes
    vg = VectorGov(api_key=VECTORGOV_KEY)
    client = OpenAI(api_key=OPENAI_KEY)

    # Pergunta do usuário
    user_question = "Me explique quais são os critérios de julgamento em uma licitação"

    print(f"Pergunta: {user_question}")
    print("\n[1/3] Enviando pergunta para o GPT-4o com ferramenta VectorGov...")

    # Primeira chamada - GPT decide se precisa da ferramenta
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_question}],
        tools=[vg.to_openai_tool()],  # Registra a ferramenta VectorGov
        tool_choice="auto",  # GPT decide se usa ou não
    )

    message = response.choices[0].message

    # Verifica se GPT quer usar a ferramenta
    if message.tool_calls:
        print("\n[2/3] GPT-4o solicitou consulta à legislação...")
        tool_call = message.tool_calls[0]

        # Executa a busca na legislação
        tool_result = vg.execute_tool_call(tool_call)
        print(f"      Encontrados resultados na legislação")

        # Segunda chamada - GPT usa os resultados para responder
        print("\n[3/3] Gerando resposta final com base na legislação...")
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_question},
                message,  # Inclui a mensagem com tool_call
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                },
            ],
        )

        answer = final_response.choices[0].message.content
    else:
        # GPT respondeu sem precisar da ferramenta
        answer = message.content

    # Exibir resposta
    print("\n" + "=" * 60)
    print("RESPOSTA:")
    print("=" * 60)
    print(answer)


if __name__ == "__main__":
    main()
