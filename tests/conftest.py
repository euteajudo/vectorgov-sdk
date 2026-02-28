"""
Fixtures compartilhadas para testes do VectorGov SDK.

Cada fixture JSON simula a resposta real da API e é instanciada
na classe tipada correta usando os parsers reais do client.py,
validando o caminho completo: JSON → parser → classe → to_xml().
"""

import json

import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Carrega um arquivo JSON de fixtures."""
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _make_client():
    """Cria instância VectorGov sem chamar __init__ (parsers não usam self)."""
    from vectorgov.client import VectorGov
    client = VectorGov.__new__(VectorGov)
    return client


# ─── Raw dicts (payload da API) ───


@pytest.fixture
def hybrid_raw():
    return load_fixture("hybrid_criterios_julgamento.json")


@pytest.fixture
def search_raw():
    return load_fixture("search_pesquisa_precos.json")


@pytest.fixture
def lookup_raw():
    return load_fixture("lookup_par_018_2.json")


# ─── Objetos tipados (como vg.search/hybrid/lookup retornariam) ───


@pytest.fixture
def search_result(search_raw):
    """SearchResult tipado — como vg.search() retornaria."""
    client = _make_client()
    return client._parse_search_response(
        query="Como fazer pesquisa de preços?",
        response=search_raw,
        mode="balanced",
    )


@pytest.fixture
def hybrid_result(hybrid_raw):
    """HybridResult tipado — como vg.hybrid() retornaria."""
    client = _make_client()
    return client._parse_hybrid_response(
        query="Quais os critérios de julgamento?",
        response=hybrid_raw,
    )


@pytest.fixture
def lookup_result(lookup_raw):
    """LookupResult tipado — como vg.lookup() retornaria."""
    client = _make_client()
    return client._parse_lookup_response(
        reference="§ 2º do Art. 18 da Lei 14.133",
        response=lookup_raw,
    )
