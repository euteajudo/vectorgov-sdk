"""
Exemplo 12: Integração com HuggingFace Transformers

Este exemplo mostra como usar o VectorGov com modelos locais
do HuggingFace para RAG gratuito e offline.

Requisitos:
    pip install vectorgov transformers torch accelerate

Modelos recomendados (em ordem de leveza):
    - meta-llama/Llama-3.2-1B-Instruct (2GB VRAM, roda em CPU)
    - Qwen/Qwen2.5-3B-Instruct (6GB VRAM, excelente português)
    - meta-llama/Llama-3.2-3B-Instruct (6GB VRAM)
    - Qwen/Qwen2.5-7B-Instruct (14GB VRAM, melhor qualidade)
"""

import os
from vectorgov import VectorGov

# Chave de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")


def exemplo_basico():
    """Exemplo básico com pipeline simples."""
    print("=" * 60)
    print("EXEMPLO 1: Pipeline Básico")
    print("=" * 60)

    try:
        from transformers import pipeline
    except ImportError:
        print("\nTransformers não instalado.")
        print("Para usar este exemplo, instale:")
        print("  pip install transformers torch accelerate")
        print("\nExibindo código de exemplo:\n")

        code = '''
from vectorgov import VectorGov
from transformers import pipeline

# Inicializa VectorGov
vg = VectorGov(api_key="vg_xxx")

# Carrega modelo local (primeira vez faz download)
llm = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-3B-Instruct",
    device_map="auto",  # Usa GPU se disponível
)

# Busca contexto
query = "O que é ETP?"
results = vg.search(query, top_k=3)

# Formata prompt
messages = [
    {"role": "system", "content": "Você é um assistente jurídico. Responda com base no contexto."},
    {"role": "user", "content": f"Contexto:\\n{results.to_context()}\\n\\nPergunta: {query}"},
]

# Gera resposta
output = llm(messages, max_new_tokens=256)
print(output[0]["generated_text"][-1]["content"])
'''
        print(code)
        return

    from vectorgov.integrations.transformers import format_prompt_for_transformers

    # Inicializa VectorGov
    vg = VectorGov(api_key=VECTORGOV_KEY)

    # Busca contexto (não precisa do modelo para isso)
    query = "O que é Estudo Técnico Preliminar?"
    print(f"\nQuery: {query}")
    print("\nBuscando no VectorGov...")

    results = vg.search(query, top_k=3)
    print(f"Encontrados: {results.total} resultados")
    print(f"Latência: {results.latency_ms}ms")

    # Mostra como seria o prompt formatado
    prompt = format_prompt_for_transformers(
        query=query,
        context=results.to_context(),
        chat_template="raw",
    )
    print("\n" + "-" * 40)
    print("PROMPT FORMATADO (primeiros 500 chars):")
    print("-" * 40)
    print(prompt[:500] + "...")
    print()


def exemplo_rag_pipeline():
    """Exemplo com pipeline RAG completo."""
    print("=" * 60)
    print("EXEMPLO 2: Pipeline RAG Completo")
    print("=" * 60)

    try:
        from transformers import pipeline
    except ImportError:
        print("\nTransformers não instalado. Exibindo código de exemplo:\n")

        code = '''
from vectorgov import VectorGov
from vectorgov.integrations.transformers import create_rag_pipeline
from transformers import pipeline

# Inicializa
vg = VectorGov(api_key="vg_xxx")
llm = pipeline("text-generation", model="Qwen/Qwen2.5-3B-Instruct", device_map="auto")

# Cria pipeline RAG
rag = create_rag_pipeline(
    vectorgov_client=vg,
    text_generation_pipeline=llm,
    top_k=5,
    mode="balanced",
    max_new_tokens=512,
)

# Usa como função simples
resposta = rag("Quais os critérios de julgamento na licitação?")
print(resposta)
'''
        print(code)
        return

    # Se transformers instalado, mostra estrutura
    from vectorgov.integrations.transformers import create_rag_pipeline

    print("\nA função create_rag_pipeline() cria um pipeline que:")
    print("1. Recebe uma pergunta")
    print("2. Busca contexto no VectorGov")
    print("3. Formata o prompt")
    print("4. Gera resposta com o modelo local")
    print("5. Retorna texto limpo")
    print()


def exemplo_classe_rag():
    """Exemplo com classe VectorGovRAG."""
    print("=" * 60)
    print("EXEMPLO 3: Classe VectorGovRAG")
    print("=" * 60)

    try:
        from transformers import pipeline
    except ImportError:
        print("\nTransformers não instalado. Exibindo código de exemplo:\n")

        code = '''
from vectorgov import VectorGov
from vectorgov.integrations.transformers import VectorGovRAG
from transformers import pipeline

# Inicializa
vg = VectorGov(api_key="vg_xxx")
llm = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct", device_map="auto")

# Cria instância RAG
rag = VectorGovRAG(
    vectorgov_client=vg,
    text_generation_pipeline=llm,
    top_k=5,
    temperature=0.1,
)

# Faz perguntas
response = rag.ask("O que é ETP?")

print("RESPOSTA:")
print(response.answer)
print()
print("FONTES:")
for source in response.sources:
    print(f"  - {source}")
print()
print(f"Latência busca: {response.latency_ms}ms")
print(f"Cache: {response.cached}")

# Histórico de conversas
print(f"\\nHistórico: {len(rag.history)} perguntas")
'''
        print(code)
        return

    from vectorgov.integrations.transformers import VectorGovRAG, RAGResponse

    print("\nA classe VectorGovRAG oferece:")
    print("- Método ask() que retorna RAGResponse")
    print("- RAGResponse com answer, sources, context, latency_ms")
    print("- Histórico de conversas")
    print("- Configuração de temperatura e max_tokens")
    print()


def exemplo_modelos_recomendados():
    """Lista modelos recomendados."""
    print("=" * 60)
    print("EXEMPLO 4: Modelos Recomendados")
    print("=" * 60)

    from vectorgov.integrations.transformers import get_recommended_models, estimate_vram_usage

    models = get_recommended_models()

    print("\nMODELOS RECOMENDADOS PARA PORTUGUÊS:\n")
    print(f"{'Modelo':<45} {'VRAM':<8} {'Qualidade':<12} {'PT-BR':<10}")
    print("-" * 80)

    for name, info in models.items():
        print(f"{name:<45} {info['vram_gb']}GB{'':<4} {info['quality']:<12} {info['portuguese']:<10}")

    print("\n" + "-" * 40)
    print("ESTIMATIVA DE VRAM:")
    print("-" * 40)

    test_models = [
        "meta-llama/Llama-3.2-1B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "algum-modelo/modelo-13b-custom",
    ]

    for model in test_models:
        vram = estimate_vram_usage(model)
        print(f"{model}: {vram}GB" if vram else f"{model}: desconhecido")
    print()


def exemplo_cpu_only():
    """Exemplo para rodar sem GPU."""
    print("=" * 60)
    print("EXEMPLO 5: Rodando sem GPU (CPU only)")
    print("=" * 60)

    code = '''
from vectorgov import VectorGov
from vectorgov.integrations.transformers import create_rag_pipeline
from transformers import pipeline
import torch

# Força uso de CPU
llm = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B-Instruct",  # Modelo leve!
    device="cpu",
    torch_dtype=torch.float32,  # CPU não suporta float16
)

vg = VectorGov(api_key="vg_xxx")
rag = create_rag_pipeline(vg, llm, max_new_tokens=256)

# Mais lento, mas funciona sem GPU
resposta = rag("O que é ETP?")
print(resposta)
'''

    print("\nPara rodar sem GPU, use modelos leves:\n")
    print(code)
    print()


def exemplo_quantizado():
    """Exemplo com modelo quantizado (4-bit)."""
    print("=" * 60)
    print("EXEMPLO 6: Modelo Quantizado (4-bit)")
    print("=" * 60)

    code = '''
from vectorgov import VectorGov
from vectorgov.integrations.transformers import VectorGovRAG
from transformers import pipeline, BitsAndBytesConfig
import torch

# Configuração de quantização 4-bit
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)

# Carrega modelo quantizado (usa ~4GB VRAM para modelo 7B)
llm = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-7B-Instruct",
    model_kwargs={"quantization_config": quantization_config},
    device_map="auto",
)

vg = VectorGov(api_key="vg_xxx")
rag = VectorGovRAG(vg, llm)

response = rag.ask("Quais os critérios de julgamento?")
print(response.answer)
'''

    print("\nPara usar menos VRAM, quantize o modelo:\n")
    print("Requisito: pip install bitsandbytes\n")
    print(code)
    print()


def main():
    print("\n" + "=" * 60)
    print("VECTORGOV + HUGGINGFACE TRANSFORMERS")
    print("RAG com Modelos Locais Gratuitos")
    print("=" * 60 + "\n")

    # Exemplo 1: Básico
    exemplo_basico()
    print("\n")

    # Exemplo 2: Pipeline RAG
    exemplo_rag_pipeline()
    print("\n")

    # Exemplo 3: Classe RAG
    exemplo_classe_rag()
    print("\n")

    # Exemplo 4: Modelos recomendados
    exemplo_modelos_recomendados()
    print("\n")

    # Exemplo 5: CPU only
    exemplo_cpu_only()
    print("\n")

    # Exemplo 6: Quantizado
    exemplo_quantizado()


if __name__ == "__main__":
    main()
