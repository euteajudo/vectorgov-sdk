"""
Testes de tipo — garantia de billing (Seção 8.7 da spec).

Cada classe tipada tem endpoint_type correto e campos isolados.
"""

from vectorgov.models import (
    SearchResult, HybridResult, LookupResult,
    BaseResult, SmartSearchResult,
)


class TestEndpointType:
    """Cada classe tem endpoint_type correto para billing."""

    def test_search_type(self, search_result):
        assert search_result.endpoint_type == "search"

    def test_hybrid_type(self, hybrid_result):
        assert hybrid_result.endpoint_type == "hybrid"

    def test_lookup_type(self, lookup_result):
        assert lookup_result.endpoint_type == "lookup"

    def test_isinstance_search(self, search_result):
        assert isinstance(search_result, SearchResult)
        assert isinstance(search_result, BaseResult)
        assert not isinstance(search_result, HybridResult)
        assert not isinstance(search_result, LookupResult)

    def test_isinstance_hybrid(self, hybrid_result):
        assert isinstance(hybrid_result, HybridResult)
        assert isinstance(hybrid_result, BaseResult)
        assert not isinstance(hybrid_result, SearchResult)
        assert not isinstance(hybrid_result, LookupResult)

    def test_isinstance_lookup(self, lookup_result):
        assert isinstance(lookup_result, LookupResult)
        assert isinstance(lookup_result, BaseResult)
        assert not isinstance(lookup_result, SearchResult)
        assert not isinstance(lookup_result, HybridResult)


class TestSmartSearchResult:
    """SmartSearchResult herda de SearchResult com billing diferenciado."""

    def test_smart_search_type(self):
        r = SmartSearchResult()
        assert r.endpoint_type == "smart_search"

    def test_smart_search_isinstance(self):
        r = SmartSearchResult()
        assert isinstance(r, SearchResult)
        assert isinstance(r, BaseResult)
        assert not isinstance(r, HybridResult)

    def test_smart_search_inherits_methods(self):
        r = SmartSearchResult(query="teste")
        assert r.query == "teste"
        assert r.total == 0
        assert r.hits == []


class TestBaseResult:
    """BaseResult é ABC e fornece campos compartilhados."""

    def test_base_result_is_abstract(self):
        """BaseResult não pode ser instanciado diretamente."""
        import pytest
        with pytest.raises(TypeError):
            BaseResult()  # type: ignore[abstract]

    def test_search_has_base_fields(self, search_result):
        assert hasattr(search_result, 'query')
        assert hasattr(search_result, 'total')
        assert hasattr(search_result, 'latency_ms')
        assert hasattr(search_result, 'cached')
        assert hasattr(search_result, 'query_id')
        assert hasattr(search_result, 'timestamp')

    def test_hybrid_has_base_fields(self, hybrid_result):
        assert hasattr(hybrid_result, 'query')
        assert hasattr(hybrid_result, 'latency_ms')
        assert hasattr(hybrid_result, 'cached')

    def test_lookup_has_base_fields(self, lookup_result):
        assert hasattr(lookup_result, 'query')
        assert hasattr(lookup_result, 'latency_ms')
        assert hasattr(lookup_result, 'cached')


class TestClassIsolation:
    """Classes não compartilham campos que não deveriam existir."""

    def test_search_has_no_graph_nodes(self, search_result):
        assert not hasattr(search_result, 'graph_nodes')

    def test_search_has_no_match(self, search_result):
        assert not hasattr(search_result, 'match')

    def test_hybrid_has_no_match(self, hybrid_result):
        assert not hasattr(hybrid_result, 'match')

    def test_lookup_has_no_hits(self, lookup_result):
        """Lookup tem match + siblings, não hits[]."""
        assert not hasattr(lookup_result, 'hits')

    def test_lookup_has_no_graph_nodes(self, lookup_result):
        assert not hasattr(lookup_result, 'graph_nodes')
