"""Testes para smart_search() — endpoint premium MOC v4."""

import pytest
import json
from unittest.mock import patch, MagicMock
from vectorgov import VectorGov, TierError, ValidationError, SearchResult


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

    def test_invalid_top_k_raises(self, vg):
        with pytest.raises(ValidationError, match="top_k"):
            vg.smart_search("query válida", top_k=0)

        with pytest.raises(ValidationError, match="top_k"):
            vg.smart_search("query válida", top_k=51)


class TestSmartSearchRequest:
    """Testes de construção do request."""

    @patch.object(VectorGov, '_parse_search_response')
    def test_calls_correct_endpoint(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query de teste")
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "/sdk/smart-search"

    @patch.object(VectorGov, '_parse_search_response')
    def test_timeout_120s(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query de teste")
            _, kwargs = mock_post.call_args
            assert kwargs.get("timeout") == 120

    @patch.object(VectorGov, '_parse_search_response')
    def test_no_mode_in_request(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query de teste")
            _, kwargs = mock_post.call_args
            request_data = kwargs.get("data")
            # mode não deve estar no request
            if isinstance(request_data, dict):
                assert "mode" not in request_data
                assert "use_hyde" not in request_data
                assert "use_reranker" not in request_data
                assert "use_cache" not in request_data

    @patch.object(VectorGov, '_parse_search_response')
    def test_expand_citations_passed(self, mock_parse, vg):
        mock_parse.return_value = MagicMock()
        with patch.object(vg._http, 'post', return_value={}) as mock_post:
            vg.smart_search("query", expand_citations=True, citation_expansion_top_n=5)
            _, kwargs = mock_post.call_args
            request_data = kwargs.get("data")
            if isinstance(request_data, dict):
                assert request_data["expand_citations"] is True
                assert request_data["citation_expansion_top_n"] == 5


class TestSmartSearchResponse:
    """Testes de parsing da resposta."""

    def test_returns_search_result(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios de julgamento")
            assert isinstance(result, SearchResult)

    def test_mode_is_smart(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios de julgamento")
            assert result.mode == "smart"

    def test_hits_parsed(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios de julgamento")
            assert len(result.hits) == 2
            assert result.hits[0].score == 0.972
            assert "Art. 33" in result.hits[0].source

    def test_curadoria_fields(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios de julgamento")
            # Segundo hit tem curadoria
            assert result.hits[1].nota_especialista is not None
            assert result.hits[1].jurisprudencia_tcu is not None
            assert result.hits[1].acordao_tcu_link is not None

    def test_to_context_works(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            context = result.to_context()
            assert "Art. 33" in context

    def test_to_messages_works(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            messages = result.to_messages("Quais os critérios?")
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    def test_query_id_preserved(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            assert result.query_id.startswith("ss_")

    def test_cached_always_false(self, vg, smart_response):
        with patch.object(vg._http, 'post', return_value=smart_response):
            result = vg.smart_search("critérios")
            assert result.cached is False


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
        # Tool continua apontando para search, não smart_search
