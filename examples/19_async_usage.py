"""
Exemplo 19: Cliente Assíncrono (AsyncVectorGov)

Wrapper async sobre o cliente síncrono usando asyncio.to_thread().
Sem dependências adicionais (não requer httpx/aiohttp).

Ideal para aplicações web assíncronas e buscas paralelas.
"""

import asyncio
import os
from vectorgov import AsyncVectorGov
from vectorgov.exceptions import RateLimitError, TierError

API_KEY = os.getenv("VECTORGOV_API_KEY", "vg_sua_chave_aqui")


async def exemplo_basico():
    """Busca simples com async/await."""
    print("=== BUSCA ASYNC BÁSICA ===")

    async with AsyncVectorGov(api_key=API_KEY) as vg:
        result = await vg.search("O que é ETP?")
        print(f"Resultados: {result.total}")
        for hit in result:
            print(f"  - {hit.source}: {hit.text[:100]}...")


async def exemplo_paralelo():
    """Múltiplas buscas em paralelo com asyncio.gather()."""
    print("\n=== BUSCAS PARALELAS ===")

    queries = [
        "O que é Estudo Técnico Preliminar?",
        "Quando a licitação pode ser dispensada?",
        "Quais os critérios de julgamento?",
        "Como funciona o pregão eletrônico?",
    ]

    async with AsyncVectorGov(api_key=API_KEY) as vg:
        # Executa todas as buscas em paralelo
        results = await asyncio.gather(
            *[vg.search(q) for q in queries],
            return_exceptions=True,  # não falha se uma query der erro
        )

        for query, result in zip(queries, results):
            if isinstance(result, Exception):
                print(f"  ✗ {query[:40]}... → Erro: {result}")
            else:
                print(f"  ✓ {query[:40]}... → {result.total} resultados ({result.latency_ms}ms)")


async def exemplo_error_handling():
    """Tratamento de erros em contexto async."""
    print("\n=== ERROR HANDLING ASYNC ===")

    async with AsyncVectorGov(api_key=API_KEY) as vg:
        try:
            result = await vg.smart_search("Hipóteses de dispensa de licitação")
            print(f"Confiança: {result.confianca}")
        except TierError as e:
            print(f"Plano insuficiente: {e}")
            print("Fazendo fallback para busca simples...")
            result = await vg.search("Hipóteses de dispensa de licitação")
            print(f"Fallback OK: {result.total} resultados")
        except RateLimitError as e:
            print(f"Rate limit: {e}")
            if e.retry_after:
                print(f"Aguardando {e.retry_after}s...")
                await asyncio.sleep(e.retry_after)


async def main():
    await exemplo_basico()
    await exemplo_paralelo()
    await exemplo_error_handling()


if __name__ == "__main__":
    asyncio.run(main())
