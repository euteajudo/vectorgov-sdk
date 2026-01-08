#!/usr/bin/env python3
"""
Exemplo de integração VectorGov + Ollama.

Ollama permite rodar LLMs localmente com facilidade.
Combinado com VectorGov, você tem RAG jurídico 100% local.

Pré-requisitos:
    1. Ollama instalado: https://ollama.ai/
    2. Modelo baixado: ollama pull qwen3:8b
    3. VectorGov SDK: pip install vectorgov

Uso:
    export VECTORGOV_API_KEY="vg_xxx"
    python 13_ollama_local.py
"""

import os


def exemplo_1_pipeline_simples():
    """Pipeline RAG simples com uma linha."""
    print("\n" + "=" * 60)
    print("Exemplo 1: Pipeline Simples")
    print("=" * 60)

    from vectorgov import VectorGov
    from vectorgov.integrations.ollama import create_rag_pipeline

    vg = VectorGov()

    # Cria pipeline RAG
    rag = create_rag_pipeline(vg, model="qwen3:8b")

    # Faz pergunta
    query = "O que é ETP segundo a legislação?"
    print(f"\nQuery: {query}")
    print("\nGerando resposta...")

    response = rag(query)
    print(f"\nResposta:\n{response}")


def exemplo_2_classe_completa():
    """Classe VectorGovOllama com respostas estruturadas."""
    print("\n" + "=" * 60)
    print("Exemplo 2: Classe VectorGovOllama")
    print("=" * 60)

    from vectorgov import VectorGov
    from vectorgov.integrations.ollama import VectorGovOllama

    vg = VectorGov()

    # Cria instância do RAG
    rag = VectorGovOllama(vg, model="qwen3:8b", top_k=5)

    # Faz pergunta
    query = "Quando o ETP pode ser dispensado?"
    print(f"\nQuery: {query}")
    print("\nGerando resposta...")

    result = rag.ask(query)

    print(f"\nResposta:\n{result.answer}")
    print(f"\nFontes ({len(result.sources)}):")
    for source in result.sources:
        print(f"  - {source}")
    print(f"\nMétricas:")
    print(f"  - Modelo: {result.model}")
    print(f"  - Latência: {result.latency_ms}ms")
    print(f"  - Cache: {result.cached}")


def exemplo_3_listar_modelos():
    """Lista modelos disponíveis no Ollama."""
    print("\n" + "=" * 60)
    print("Exemplo 3: Listar Modelos Disponíveis")
    print("=" * 60)

    from vectorgov.integrations.ollama import (
        list_models,
        get_recommended_models,
        check_ollama_available,
    )

    # Verifica se Ollama está rodando
    if not check_ollama_available():
        print("ERRO: Ollama não está rodando!")
        print("Inicie com: ollama serve")
        return

    print("\nModelos instalados no Ollama:")
    for model in list_models():
        print(f"  - {model}")

    print("\nModelos recomendados para português:")
    for name, info in get_recommended_models().items():
        print(f"\n  {name}:")
        print(f"    {info['description']}")
        print(f"    RAM: ~{info['ram_gb']}GB | Qualidade: {info['quality']}")
        print(f"    Instalar: {info['command']}")


def exemplo_4_configuracao_avancada():
    """Configuração avançada do RAG."""
    print("\n" + "=" * 60)
    print("Exemplo 4: Configuração Avançada")
    print("=" * 60)

    from vectorgov import VectorGov
    from vectorgov.integrations.ollama import VectorGovOllama

    vg = VectorGov()

    # System prompt customizado
    custom_prompt = """Você é um especialista em licitações e contratos públicos.
Responda de forma técnica e cite sempre os artigos relevantes.
Use linguagem formal e precisa."""

    # RAG com configuração customizada
    rag = VectorGovOllama(
        vg,
        model="qwen3:8b",
        top_k=3,
        mode="precise",  # Busca mais precisa (usa HyDE + Reranker)
        temperature=0.0,  # Determinístico
        max_tokens=1024,  # Respostas mais longas
        system_prompt=custom_prompt,
    )

    query = "Quais são os critérios de julgamento em licitações?"
    print(f"\nQuery: {query}")
    print("\nGerando resposta com configuração avançada...")

    result = rag.ask(query)
    print(f"\nResposta:\n{result.answer}")


def exemplo_5_chat_com_historico():
    """Chat com histórico de mensagens."""
    print("\n" + "=" * 60)
    print("Exemplo 5: Chat com Histórico")
    print("=" * 60)

    from vectorgov import VectorGov
    from vectorgov.integrations.ollama import VectorGovOllama

    vg = VectorGov()
    rag = VectorGovOllama(vg, model="qwen3:8b")

    # Histórico de mensagens
    messages = [
        {"role": "user", "content": "O que é ETP?"},
    ]

    print("\nUsuário: O que é ETP?")
    response1 = rag.chat(messages, use_rag=True)
    print(f"Assistente: {response1[:500]}...")

    # Adiciona resposta ao histórico
    messages.append({"role": "assistant", "content": response1})

    # Pergunta de follow-up (usa histórico)
    messages.append({"role": "user", "content": "E quando ele pode ser dispensado?"})

    print("\nUsuário: E quando ele pode ser dispensado?")
    response2 = rag.chat(messages, use_rag=True)
    print(f"Assistente: {response2[:500]}...")


def exemplo_6_comparar_modelos():
    """Compara respostas de diferentes modelos."""
    print("\n" + "=" * 60)
    print("Exemplo 6: Comparar Modelos")
    print("=" * 60)

    from vectorgov import VectorGov
    from vectorgov.integrations.ollama import VectorGovOllama, list_models

    vg = VectorGov()
    available = list_models()

    # Modelos para comparar (filtra os disponíveis)
    models_to_test = ["qwen3:4b", "qwen3:8b"]
    models_to_test = [m for m in models_to_test if m in available]

    if len(models_to_test) < 2:
        print("Instale mais modelos para comparar:")
        print("  ollama pull qwen3:4b")
        print("  ollama pull qwen3:8b")
        return

    query = "O que é pesquisa de preços?"
    print(f"\nQuery: {query}")

    for model in models_to_test:
        print(f"\n--- {model} ---")
        try:
            rag = VectorGovOllama(vg, model=model, max_tokens=256)
            result = rag.ask(query)
            print(f"Latência: {result.latency_ms}ms")
            print(f"Resposta: {result.answer[:300]}...")
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    # Verifica API key
    if not os.environ.get("VECTORGOV_API_KEY"):
        print("ERRO: Configure VECTORGOV_API_KEY")
        print("  export VECTORGOV_API_KEY='vg_sua_chave'")
        exit(1)

    print("=" * 60)
    print("VectorGov + Ollama - Exemplos de Integração")
    print("=" * 60)

    # Executa exemplos
    try:
        exemplo_3_listar_modelos()
        exemplo_1_pipeline_simples()
        exemplo_2_classe_completa()
        # exemplo_4_configuracao_avancada()  # Descomente para testar
        # exemplo_5_chat_com_historico()  # Descomente para testar
        # exemplo_6_comparar_modelos()  # Descomente para testar
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro: {e}")
        raise
