"""
Testes para o cliente VectorGov.
"""

import pytest
from unittest.mock import patch, MagicMock

from vectorgov import VectorGov, SearchMode
from vectorgov.exceptions import AuthError, ValidationError


class TestVectorGovInit:
    """Testes de inicialização do cliente."""

    def test_init_with_api_key(self):
        """Deve inicializar com API key válida."""
        vg = VectorGov(api_key="vg_test_key")
        assert vg._api_key == "vg_test_key"

    def test_init_without_api_key_raises_error(self):
        """Deve levantar erro sem API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthError) as exc_info:
                VectorGov()
            assert "API key não fornecida" in str(exc_info.value)

    def test_init_with_invalid_api_key_format(self):
        """Deve levantar erro com formato inválido."""
        with pytest.raises(AuthError) as exc_info:
            VectorGov(api_key="invalid_key")
        assert "formato" in str(exc_info.value).lower()

    def test_init_with_env_var(self):
        """Deve usar variável de ambiente."""
        with patch.dict("os.environ", {"VECTORGOV_API_KEY": "vg_env_key"}):
            vg = VectorGov()
            assert vg._api_key == "vg_env_key"

    def test_init_with_custom_config(self):
        """Deve aceitar configurações customizadas."""
        vg = VectorGov(
            api_key="vg_test",
            timeout=60,
            default_top_k=10,
            default_mode="precise",
        )
        assert vg._config.timeout == 60
        assert vg._config.default_top_k == 10
        assert vg._config.default_mode == SearchMode.PRECISE


class TestSearch:
    """Testes do método search()."""

    @pytest.fixture
    def vg(self):
        """Cliente VectorGov para testes."""
        return VectorGov(api_key="vg_test")

    def test_search_validates_empty_query(self, vg):
        """Deve validar query vazia."""
        with pytest.raises(ValidationError) as exc_info:
            vg.search("")
        assert "query" in str(exc_info.value).lower()

    def test_search_validates_short_query(self, vg):
        """Deve validar query muito curta."""
        with pytest.raises(ValidationError) as exc_info:
            vg.search("ab")
        assert "3 caracteres" in str(exc_info.value)

    def test_search_validates_top_k_range(self, vg):
        """Deve validar range de top_k."""
        with pytest.raises(ValidationError):
            vg.search("teste", top_k=0)

        with pytest.raises(ValidationError):
            vg.search("teste", top_k=25)

    def test_search_validates_mode(self, vg):
        """Deve validar modo inválido."""
        with pytest.raises(ValidationError) as exc_info:
            vg.search("teste", mode="invalid")
        assert "modo" in str(exc_info.value).lower()

    @patch("vectorgov.client.HTTPClient")
    def test_search_calls_api(self, mock_http_class, vg):
        """Deve chamar a API corretamente."""
        mock_http = MagicMock()
        mock_http.post.return_value = {
            "hits": [],
            "total": 0,
            "latency_ms": 100,
            "cached": False,
            "query_id": "test-123",
        }
        vg._http = mock_http

        results = vg.search("teste")

        mock_http.post.assert_called_once()
        call_args = mock_http.post.call_args
        assert call_args[0][0] == "/sdk/search"
        assert call_args[1]["data"]["query"] == "teste"


class TestSearchResult:
    """Testes do SearchResult."""

    @pytest.fixture
    def mock_results(self):
        """Resultado de busca mockado."""
        from vectorgov.models import SearchResult, Hit, Metadata

        hits = [
            Hit(
                text="Texto do artigo 1",
                score=0.95,
                source="Lei 14.133/2021, Art. 33",
                metadata=Metadata(
                    document_type="lei",
                    document_number="14133",
                    year=2021,
                    article="33",
                ),
            ),
            Hit(
                text="Texto do artigo 2",
                score=0.85,
                source="Lei 14.133/2021, Art. 36",
                metadata=Metadata(
                    document_type="lei",
                    document_number="14133",
                    year=2021,
                    article="36",
                ),
            ),
        ]

        return SearchResult(
            query="teste",
            hits=hits,
            total=2,
            latency_ms=100,
            cached=False,
            query_id="test-123",
            mode="balanced",
        )

    def test_iteration(self, mock_results):
        """Deve suportar iteração."""
        count = 0
        for hit in mock_results:
            count += 1
        assert count == 2

    def test_len(self, mock_results):
        """Deve retornar quantidade de hits."""
        assert len(mock_results) == 2

    def test_indexing(self, mock_results):
        """Deve suportar indexação."""
        assert mock_results[0].score == 0.95
        assert mock_results[1].score == 0.85

    def test_to_context(self, mock_results):
        """Deve formatar contexto."""
        context = mock_results.to_context()
        assert "[1]" in context
        assert "[2]" in context
        assert "Lei 14.133/2021" in context

    def test_to_context_with_limit(self, mock_results):
        """Deve respeitar limite de caracteres."""
        context = mock_results.to_context(max_chars=50)
        assert len(context) <= 100  # margem para formatação

    def test_to_messages(self, mock_results):
        """Deve formatar mensagens."""
        messages = mock_results.to_messages("teste")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "teste" in messages[1]["content"]

    def test_to_prompt(self, mock_results):
        """Deve formatar prompt único."""
        prompt = mock_results.to_prompt("teste")
        assert "teste" in prompt
        assert "Lei 14.133/2021" in prompt


class TestSystemPrompts:
    """Testes de system prompts."""

    @pytest.fixture
    def vg(self):
        return VectorGov(api_key="vg_test")

    def test_available_prompts(self, vg):
        """Deve listar prompts disponíveis."""
        prompts = vg.available_prompts
        assert "default" in prompts
        assert "concise" in prompts
        assert "detailed" in prompts
        assert "chatbot" in prompts

    def test_get_system_prompt(self, vg):
        """Deve retornar prompt correto."""
        prompt = vg.get_system_prompt("default")
        assert len(prompt) > 0
        assert "legislação" in prompt.lower() or "jurídico" in prompt.lower()

    def test_get_invalid_prompt_returns_default(self, vg):
        """Deve retornar default para estilo inválido."""
        prompt = vg.get_system_prompt("invalid")
        default = vg.get_system_prompt("default")
        assert prompt == default
