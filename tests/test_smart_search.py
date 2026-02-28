"""Testes para smart_search() — endpoint turnkey MOC v4 (ADDENDUM v2)."""

import pytest
import json
from unittest.mock import patch, MagicMock
from vectorgov import VectorGov, TierError, ValidationError, SearchResult
from vectorgov.models import SmartSearchResult


@pytest.fixture
def vg():
    """Client com API key de teste."""
    return VectorGov(api_key="vg_test_123")


@pytest.fixture
def smart_response():
    """Fixture de resposta bem-sucedida."""
    with open("tests/fixtures/smart_search_response.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tier_error_response():
    """Fixture de erro 403."""
    with open("tests/fixtures/smart_search_tier_error.json", encoding="utf-8") as f:
        return json.load(f)


class TestSmartSearchValidation:
    """Testes de validação de parâmetros."""

    def test_empty_query_raises(self, vg):
        with pytest.raises(ValidationError, match="vazia"):
            vg.smart_search("")

    def test_short_query_raises(self, vg):
        with pytest.raises(ValidationError, match="3 caracteres"):
            vg.smart_search("ab")

    def test_long_query_raises(self, vg):
        with pytest.raises(ValidationError, match="1000 caracteres"):
            vg.smart_search("x" * 1001)


class TestSmartSearchSignature:
    """O smart_search() aceita APENAS query + use_cache."""

    @patch.object(VectorGov, '_parse_search_response')
    def test_accepts_only_query_and_cache(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("critérios de julgamento")

            _, kwargs = mock_post.call_args
            data = kwargs.get("data", {})

            # SÓ query + use_cache
            assert set(data.keys()) == {"query", "use_cache"}
            assert data["query"] == "critérios de julgamento"
            assert data["use_cache"] is False

    @patch.object(VectorGov, '_parse_search_response')
    def test_no_top_k_in_request(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query")
            data = mock_post.call_args[1].get("data", {})
            assert "top_k" not in data

    @patch.object(VectorGov, '_parse_search_response')
    def test_no_expand_citations_in_request(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query")
            data = mock_post.call_args[1].get("data", {})
            assert "expand_citations" not in data
            assert "citation_expansion_top_n" not in data

    @patch.object(VectorGov, '_parse_search_response')
    def test_no_mode_in_request(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query")
            data = mock_post.call_args[1].get("data", {})
            assert "mode" not in data
            assert "use_hyde" not in data
            assert "use_reranker" not in data

    @patch.object(VectorGov, '_parse_search_response')
    def test_use_cache_true(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query", use_cache=True)
            data = mock_post.call_args[1].get("data", {})
            assert data["use_cache"] is True

    @patch.object(VectorGov, '_parse_search_response')
    def test_timeout_120s(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query")
            _, kwargs = mock_post.call_args
            assert kwargs.get("timeout") == 120


class TestSmartSearchResponse:
    """Resposta é SmartSearchResult (herda SearchResult)."""

    def test_returns_smart_search_result(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            assert isinstance(result, SmartSearchResult)
            assert isinstance(result, SearchResult)

    def test_endpoint_type_is_smart_search(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            assert result.endpoint_type == "smart_search"

    def test_mode_is_smart(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            assert result.mode == "smart"

    def test_total_equals_approved_hits(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            assert result.total == len(result.hits)
            assert result.total == 2

    def test_curadoria_fields_present(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            hit = result.hits[0]
            assert hit.nota_especialista is not None
            assert hit.jurisprudencia_tcu is not None
            assert hit.acordao_tcu_link is not None

    def test_evidence_url_present(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            for hit in result.hits:
                assert hit.evidence_url is not None
                assert "/api/v1/evidence/" in hit.evidence_url

    def test_document_url_present(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            for hit in result.hits:
                assert hit.document_url is not None
                assert "/api/v1/documents/" in hit.document_url

    def test_to_xml_works(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            xml = result.to_xml("full")
            assert "vectorgov_knowledge_package" in xml
            assert "base_normativa" in xml

    def test_to_messages_works(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            messages = result.to_messages("Quais os critérios?", level="full")
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    def test_to_response_schema_works(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            schema = result.to_response_schema()
            assert schema is not None
            assert "fundamentacao" in str(schema)


class TestSmartSearchErrors:
    """Testes de tratamento de erros."""

    def test_tier_error_403(self, vg):
        with patch.object(vg._http, 'post', side_effect=TierError(
            "smart-search requer plano Premium",
            upgrade_url="https://vectorgov.io/pricing"
        )):
            with pytest.raises(TierError) as exc_info:
                vg.smart_search("query")
            assert exc_info.value.upgrade_url == "https://vectorgov.io/pricing"

    def test_fallback_pattern(self, vg, smart_response):
        """Testa o padrão try smart_search / except TierError / fallback search."""
        call_count = 0

        def mock_post(path, data=None, timeout=None):
            nonlocal call_count
            call_count += 1
            if path == "/sdk/smart-search":
                raise TierError("requer plano Premium")
            return smart_response

        with patch.object(vg._http, 'post', side_effect=mock_post):
            try:
                result = vg.smart_search("query")
            except TierError:
                result = vg.search("query", mode="precise")

            assert isinstance(result, SearchResult)


class TestSmartSearchIntegration:
    """Testes de integração com outros métodos do SDK."""

    def test_store_response_with_smart_search(self, vg, smart_response):
        store_response_data = {
            "success": True,
            "query_hash": "hash_abc123",
            "message": "Resposta armazenada"
        }

        with patch.object(vg._http, 'post') as mock_post:
            mock_post.side_effect = [smart_response, store_response_data]

            result = vg.smart_search("critérios")
            stored = vg.store_response(
                query="critérios",
                answer="Os critérios são...",
                provider="OpenAI",
                model="gpt-4o-mini",
                chunks_used=len(result),
            )

            assert stored.success is True

    def test_to_openai_tool_unaffected(self, vg):
        """smart_search não afeta function calling tools."""
        tool = vg.to_openai_tool()
        assert tool["type"] == "function"
