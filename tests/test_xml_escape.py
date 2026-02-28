"""
Testes de escape XML — Seção 8.6 da spec.

Valida a função escape_xml() para caracteres especiais.
"""

from vectorgov.payload import escape_xml


class TestEscapeXml:
    """Escape de caracteres especiais para XML válido."""

    def test_ampersand(self):
        assert escape_xml("art. 1º & §2º") == "art. 1º &amp; §2º"

    def test_less_than(self):
        assert escape_xml("valor < R$100") == "valor &lt; R$100"

    def test_greater_than(self):
        assert escape_xml("valor > R$50") == "valor &gt; R$50"

    def test_quotes(self):
        result = escape_xml('O "texto" legal')
        assert "&quot;" in result

    def test_no_double_escaping(self):
        """Entidade já escapada não deve ser re-escapada (& → &amp; mas não &amp;amp;)."""
        text = "Art. 4&ordm; da IN 65/2021"
        escaped = escape_xml(text)
        assert "&amp;ordm;" in escaped
        assert "&amp;amp;" not in escaped

    def test_empty_string(self):
        assert escape_xml("") == ""

    def test_none_returns_empty(self):
        assert escape_xml(None) == ""
