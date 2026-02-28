"""
Testes do LookupResult — Seção 8.5 da spec.

Valida XML, schema, messages e markdown do LookupResult
usando fixtures JSON reais da API.
"""

class TestLookupXmlData:
    """LookupResult.to_xml(level='data')"""

    def test_has_hierarquia(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        assert "<hierarquia_normativa" in xml

    def test_has_artigo_pai(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        assert "<artigo_pai" in xml

    def test_has_dispositivo_principal(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        assert "<dispositivo_principal" in xml

    def test_has_irmaos(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        assert "<dispositivos_irmaos" in xml

    def test_irmao_atual_marcado(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        assert 'atual="true"' in xml

    def test_lookup_endpoint_in_root(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        # Implementação usa endpoint="lookup" (não tipo="lookup")
        assert 'endpoint="lookup"' in xml

    def test_no_base_normativa(self, lookup_result):
        """Lookup não tem <base_normativa> — tem <hierarquia_normativa>."""
        xml = lookup_result.to_xml(level="data")
        assert "<base_normativa>" not in xml

    def test_no_contexto_normativo(self, lookup_result):
        xml = lookup_result.to_xml(level="data")
        assert "<contexto_normativo>" not in xml


class TestLookupXmlFull:
    """LookupResult.to_xml(level='full')"""

    def test_has_full_instructions(self, lookup_result):
        xml = lookup_result.to_xml(level="full")
        assert "<instrucoes_completas>" in xml

    def test_has_contrato_with_ids(self, lookup_result):
        xml = lookup_result.to_xml(level="full")
        assert "<contrato_resposta>" in xml
        assert "<dispositivos_autorizados>" in xml


class TestLookupSchema:
    """LookupResult.to_response_schema()"""

    def test_schema_not_none(self, lookup_result):
        """Lookup tem pelo menos o match → schema não é None."""
        assert lookup_result.to_response_schema() is not None

    def test_schema_has_match_id(self, lookup_result, lookup_raw):
        schema = lookup_result.to_response_schema()
        fund_items = schema["schema"]["properties"]["fundamentacao"]["items"]
        enum_ids = fund_items["properties"]["dispositivo_id"]["enum"]
        match_id = lookup_raw["match"]["span_id"]
        assert match_id in enum_ids

    def test_schema_has_sibling_ids(self, lookup_result, lookup_raw):
        schema = lookup_result.to_response_schema()
        fund_items = schema["schema"]["properties"]["fundamentacao"]["items"]
        enum_ids = fund_items["properties"]["dispositivo_id"]["enum"]
        for sib in lookup_raw.get("siblings", []):
            assert sib["span_id"] in enum_ids


class TestLookupMessages:
    """LookupResult.to_messages()"""

    def test_separates_system_user(self, lookup_result):
        msgs = lookup_result.to_messages("Art. 18, §2º", level="full")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"


class TestLookupMarkdown:
    """LookupResult.to_markdown()"""

    def test_has_dispositivo_consultado(self, lookup_result):
        md = lookup_result.to_markdown()
        assert "Dispositivo" in md or "dispositivo" in md.lower()

    def test_no_xml_tags(self, lookup_result):
        md = lookup_result.to_markdown()
        assert "<vectorgov" not in md
        assert "<hierarquia" not in md
