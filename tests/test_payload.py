"""
Testes para o módulo payload (XML knowledge_package, Markdown, JSON Schema).
"""

import xml.etree.ElementTree as ET
import pytest

from vectorgov.models import (
    SearchResult,
    SmartSearchResult,
    BaseResult,
    Hit,
    Metadata,
)


# =============================================================================
# FIXTURES
# =============================================================================


def _make_hit(
    text="Art. 33. Os critérios de julgamento...",
    score=0.9,
    source="Lei 14.133/2021, Art. 33",
    doc_type="lei",
    doc_num="14133",
    year=2021,
    article="33",
    paragraph=None,
    item=None,
    device_type=None,
    chunk_id=None,
    nota=None,
    juris=None,
    acordao_key=None,
    acordao_link=None,
    page_number=None,
    canonical_hash=None,
    canonical_start=None,
    origin_type=None,
    origin_reference=None,
) -> Hit:
    if chunk_id is None:
        chunk_id = f"{doc_type.upper()}-{doc_num}-{year}#ART-{article}"
    return Hit(
        text=text,
        score=score,
        source=source,
        metadata=Metadata(
            document_type=doc_type,
            document_number=doc_num,
            year=year,
            article=article,
            paragraph=paragraph,
            item=item,
            device_type=device_type,
        ),
        chunk_id=chunk_id,
        nota_especialista=nota,
        jurisprudencia_tcu=juris,
        acordao_tcu_key=acordao_key,
        acordao_tcu_link=acordao_link,
        page_number=page_number,
        canonical_hash=canonical_hash,
        canonical_start=canonical_start,
        origin_type=origin_type,
        origin_reference=origin_reference,
    )


def _make_result(
    hits=None,
    expanded=None,
    expansion_stats=None,
    query="Quais os critérios de julgamento?",
    raw_response=None,
) -> SearchResult:
    if hits is None:
        hits = [
            _make_hit(),
            _make_hit(
                text="Art. 34. O julgamento por menor preço...",
                score=0.78,
                source="Lei 14.133/2021, Art. 34",
                article="34",
            ),
        ]
    return SearchResult(
        query=query,
        hits=hits,
        total=len(hits),
        latency_ms=150,
        cached=False,
        query_id="q-test-001",
        mode="balanced",
        expanded_chunks=expanded or [],
        expansion_stats=expansion_stats,
        _raw_response=raw_response,
    )


def _make_expanded_chunk() -> dict:
    return {
        "chunk_id": "LEI-14133-2021#ART-018",
        "node_id": "leis:LEI-14133-2021#ART-018",
        "text": "Art. 18. A fase preparatória do processo...",
        "document_id": "LEI-14133-2021",
        "span_id": "ART-018",
        "device_type": "article",
        "source_chunk_id": "LEI-14133-2021#ART-033",
        "source_citation_raw": "art. 18 da Lei 14.133",
        "hop": 1,
        "relacao": "citacao",
        "frequency": 0,
        "paths": [],
        "origin_type": "self",
    }


def _make_expansion_stats() -> dict:
    return {
        "expanded_chunks_count": 1,
        "citations_scanned_count": 3,
        "citations_resolved_count": 2,
        "expansion_time_ms": 45.0,
    }


# =============================================================================
# TESTES to_xml() — SCHEMA vectorgov_knowledge_package
# =============================================================================


class TestToXml:
    def test_root_element(self):
        """Root deve ser <vectorgov_knowledge_package version='1.0'>."""
        r = _make_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("version") == "1.0"

    def test_consulta_section(self):
        """Seção 1: <consulta> sempre presente com query e confiança."""
        r = _make_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        consulta = root.find("consulta")
        assert consulta is not None
        assert consulta.find("query_original").text == "Quais os critérios de julgamento?"
        assert consulta.find("query_interpretada").text == "Quais os critérios de julgamento?"

        conf = float(consulta.find("confianca_global").text)
        assert 0.0 <= conf <= 1.0

        assert consulta.find("estrategia").text == "balanced"

    def test_consulta_query_interpretada_from_raw(self):
        """query_interpretada usa _raw_response quando disponível."""
        raw = {
            "query_interpretation": {
                "rewritten_query": "Critérios de julgamento em licitações",
            }
        }
        r = _make_result(raw_response=raw)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        qi = root.find("consulta/query_interpretada").text
        assert qi == "Critérios de julgamento em licitações"

    def test_base_normativa_section(self):
        """Seção 2: <base_normativa> com <fonte> agrupada."""
        r = _make_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        base = root.find("base_normativa")
        assert base is not None

        # Ambos hits são da mesma lei → uma única <fonte>
        fontes = base.findall("fonte")
        assert len(fontes) == 1
        assert fontes[0].get("lei") == "14133/2021"
        assert fontes[0].get("tipo") == "LEI"
        assert fontes[0].get("relevancia") == "direta"

        # 2 dispositivos dentro da fonte
        disps = fontes[0].findall("dispositivo")
        assert len(disps) == 2

    def test_base_normativa_grouping_multiple_sources(self):
        """Regra 3: hits de fontes diferentes → múltiplas <fonte>."""
        hits = [
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="33"),
            _make_hit(doc_type="in", doc_num="65", year=2021, article="5",
                      source="IN 65/2021, Art. 5", chunk_id="IN-65-2021#ART-005"),
        ]
        r = _make_result(hits=hits)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        fontes = root.findall("base_normativa/fonte")
        assert len(fontes) == 2

        tipos = {f.get("tipo") for f in fontes}
        assert "LEI" in tipos
        assert "IN" in tipos

    def test_base_normativa_ordering_within_fonte(self):
        """Regra 4: dentro de cada <fonte>, dispositivos ordenados por score decrescente."""
        hits = [
            _make_hit(score=0.7, article="34"),
            _make_hit(score=0.95, article="33"),
            _make_hit(score=0.8, article="36"),
        ]
        r = _make_result(hits=hits)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disps = root.findall("base_normativa/fonte/dispositivo")
        scores = [float(d.get("score")) for d in disps]
        assert scores == sorted(scores, reverse=True)

    def test_dispositivo_attributes(self):
        """<dispositivo> tem atributos corretos: id, tipo, artigo, score, evidence_url."""
        hit = _make_hit(article="33", chunk_id="LEI-14133-2021#INC-033-III",
                        item="III")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("id") == "INC-033-III"
        assert disp.get("tipo") == "inciso"
        assert disp.get("artigo") == "33"
        assert disp.get("score") == "0.9000"
        assert "/api/v1/evidence/" in disp.get("evidence_url")

    def test_dispositivo_tipo_paragrafo(self):
        """Tipo 'paragrafo' quando metadata.paragraph está presente."""
        hit = _make_hit(paragraph="1", chunk_id="LEI-14133-2021#PAR-033-1")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("tipo") == "paragrafo"

    def test_dispositivo_tipo_artigo(self):
        """Tipo 'artigo' quando apenas metadata.article."""
        hit = _make_hit(article="33")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("tipo") == "artigo"

    def test_contexto_normativo_with_expanded(self):
        """Seção 3: <contexto_normativo> presente quando há expanded_chunks."""
        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        ctx = root.find("contexto_normativo")
        assert ctx is not None

        disp_rel = ctx.find("dispositivo_relacionado")
        assert disp_rel is not None
        assert disp_rel.get("id") == "ART-018"
        assert disp_rel.get("lei") == "LEI-14133-2021"
        assert disp_rel.get("relacao") == "citacao"
        assert disp_rel.get("hop") == "1"
        assert "fase preparatória" in disp_rel.text

    def test_contexto_normativo_custom_hop_and_relacao(self):
        """Seção 3: hop e relacao vêm do expanded chunk dict."""
        ec = _make_expanded_chunk()
        ec["hop"] = 2
        ec["relacao"] = "regulamenta"
        r = _make_result(expanded=[ec])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp_rel = root.find("contexto_normativo/dispositivo_relacionado")
        assert disp_rel.get("hop") == "2"
        assert disp_rel.get("relacao") == "regulamenta"

    def test_contexto_normativo_omitted_without_expanded(self):
        """Regra 1: <contexto_normativo> omitido se sem expanded_chunks."""
        r = _make_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.find("contexto_normativo") is None

    def test_level_data_all_sections_no_instrucoes(self):
        """Level 'data': todas as 7 seções, sem instrucoes."""
        hit = _make_hit(nota="Nota test", juris="Jurisprudência test")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        # Sem instruções (nem instrucoes nem instrucoes_completas)
        assert root.find("instrucoes") is None
        assert root.find("instrucoes_completas") is None

        # Todas as 7 seções de dados estão presentes
        assert root.find("consulta") is not None
        assert root.find("base_normativa") is not None
        assert root.find("notas_especialista") is not None
        assert root.find("jurisprudencia") is not None
        assert root.find("trilha_verificavel") is not None
        assert root.find("metadados") is not None

    def test_root_element_has_level_attribute(self):
        """Root element tem atributo level correspondente ao nível solicitado."""
        r = _make_result()
        for level in ("data", "instructions", "full"):
            xml = r.to_xml(level)
            root = ET.fromstring(xml)
            assert root.get("level") == level

    def test_level_instructions_has_instrucoes(self):
        """Level 'instructions': <instrucoes> com 7 regras flat (Seção 6.2)."""
        r = _make_result()
        xml = r.to_xml("instructions")
        root = ET.fromstring(xml)

        instrucoes = root.find("instrucoes")
        assert instrucoes is not None

        # 7 regras flat (sem nesting) — Seção 6.2 spec
        regras = instrucoes.findall("regra")
        assert len(regras) == 7

        # Sem sub-elementos aninhados (mudou na Seção 4)
        assert instrucoes.find("papel") is None
        assert instrucoes.find("regras") is None
        assert instrucoes.find("formato_resposta") is None

        # Sem instrucoes_completas
        assert root.find("instrucoes_completas") is None

        # Todas as seções de dados presentes
        assert root.find("consulta") is not None
        assert root.find("base_normativa") is not None
        assert root.find("metadados") is not None
        # trilha presente (hits têm chunk_id)
        assert root.find("trilha_verificavel") is not None

    def test_level_full_has_everything(self):
        """Level 'full': tem instrucoes_completas + todas as seções de dados."""
        hit = _make_hit(
            nota="Atenção: alterado",
            juris="TCU Acórdão 1852/2020",
            acordao_key="1852/2020",
            acordao_link="https://example.com/acordao",
        )
        r = _make_result(hits=[hit])
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        # Instrucoes_completas (NÃO instrucoes)
        assert root.find("instrucoes") is None
        ic = root.find("instrucoes_completas")
        assert ic is not None

        # Sub-seções de instrucoes_completas
        assert ic.find("papel") is not None
        assert ic.find("anti_alucinacao") is not None
        assert ic.find("formato_citacao") is not None
        assert ic.find("estrutura_resposta") is not None
        assert ic.find("modo_geracao_documento") is not None
        assert ic.find("contrato_resposta") is not None

        # Notas
        notas = root.find("notas_especialista")
        assert notas is not None
        nota = notas.find("nota")
        assert nota is not None
        assert nota.text is not None
        assert "alterado" in nota.text
        assert nota.get("dispositivo_ref") == "ART-33"

        # Jurisprudencia
        juris = root.find("jurisprudencia")
        assert juris is not None
        ac = juris.find("acordao")
        assert ac is not None
        assert ac.get("chave") == "1852/2020"
        assert ac.get("link") == "https://example.com/acordao"

        # Trilha verificável
        trilha = root.find("trilha_verificavel")
        assert trilha is not None
        ev = trilha.find("evidencia")
        assert ev is not None
        assert ev.get("dispositivo_ref") == "ART-33"
        assert "/api/v1/evidence/" in ev.get("url")

    def test_notas_omitted_when_no_notas(self):
        """Regra 1: <notas_especialista> omitida quando nenhum hit tem nota."""
        r = _make_result()  # hits sem nota
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        assert root.find("notas_especialista") is None

    def test_jurisprudencia_omitted_when_no_juris(self):
        """Regra 1: <jurisprudencia> omitida quando nenhum hit tem jurisprudência."""
        r = _make_result()  # hits sem juris
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        assert root.find("jurisprudencia") is None

    def test_metadados_section(self):
        """Seção 7: <metadados> com informações operacionais."""
        r = _make_result(expansion_stats=_make_expansion_stats())
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        meta = root.find("metadados")
        assert meta is not None
        assert meta.find("pipeline").text == "fenix"
        assert meta.find("tempo_total_ms").text == "150"
        assert meta.find("reranker").text == "true"
        assert meta.find("grafo_expandido").text == "false"
        assert meta.find("cache_hit").text == "false"
        assert meta.find("query_id").text == "q-test-001"

        # Expansion stats
        exp = meta.find("expansao")
        assert exp is not None
        assert exp.find("expandidos").text == "1"
        assert exp.find("citacoes_encontradas").text == "3"
        assert exp.find("citacoes_resolvidas").text == "2"

    def test_metadados_reranker_from_raw_response(self):
        """<reranker> extrai valor de _raw_response quando disponível."""
        r = _make_result(raw_response={"reranker": False})
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.find("metadados/reranker").text == "false"

    def test_dispositivo_artigo_consolidado(self):
        """Regra 5: device_type='article_consolidated' → tipo='artigo_consolidado'."""
        hit = _make_hit(device_type="article_consolidated", article="33")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("tipo") == "artigo_consolidado"

    def test_dispositivo_device_type_from_metadata(self):
        """Tipo deve usar metadata.device_type quando disponível."""
        hit = _make_hit(device_type="inciso", article="33")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("tipo") == "inciso"

    def test_dispositivo_origem_referencia_cruzada(self):
        """Regra 6: origin_type != 'self' → atributos origem e origem_ref."""
        hit = _make_hit(
            origin_type="referencia",
            origin_reference="Lei 14.133/2021, Art. 75",
        )
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("origem") == "referencia_cruzada"
        assert disp.get("origem_ref") == "Lei 14.133/2021, Art. 75"

    def test_dispositivo_origin_self_no_attribute(self):
        """Regra 6: origin_type='self' → sem atributo origem."""
        hit = _make_hit(origin_type="self")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("origem") is None

    def test_trilha_verificavel_pagina_and_hash(self):
        """Seção 6: <evidencia> com pagina e hash quando disponíveis."""
        hit = _make_hit(page_number=8, canonical_hash="4e59ecfba2abc123")
        r = _make_result(hits=[hit])
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        ev = root.find("trilha_verificavel/evidencia")
        assert ev.get("pagina") == "8"
        assert ev.get("hash") == "4e59ecfba2abc123"

    def test_trilha_verificavel_no_pagina_when_missing(self):
        """<evidencia> sem pagina/hash quando não disponíveis."""
        hit = _make_hit()
        r = _make_result(hits=[hit])
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        ev = root.find("trilha_verificavel/evidencia")
        assert ev.get("pagina") is None
        assert ev.get("hash") is None

    def test_empty_hits(self):
        """Sem hits: <base_normativa> não aparece, demais seções OK."""
        r = _make_result(hits=[])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        # consulta e metadados presentes
        assert root.find("consulta") is not None
        assert root.find("metadados") is not None

        # base_normativa ausente
        assert root.find("base_normativa") is None

    def test_xml_escaping(self):
        """Texto com caracteres especiais não quebra o XML (Regra 2)."""
        hit = _make_hit(text='Art. 5º — "Seção" <especial> & obrigatória')
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")

        # Deve parsear sem erro
        root = ET.fromstring(xml)
        disp = root.find("base_normativa/fonte/dispositivo")
        assert "<especial>" in disp.text
        assert "&" in disp.text

    def test_invalid_level_raises(self):
        r = _make_result()
        with pytest.raises(ValueError, match="level inválido"):
            r.to_xml("invalid")

    def test_evidence_url_encoding(self):
        """Evidence URL deve codificar # corretamente."""
        hit = _make_hit(chunk_id="LEI-14133-2021#ART-033")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        url = disp.get("evidence_url")
        assert "%23" in url  # # codificado como %23
        assert "LEI-14133-2021" in url


# =============================================================================
# TESTES BACKWARD COMPAT — to_messages / to_prompt
# =============================================================================


class TestBackwardCompat:
    def test_to_messages_legacy(self):
        """Chamada sem level continua funcionando como antes."""
        r = _make_result()
        msgs = r.to_messages("O que é ETP?")

        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "Contexto:" in msgs[1]["content"]
        assert "O que é ETP?" in msgs[1]["content"]

    def test_to_messages_legacy_with_system(self):
        r = _make_result()
        msgs = r.to_messages("Teste", system_prompt="Custom system")

        assert msgs[0]["content"] == "Custom system"

    def test_to_messages_with_level(self):
        r = _make_result()
        msgs = r.to_messages("O que é ETP?", level="instructions")

        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

        # System deve ser XML knowledge_package
        assert "<vectorgov_knowledge_package" in msgs[0]["content"]
        assert "<instrucoes>" in msgs[0]["content"]

        # User é a query pura
        assert msgs[1]["content"] == "O que é ETP?"

    def test_to_prompt_legacy(self):
        r = _make_result()
        prompt = r.to_prompt("Teste?")

        assert "Contexto:" in prompt
        assert "Teste?" in prompt
        assert "Resposta:" in prompt

    def test_to_prompt_with_level(self):
        r = _make_result()
        prompt = r.to_prompt("Teste?", level="data")

        assert "<vectorgov_knowledge_package" in prompt
        assert "Teste?" in prompt
        assert "Resposta:" in prompt


# =============================================================================
# TESTES to_dict()
# =============================================================================


class TestToDict:
    def test_to_dict_without_raw_response(self):
        """Sem _raw_response, reconstrói manualmente."""
        r = _make_result()
        d = r.to_dict()

        assert d["query"] == "Quais os critérios de julgamento?"
        assert len(d["hits"]) == 2
        assert d["hits"][0]["score"] == 0.9
        assert d["total"] == 2
        assert d["mode"] == "balanced"

    def test_to_dict_with_raw_response(self):
        """Com _raw_response, retorna cópia da resposta bruta."""
        raw = {"query": "test", "hits": [], "custom_field": 42}
        r = _make_result(raw_response=raw)
        d = r.to_dict()

        assert d["custom_field"] == 42
        assert d["query"] == "test"

        # Deve ser uma cópia, não a mesma referência
        assert d is not raw


# =============================================================================
# TESTES to_markdown()
# =============================================================================


class TestToMarkdown:
    def test_basic_markdown(self):
        r = _make_result()
        md = r.to_markdown()

        assert "# Resultados para:" in md
        assert "## Dispositivos" in md
        assert "Lei 14.133/2021, Art. 33" in md
        assert "score: 0.900" in md

    def test_markdown_empty_hits(self):
        r = _make_result(hits=[])
        md = r.to_markdown()

        assert "Nenhum resultado encontrado" in md

    def test_markdown_with_curadoria(self):
        hit = _make_hit(
            nota="Nota importante",
            juris="Acórdão 1852/2020",
            acordao_link="https://example.com",
        )
        r = _make_result(hits=[hit])
        md = r.to_markdown()

        assert "Nota do Especialista" in md
        assert "Nota importante" in md
        assert "Jurisprudência TCU" in md
        assert "[link]" in md

    def test_markdown_with_expanded(self):
        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec], expansion_stats=_make_expansion_stats())
        md = r.to_markdown()

        assert "Trechos Citados" in md
        assert "LEI-14133-2021" in md
        assert "ART-018" in md
        assert "Citado por" in md


# =============================================================================
# TESTES to_response_schema()
# =============================================================================


class TestResponseSchema:
    def test_basic_schema_wrapper(self):
        """Schema retorna wrapper {name, strict, schema}."""
        r = _make_result()
        wrapper = r.to_response_schema()

        assert wrapper is not None
        assert wrapper["name"] == "resposta_juridica_vectorgov"
        assert wrapper["strict"] is True
        assert "schema" in wrapper

        schema = wrapper["schema"]
        assert schema["type"] == "object"
        assert "resposta_direta" in schema["properties"]
        assert "fundamentacao" in schema["properties"]
        assert "informacao_insuficiente" in schema["properties"]

    def test_schema_fundamentacao_array(self):
        """fundamentacao é array com dispositivo_id enum restrito a span IDs."""
        r = _make_result()
        wrapper = r.to_response_schema()
        schema = wrapper["schema"]

        fund = schema["properties"]["fundamentacao"]
        assert fund["type"] == "array"

        item_props = fund["items"]["properties"]
        assert "afirmacao" in item_props
        assert "dispositivo_id" in item_props
        assert "citacao_formatada" in item_props
        assert "evidence_link" in item_props

        # dispositivo_id enum tem span IDs (não nomes de docs)
        enum_values = item_props["dispositivo_id"]["enum"]
        assert "ART-33" in enum_values
        assert "ART-34" in enum_values

    def test_schema_nullable_fields(self):
        """observacoes_praticas e jurisprudencia_tcu sempre nullable."""
        r = _make_result()
        wrapper = r.to_response_schema()
        schema = wrapper["schema"]

        obs = schema["properties"]["observacoes_praticas"]
        assert obs["type"] == ["string", "null"]

        juris = schema["properties"]["jurisprudencia_tcu"]
        assert juris["type"] == ["string", "null"]

    def test_schema_empty_returns_none(self):
        r = _make_result(hits=[])
        schema = r.to_response_schema()
        assert schema is None

    def test_schema_compat_params_accepted(self):
        """Parâmetros include_jurisprudencia/include_observacoes aceitos sem erro."""
        r = _make_result()
        # Não devem causar erro (são no-ops agora)
        w1 = r.to_response_schema(include_jurisprudencia=True)
        w2 = r.to_response_schema(include_observacoes=True)
        assert w1 is not None
        assert w2 is not None

    def test_schema_enum_restricts_to_span_ids(self):
        """Enum de dispositivo_id usa span IDs deduplicados."""
        hits = [
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="33",
                      chunk_id="LEI-14133-2021#ART-033"),
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="34",
                      chunk_id="LEI-14133-2021#ART-034"),
            _make_hit(doc_type="in", doc_num="65", year=2021, article="5",
                      chunk_id="IN-65-2021#ART-005"),
        ]
        r = _make_result(hits=hits)
        wrapper = r.to_response_schema()
        schema = wrapper["schema"]

        enum = schema["properties"]["fundamentacao"]["items"]["properties"]["dispositivo_id"]["enum"]
        assert len(enum) == 3
        assert "ART-033" in enum
        assert "ART-034" in enum
        assert "ART-005" in enum

    def test_schema_enum_includes_expanded_chunks(self):
        """Enum inclui span IDs de expanded_chunks."""
        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        wrapper = r.to_response_schema()
        schema = wrapper["schema"]

        enum = schema["properties"]["fundamentacao"]["items"]["properties"]["dispositivo_id"]["enum"]
        assert "ART-018" in enum  # do expanded chunk
        assert "ART-33" in enum   # do hit direto

    def test_schema_dispositivos_nao_utilizados(self):
        """dispositivos_nao_utilizados tem mesmo enum que fundamentacao."""
        r = _make_result()
        wrapper = r.to_response_schema()
        schema = wrapper["schema"]

        dnu = schema["properties"]["dispositivos_nao_utilizados"]
        assert dnu["type"] == "array"
        enum = dnu["items"]["enum"]
        assert "ART-33" in enum


# =============================================================================
# TESTES to_anthropic_tool_schema()
# =============================================================================


class TestAnthropicToolSchema:
    def test_basic_tool(self):
        r = _make_result()
        tool = r.to_anthropic_tool_schema()

        assert tool is not None
        assert tool["name"] == "resposta_juridica_vectorgov"
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "fundamentacao" in tool["input_schema"]["properties"]

    def test_tool_empty_returns_none(self):
        r = _make_result(hits=[])
        tool = r.to_anthropic_tool_schema()
        assert tool is None


# =============================================================================
# TESTES Properties
# =============================================================================


class TestProperties:
    def test_confidence_basic(self):
        r = _make_result()
        conf = r.confidence

        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0
        # Com scores 0.9 e 0.78, deve ser alto
        assert conf > 0.7

    def test_confidence_empty(self):
        r = _make_result(hits=[])
        assert r.confidence == 0.0

    def test_confidence_single_hit_penalty(self):
        """Hit único recebe penalidade de 20%."""
        r_single = _make_result(hits=[_make_hit(score=0.9)])
        r_multi = _make_result(hits=[_make_hit(score=0.9), _make_hit(score=0.9)])

        assert r_single.confidence < r_multi.confidence

    def test_confidence_high_top_bonus(self):
        """Top hit > 0.9 recebe bonus de 5%."""
        hit_high = _make_hit(score=0.95)
        hit_med = _make_hit(score=0.85)
        r_high = _make_result(hits=[hit_high, _make_hit(score=0.5)])
        r_med = _make_result(hits=[hit_med, _make_hit(score=0.5)])

        # O bonus do 0.95 deve refletir
        assert r_high.confidence >= r_med.confidence

    def test_normative_trail(self):
        hits = [
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="33"),
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="34"),
            _make_hit(doc_type="in", doc_num="65", year=2021, article="5"),
        ]
        r = _make_result(hits=hits)
        trail = r.normative_trail

        assert isinstance(trail, list)
        assert len(trail) == 2  # Deduplicado
        assert "LEI 14133/2021" in trail
        assert "IN 65/2021" in trail

    def test_normative_trail_empty(self):
        r = _make_result(hits=[])
        assert r.normative_trail == []

    def test_query_interpretation_from_raw(self):
        raw = {
            "query_interpretation": {
                "original_query": "ETP",
                "rewritten_query": "Estudo Técnico Preliminar",
            }
        }
        r = _make_result(raw_response=raw)
        qi = r.query_interpretation

        assert qi["original_query"] == "ETP"
        assert qi["rewritten_query"] == "Estudo Técnico Preliminar"

    def test_query_interpretation_fallback(self):
        r = _make_result()
        qi = r.query_interpretation

        assert qi["original_query"] == "Quais os critérios de julgamento?"


# =============================================================================
# TESTES INTEGRAÇÃO — payload direto
# =============================================================================


class TestPayloadDirect:
    """Testes chamando funções de payload.py diretamente."""

    def test_build_xml_is_valid_xml(self):
        from vectorgov.payload import build_xml

        r = _make_result()
        for level in ("data", "instructions", "full"):
            xml = build_xml(r, level=level)
            # Deve parsear sem erro
            root = ET.fromstring(xml)
            assert root.tag == "vectorgov_knowledge_package"

    def test_build_prompt_xml(self):
        from vectorgov.payload import build_prompt_xml

        r = _make_result()
        prompt = build_prompt_xml(r, query="Teste?", level="data")

        assert "<vectorgov_knowledge_package" in prompt
        assert "Teste?" in prompt
        assert "Resposta:" in prompt

    def test_build_messages_xml(self):
        from vectorgov.payload import build_messages_xml

        r = _make_result()
        msgs = build_messages_xml(r, query="Q?", level="full")

        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "<vectorgov_knowledge_package" in msgs[0]["content"]
        assert msgs[1]["content"] == "Q?"

    def test_build_markdown(self):
        from vectorgov.payload import build_markdown

        r = _make_result()
        md = build_markdown(r)
        assert "# Resultados para:" in md

    def test_calculate_confidence_zero_scores(self):
        from vectorgov.payload import _calculate_confidence

        r = _make_result(hits=[_make_hit(score=0.0)])
        assert _calculate_confidence(r) == 0.0

    def test_extract_normative_trail_preserves_order(self):
        from vectorgov.payload import _extract_normative_trail

        hits = [
            _make_hit(doc_type="in", doc_num="65", year=2021, article="1"),
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="33"),
        ]
        r = _make_result(hits=hits)
        trail = _extract_normative_trail(r)

        assert trail[0] == "IN 65/2021"
        assert trail[1] == "LEI 14133/2021"

    def test_extract_span_id(self):
        from vectorgov.payload import _extract_span_id

        assert _extract_span_id("LEI-14133-2021#ART-033") == "ART-033"
        assert _extract_span_id("LEI-14133-2021#INC-033-III") == "INC-033-III"
        assert _extract_span_id("") == ""
        assert _extract_span_id("no-hash") == "no-hash"

    def test_group_hits_by_source(self):
        from vectorgov.payload import _group_hits_by_source

        hits = [
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="33"),
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="34"),
            _make_hit(doc_type="in", doc_num="65", year=2021, article="5"),
        ]
        groups = _group_hits_by_source(hits)

        assert len(groups) == 2
        keys = list(groups.keys())
        assert groups[keys[0]]["tipo"] == "LEI"
        assert len(groups[keys[0]]["hits"]) == 2
        assert groups[keys[1]]["tipo"] == "IN"
        assert len(groups[keys[1]]["hits"]) == 1


# =============================================================================
# TESTES REGRAS DE SERIALIZAÇÃO
# =============================================================================


class TestSerializationRules:
    """Testes específicos para as 6 regras de serialização da Seção 3."""

    def test_rule1_empty_sections_omitted(self):
        """Regra 1: Tags vazias são omitidas."""
        r = _make_result()  # Sem notas, sem juris, sem expanded
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        # Seções condicionais ausentes
        assert root.find("notas_especialista") is None
        assert root.find("jurisprudencia") is None
        assert root.find("contexto_normativo") is None

    def test_rule2_xml_escaping_special_chars(self):
        """Regra 2: Texto escapado corretamente (via ET, não .replace())."""
        hit = _make_hit(text='§ 1º — Texto com <tags>, "aspas" & entidades')
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")

        # Parse não deve falhar
        root = ET.fromstring(xml)
        texto = root.find("base_normativa/fonte/dispositivo").text
        assert "<tags>" in texto
        assert '"aspas"' in texto
        assert "&" in texto

    def test_rule3_grouping_by_fonte(self):
        """Regra 3: Dispositivos da mesma lei agrupados na mesma <fonte>."""
        hits = [
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="33"),
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="34", score=0.8),
            _make_hit(doc_type="lei", doc_num="14133", year=2021, article="36", score=0.7),
        ]
        r = _make_result(hits=hits)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        # Deve ter apenas 1 <fonte> (mesma lei)
        fontes = root.findall("base_normativa/fonte")
        assert len(fontes) == 1

        # Com 3 dispositivos dentro
        disps = fontes[0].findall("dispositivo")
        assert len(disps) == 3

    def test_rule4_ordering_by_score_desc(self):
        """Regra 4: Dentro de cada fonte, score decrescente."""
        hits = [
            _make_hit(score=0.6, article="36"),
            _make_hit(score=0.9, article="33"),
            _make_hit(score=0.75, article="34"),
        ]
        r = _make_result(hits=hits)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disps = root.findall("base_normativa/fonte/dispositivo")
        scores = [float(d.get("score")) for d in disps]
        assert scores == [0.9, 0.75, 0.6]

    def test_rule4_tiebreak_by_canonical_start(self):
        """Regra 4: Em empate de score, desempata por canonical_start crescente."""
        hits = [
            _make_hit(score=0.9, article="36", canonical_start=5000,
                      chunk_id="LEI-14133-2021#ART-036"),
            _make_hit(score=0.9, article="33", canonical_start=1000,
                      chunk_id="LEI-14133-2021#ART-033"),
            _make_hit(score=0.9, article="34", canonical_start=3000,
                      chunk_id="LEI-14133-2021#ART-034"),
        ]
        r = _make_result(hits=hits)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disps = root.findall("base_normativa/fonte/dispositivo")
        ids = [d.get("id") for d in disps]
        # Mesmo score → ordenados por canonical_start crescente
        assert ids == ["ART-033", "ART-034", "ART-036"]

    def test_rule5_separation_direct_vs_graph(self):
        """Regra 5: Evidência direta em base_normativa, grafo em contexto_normativo."""
        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        # base_normativa tem dispositivos diretos
        base = root.find("base_normativa")
        assert base is not None
        assert base.findall("fonte/dispositivo") != []

        # contexto_normativo tem dispositivos expandidos
        ctx = root.find("contexto_normativo")
        assert ctx is not None
        assert ctx.findall("dispositivo_relacionado") != []

        # Não devem misturar
        assert base.find("dispositivo_relacionado") is None
        assert ctx.find("fonte") is None

    def test_rule5_artigo_consolidado(self):
        """Regra 5: article_consolidated marcado como artigo_consolidado."""
        hit = _make_hit(device_type="article_consolidated")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("tipo") == "artigo_consolidado"

    def test_rule6_provenance_marking(self):
        """Regra 6: origin_type != 'self' gera atributos origem/origem_ref."""
        hit = _make_hit(
            origin_type="referencia_cruzada",
            origin_reference="Lei 14.133/2021, Art. 75",
        )
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("origem") == "referencia_cruzada"
        assert disp.get("origem_ref") == "Lei 14.133/2021, Art. 75"

    def test_rule6_self_origin_no_attributes(self):
        """Regra 6: origin_type='self' não adiciona atributos de proveniência."""
        hit = _make_hit(origin_type="self")
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("origem") is None
        assert disp.get("origem_ref") is None


# =============================================================================
# TESTES SEÇÃO 4 — TRÊS NÍVEIS DE INSTRUÇÃO
# =============================================================================


class TestInstructionLevels:
    """Testes específicos para a Seção 4 da spec (3 níveis de instrução)."""

    def test_instrucoes_before_data_sections(self):
        """Instruções vêm ANTES das seções de dados no XML."""
        r = _make_result()
        xml = r.to_xml("instructions")
        root = ET.fromstring(xml)

        children = list(root)
        tag_order = [c.tag for c in children]

        # instrucoes deve vir antes de consulta
        idx_instrucoes = tag_order.index("instrucoes")
        idx_consulta = tag_order.index("consulta")
        assert idx_instrucoes < idx_consulta

    def test_instrucoes_completas_before_data_sections(self):
        """instrucoes_completas vêm ANTES das seções de dados no XML (level full)."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        children = list(root)
        tag_order = [c.tag for c in children]

        idx_ic = tag_order.index("instrucoes_completas")
        idx_consulta = tag_order.index("consulta")
        assert idx_ic < idx_consulta

    def test_instrucoes_regra_content(self):
        """Cada <regra> em <instrucoes> tem conteúdo textual (7 regras, Seção 6.2)."""
        r = _make_result()
        xml = r.to_xml("instructions")
        root = ET.fromstring(xml)

        regras = root.findall("instrucoes/regra")
        assert len(regras) == 7
        for regra in regras:
            assert regra.text is not None
            assert len(regra.text) > 10

    def test_instrucoes_completas_anti_alucinacao(self):
        """<anti_alucinacao> tem regras com atributo prioridade."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        aa = root.find("instrucoes_completas/anti_alucinacao")
        assert aa is not None

        regras = aa.findall("regra")
        assert len(regras) == 3

        # Pelo menos 2 regras com prioridade "critica"
        criticas = [r for r in regras if r.get("prioridade") == "critica"]
        assert len(criticas) == 2

    def test_instrucoes_completas_formato_citacao(self):
        """<formato_citacao> tem regras de formato."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        fc = root.find("instrucoes_completas/formato_citacao")
        assert fc is not None
        regras = fc.findall("regra")
        assert len(regras) == 4

    def test_instrucoes_completas_estrutura_resposta(self):
        """<estrutura_resposta> tem regras de estrutura."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        er = root.find("instrucoes_completas/estrutura_resposta")
        assert er is not None
        regras = er.findall("regra")
        assert len(regras) == 5

    def test_instrucoes_completas_modo_geracao_documento(self):
        """<modo_geracao_documento> tem atributo condition e regras."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        mgd = root.find("instrucoes_completas/modo_geracao_documento")
        assert mgd is not None
        assert mgd.get("condition") is not None
        regras = mgd.findall("regra")
        assert len(regras) == 3

    def test_contrato_resposta_dispositivos_autorizados(self):
        """<contrato_resposta> contém whitelist de IDs autorizados."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        cr = root.find("instrucoes_completas/contrato_resposta")
        assert cr is not None

        da = cr.find("dispositivos_autorizados")
        assert da is not None
        assert da.text is not None
        assert "ART-33" in da.text
        assert "ART-34" in da.text

    def test_contrato_resposta_mapa_evidencias(self):
        """<mapa_evidencias> mapeia span_id → evidence_url."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        me = root.find("instrucoes_completas/contrato_resposta/mapa_evidencias")
        assert me is not None
        assert me.text is not None
        assert "ART-33" in me.text
        assert "/api/v1/evidence/" in me.text

    def test_contrato_resposta_formato_obrigatorio(self):
        """<formato_obrigatorio> contém instruções de formato."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        fo = root.find("instrucoes_completas/contrato_resposta/formato_obrigatorio")
        assert fo is not None
        assert fo.text is not None
        assert "RESPOSTA DIRETA" in fo.text

    def test_contrato_resposta_verificacao_final(self):
        """<verificacao_final> contém checklist."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        vf = root.find("instrucoes_completas/contrato_resposta/verificacao_final")
        assert vf is not None
        assert vf.text is not None
        assert "Antes de enviar" in vf.text

    def test_contrato_includes_expanded_ids(self):
        """Whitelist inclui IDs de expanded_chunks."""
        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        da = root.find("instrucoes_completas/contrato_resposta/dispositivos_autorizados")
        assert da is not None
        assert da.text is not None
        assert "ART-018" in da.text  # do expanded chunk
        assert "ART-33" in da.text   # do hit direto

    def test_mapa_evidencias_includes_expanded(self):
        """Mapa de evidências inclui URLs de expanded_chunks."""
        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        me = root.find("instrucoes_completas/contrato_resposta/mapa_evidencias")
        assert me is not None
        assert me.text is not None
        assert "ART-018" in me.text

    def test_empty_hits_no_contrato_sections(self):
        """Sem hits, contrato_resposta não tem dispositivos_autorizados nem mapa."""
        r = _make_result(hits=[])
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        cr = root.find("instrucoes_completas/contrato_resposta")
        assert cr is not None
        assert cr.find("formato_obrigatorio") is not None
        assert cr.find("verificacao_final") is not None
        # Sem dispositivos
        assert cr.find("dispositivos_autorizados") is None
        assert cr.find("mapa_evidencias") is None


class TestCollectAuthorizedIds:
    """Testes para _collect_authorized_ids."""

    def test_basic_collection(self):
        from vectorgov.payload import _collect_authorized_ids

        r = _make_result()
        ids, emap = _collect_authorized_ids(r)

        assert "ART-33" in ids
        assert "ART-34" in ids
        assert len(ids) == 2
        assert "ART-33" in emap
        assert "/api/v1/evidence/" in emap["ART-33"]

    def test_deduplication(self):
        from vectorgov.payload import _collect_authorized_ids

        hits = [
            _make_hit(article="33", chunk_id="LEI-14133-2021#ART-033"),
            _make_hit(article="33", chunk_id="LEI-14133-2021#ART-033"),  # duplicata
        ]
        r = _make_result(hits=hits)
        ids, _ = _collect_authorized_ids(r)

        assert len(ids) == 1
        assert ids[0] == "ART-033"

    def test_with_expanded(self):
        from vectorgov.payload import _collect_authorized_ids

        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        ids, emap = _collect_authorized_ids(r)

        assert "ART-018" in ids
        assert "ART-018" in emap

    def test_empty_result(self):
        from vectorgov.payload import _collect_authorized_ids

        r = _make_result(hits=[])
        ids, emap = _collect_authorized_ids(r)

        assert ids == []
        assert emap == {}


# =============================================================================
# FIXTURES — Hybrid & Lookup
# =============================================================================


def _make_hybrid_hit(
    text="Art. 33. Os critérios de julgamento...",
    score=0.9,
    source="Lei 14.133/2021, Art. 33",
    doc_type="lei",
    doc_num="14133",
    year=2021,
    article="33",
    chunk_id=None,
    stitched_text=None,
    pure_rerank_score=None,
    is_parent=False,
    is_child_of_seed=False,
    evidence_url=None,
    sha256_source=None,
) -> Hit:
    if chunk_id is None:
        chunk_id = f"{doc_type.upper()}-{doc_num}-{year}#ART-{article}"
    return Hit(
        text=text,
        score=score,
        source=source,
        metadata=Metadata(
            document_type=doc_type,
            document_number=doc_num,
            year=year,
            article=article,
        ),
        chunk_id=chunk_id,
        stitched_text=stitched_text,
        pure_rerank_score=pure_rerank_score,
        is_parent=is_parent,
        is_child_of_seed=is_child_of_seed,
        evidence_url=evidence_url,
        sha256_source=sha256_source,
    )


def _make_hybrid_expanded(
    chunk_id="LEI-14133-2021#ART-036",
    node_id="leis:LEI-14133-2021#ART-036",
    text="Art. 36. A avaliação das propostas...",
    document_id="LEI-14133-2021",
    span_id="ART-036",
    hop=1,
    frequency=5,
    paths=None,
    device_type="article",
    origin_type=None,
) -> Hit:
    return Hit(
        chunk_id=chunk_id,
        node_id=node_id,
        text=text,
        score=0.0,
        source=document_id,
        metadata=Metadata(document_type="", document_number="", year=0),
        document_id=document_id,
        span_id=span_id,
        hop=hop,
        frequency=frequency,
        paths=paths or [["ART-033", "ART-036"]],
        device_type=device_type,
        origin_type=origin_type,
    )


def _make_hybrid_result(
    hits=None,
    graph_nodes=None,
    query="Quais os critérios de julgamento?",
    confidence=0.85,
    hyde_used=True,
    docfilter_active=True,
    docfilter_detected_doc_id="LEI-14133-2021",
    query_rewrite_active=False,
    query_rewrite_clean_query=None,
    dual_lane_active=False,
    dual_lane_filtered_doc=None,
    dual_lane_from_filtered=0,
    dual_lane_from_free=0,
    stats=None,
    cached=False,
    latency_ms=200.0,
):
    from vectorgov.models import HybridResult

    if hits is None:
        hits = [
            _make_hybrid_hit(),
            _make_hybrid_hit(
                text="Art. 34. O julgamento por menor preço...",
                score=0.78,
                source="Lei 14.133/2021, Art. 34",
                article="34",
            ),
        ]
    if graph_nodes is None:
        graph_nodes = [_make_hybrid_expanded()]
    if stats is None:
        stats = {
            "timings": {
                "embedding_ms": 50,
                "search_ms": 80,
                "rerank_ms": 40,
                "graph_ms": 30,
                "total_ms": 200,
            },
            "hits_milvus": 8,
        }

    return HybridResult(
        query=query,
        hits=hits,
        graph_nodes=graph_nodes,
        stats=stats,
        confidence=confidence,
        latency_ms=latency_ms,
        hyde_used=hyde_used,
        docfilter_active=docfilter_active,
        docfilter_detected_doc_id=docfilter_detected_doc_id,
        query_rewrite_active=query_rewrite_active,
        query_rewrite_clean_query=query_rewrite_clean_query,
        dual_lane_active=dual_lane_active,
        dual_lane_filtered_doc=dual_lane_filtered_doc,
        dual_lane_from_filtered=dual_lane_from_filtered,
        dual_lane_from_free=dual_lane_from_free,
        cached=cached,
        query_id="q-hybrid-001",
        mode="hybrid",
    )


def _make_lookup_result(
    status="found",
    reference="Inc. III do Art. 9 da IN 58",
    elapsed_ms=45.0,
    include_match=True,
    include_parent=True,
    include_siblings=True,
    include_resolved=True,
    candidates=None,
):
    from vectorgov.models import LookupResult

    _empty_meta = Metadata(document_type="", document_number="", year=0)

    match = None
    if include_match:
        match = Hit(
            node_id="leis:IN-58-2022#INC-009-III",
            span_id="INC-009-III",
            document_id="IN-58-2022",
            text="III - texto do inciso...",
            score=0.0,
            source="IN-58-2022",
            metadata=Metadata(document_type="IN", document_number="58", year=2022),
            device_type="inciso",
            article_number="9",
            tipo_documento="IN",
            evidence_url="/api/v1/evidence/IN-58-2022%23INC-009-III",
        )

    parent = None
    if include_parent:
        parent = Hit(
            node_id="leis:IN-58-2022#ART-009",
            span_id="ART-009",
            text="Art. 9. Os documentos...",
            score=0.0,
            source="",
            metadata=_empty_meta,
            device_type="article",
        )

    siblings = []
    if include_siblings:
        siblings = [
            Hit(
                span_id="INC-009-I", node_id="leis:IN-58-2022#INC-009-I",
                device_type="inciso", text="I - texto...", is_current=False,
                score=0.0, source="", metadata=_empty_meta,
            ),
            Hit(
                span_id="INC-009-II", node_id="leis:IN-58-2022#INC-009-II",
                device_type="inciso", text="II - texto...", is_current=False,
                score=0.0, source="", metadata=_empty_meta,
            ),
            Hit(
                span_id="INC-009-III", node_id="leis:IN-58-2022#INC-009-III",
                device_type="inciso", text="III - texto do inciso...", is_current=True,
                score=0.0, source="", metadata=_empty_meta,
            ),
        ]

    resolved = None
    if include_resolved:
        resolved = {
            "device_type": "inciso",
            "article_number": "9",
            "inciso_number": "III",
            "document_alias": "IN 58",
            "resolved_document_id": "IN-58-2022",
            "resolved_span_id": "INC-009-III",
        }

    return LookupResult(
        query=reference,
        status=status,
        latency_ms=elapsed_ms,
        match=match,
        parent=parent,
        siblings=siblings,
        resolved=resolved,
        candidates=candidates or [],
    )


# =============================================================================
# TESTES HYBRID XML
# =============================================================================


class TestHybridXml:
    def test_hybrid_xml_data_level(self):
        """Estrutura básica do hybrid XML com endpoint='hybrid'."""
        r = _make_hybrid_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("version") == "1.0"
        assert root.get("endpoint") == "hybrid"
        assert root.get("level") == "data"

        # Seções de dados presentes
        assert root.find("consulta") is not None
        assert root.find("base_normativa") is not None
        assert root.find("contexto_normativo") is not None
        assert root.find("metadados") is not None

        # Sem instruções
        assert root.find("instrucoes") is None
        assert root.find("instrucoes_completas") is None

    def test_hybrid_xml_full_level(self):
        """Level full tem instrucoes_completas e contrato."""
        r = _make_hybrid_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        assert root.get("level") == "full"

        ic = root.find("instrucoes_completas")
        assert ic is not None
        assert ic.find("papel") is not None
        assert ic.find("anti_alucinacao") is not None
        assert ic.find("contrato_resposta") is not None

    def test_hybrid_xml_instructions_level(self):
        """Level instructions tem instrucoes (7 regras, Seção 6.2)."""
        r = _make_hybrid_result()
        xml = r.to_xml("instructions")
        root = ET.fromstring(xml)

        assert root.get("level") == "instructions"
        instrucoes = root.find("instrucoes")
        assert instrucoes is not None
        regras = instrucoes.findall("regra")
        assert len(regras) == 7

    def test_hybrid_xml_doc_foco(self):
        """Consulta tem atributo doc_foco quando docfilter ativo."""
        r = _make_hybrid_result(docfilter_active=True,
                                docfilter_detected_doc_id="LEI-14133-2021")
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        consulta = root.find("consulta")
        assert consulta.get("doc_foco") == "LEI-14133-2021"

    def test_hybrid_xml_backend_confidence(self):
        """Usa confiança do backend (não calculada)."""
        r = _make_hybrid_result(confidence=0.92)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        conf = root.find("consulta/confianca_global")
        assert conf is not None
        assert conf.text == "0.9200"

    def test_hybrid_xml_stitched_text_priority(self):
        """stitched_text prioriza sobre text no dispositivo."""
        hit = _make_hybrid_hit(
            text="Art. 33. Texto curto.",
            stitched_text="[CONTEXTO] Art. 33. Texto consolidado completo...",
        )
        r = _make_hybrid_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp is not None
        assert "Texto consolidado completo" in disp.text

    def test_hybrid_xml_score_rerank(self):
        """Atributo score_rerank no dispositivo quando pure_rerank_score presente."""
        hit = _make_hybrid_hit(pure_rerank_score=0.87)
        r = _make_hybrid_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("score_rerank") == "0.8700"

    def test_hybrid_xml_graph_expansion_freq_tipo(self):
        """Contexto normativo tem freq e tipo nos relacionados."""
        ec = _make_hybrid_expanded(frequency=5, device_type="article")
        r = _make_hybrid_result(graph_nodes=[ec])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp_rel = root.find("contexto_normativo/dispositivo_relacionado")
        assert disp_rel is not None
        assert disp_rel.get("freq") == "5"
        assert disp_rel.get("tipo") == "artigo"
        # origem não é mais emitido (Seção 6 spec)
        assert disp_rel.get("origem") is None

    def test_hybrid_xml_metadados_hyde(self):
        """Metadados incluem tag hyde."""
        r = _make_hybrid_result(hyde_used=True)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        meta = root.find("metadados")
        hyde = meta.find("hyde")
        assert hyde is not None
        assert hyde.text == "true"

    def test_hybrid_xml_metadados_timings(self):
        """Metadados incluem timings flat (sem wrapper)."""
        r = _make_hybrid_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        meta = root.find("metadados")
        assert meta is not None
        # Timings flat diretamente em metadados
        assert meta.find("tempo_busca_ms") is not None
        assert meta.find("tempo_rerank_ms") is not None
        assert meta.find("tempo_grafo_ms") is not None
        # Sem wrapper <timings>
        assert meta.find("timings") is None

    def test_hybrid_xml_metadados_stats(self):
        """Metadados incluem stats extras (nodes_grafo, total_chunks, total_tokens)."""
        r = _make_hybrid_result(stats={
            "timings": {"search_ms": 80, "rerank_ms": 40, "graph_ms": 30},
            "hits_milvus": 9,
            "graph_nodes": 4,
            "total_chunks": 13,
            "total_tokens": 1480,
        })
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        meta = root.find("metadados")
        assert meta.find("hits_milvus").text == "9"
        assert meta.find("nodes_grafo").text == "4"
        assert meta.find("total_chunks").text == "13"
        assert meta.find("total_tokens").text == "1480"

    def test_hybrid_xml_metadados_dual_lane_in_estrategia(self):
        """dual_lane info aparece no texto da estrategia, não em sub-elemento."""
        r = _make_hybrid_result(
            dual_lane_active=True,
            dual_lane_filtered_doc="LEI-14133-2021",
            dual_lane_from_filtered=5,
            dual_lane_from_free=3,
            docfilter_detected_doc_id="LEI-14133-2021",
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        # dual_lane NÃO aparece como sub-elemento de metadados
        assert root.find("metadados/dual_lane") is None
        # Em vez disso, aparece no texto da estrategia
        estrategia = root.find("consulta/estrategia").text
        assert "dual_lane" in estrategia
        assert "doc_foco=LEI-14133-2021" in estrategia

    def test_hybrid_xml_empty_graph(self):
        """Sem graph_expansion: contexto_normativo ausente."""
        r = _make_hybrid_result(graph_nodes=[])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.find("contexto_normativo") is None

    def test_hybrid_to_messages(self):
        """build_hybrid_messages_xml retorna formato correto."""
        r = _make_hybrid_result()
        msgs = r.to_messages("Teste?", level="instructions")

        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "<vectorgov_knowledge_package" in msgs[0]["content"]
        assert "endpoint=\"hybrid\"" in msgs[0]["content"]
        assert msgs[1]["content"] == "Teste?"

    def test_hybrid_to_prompt(self):
        """build_hybrid_prompt_xml retorna XML + query."""
        r = _make_hybrid_result()
        prompt = r.to_prompt("Teste?", level="data")

        assert "<vectorgov_knowledge_package" in prompt
        assert "Teste?" in prompt
        assert "Resposta:" in prompt

    def test_hybrid_response_schema(self):
        """JSON Schema com IDs de direct_evidence."""
        r = _make_hybrid_result()
        wrapper = r.to_response_schema()

        assert wrapper is not None
        assert wrapper["name"] == "resposta_juridica_vectorgov"
        assert wrapper["strict"] is True

        schema = wrapper["schema"]
        enum = schema["properties"]["fundamentacao"]["items"]["properties"]["dispositivo_id"]["enum"]
        assert "ART-33" in enum
        assert "ART-34" in enum
        # expanded chunk span_id
        assert "ART-036" in enum

    def test_hybrid_markdown(self):
        """Markdown legível com evidências e expansão."""
        r = _make_hybrid_result()
        md = r.to_markdown()

        assert "Resultados Híbridos" in md
        assert "Evidências Diretas" in md
        assert "Expansão via Grafo" in md
        assert "ART-036" in md


# =============================================================================
# TESTES LOOKUP XML
# =============================================================================


class TestLookupXml:
    def test_lookup_xml_found(self):
        """Status=found com hierarquia completa."""
        r = _make_lookup_result(status="found")
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("endpoint") == "lookup"
        assert root.get("level") == "data"

        consulta = root.find("consulta")
        assert consulta is not None
        assert consulta.find("referencia_original").text == "Inc. III do Art. 9 da IN 58"
        assert consulta.find("status").text == "found"

        hierarquia = root.find("hierarquia_normativa")
        assert hierarquia is not None

    def test_lookup_xml_not_found(self):
        """Status=not_found: sem hierarquia."""
        r = _make_lookup_result(
            status="not_found",
            include_match=False,
            include_parent=False,
            include_siblings=False,
            include_resolved=False,
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.find("consulta/status").text == "not_found"
        assert root.find("hierarquia_normativa") is None

    def test_lookup_xml_ambiguous(self):
        """Status=ambiguous com candidatos."""
        from vectorgov.models import LookupCandidate

        candidates = [
            LookupCandidate(
                document_id="LEI-14133-2021", node_id="leis:LEI-14133-2021#ART-009",
                text="Art. 9 da Lei 14.133...", tipo_documento="LEI",
            ),
            LookupCandidate(
                document_id="IN-58-2022", node_id="leis:IN-58-2022#ART-009",
                text="Art. 9 da IN 58...", tipo_documento="IN",
            ),
        ]
        r = _make_lookup_result(
            status="ambiguous",
            include_match=False,
            include_parent=False,
            include_siblings=False,
            candidates=candidates,
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.find("consulta/status").text == "ambiguous"
        candidatos = root.find("candidatos")
        assert candidatos is not None
        cands = candidatos.findall("candidato")
        assert len(cands) == 2

    def test_lookup_xml_with_parent(self):
        """Artigo pai presente na hierarquia."""
        r = _make_lookup_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        pai = root.find("hierarquia_normativa/artigo_pai")
        assert pai is not None
        assert pai.get("id") == "ART-009"
        assert pai.get("device_type") == "article"
        assert "documentos" in pai.text

    def test_lookup_xml_with_siblings(self):
        """Dispositivos irmãos com is_current."""
        r = _make_lookup_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        irmaos = root.find("hierarquia_normativa/dispositivos_irmaos")
        assert irmaos is not None
        irmao_list = irmaos.findall("irmao")
        assert len(irmao_list) == 3

        # O terceiro é o atual
        assert irmao_list[2].get("atual") == "true"
        assert irmao_list[0].get("atual") == "false"

    def test_lookup_xml_resolved_components(self):
        """Referência resolvida com atributos de parsing."""
        r = _make_lookup_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        ref = root.find("consulta/referencia_resolvida")
        assert ref is not None
        assert ref.get("device_type") == "inciso"
        assert ref.get("artigo") == "9"
        assert ref.get("inciso") == "III"
        assert ref.get("documento") == "IN-58-2022"

    def test_lookup_xml_instructions_level(self):
        """Level instructions com instrucoes."""
        r = _make_lookup_result()
        xml = r.to_xml("instructions")
        root = ET.fromstring(xml)

        assert root.get("level") == "instructions"
        instrucoes = root.find("instrucoes")
        assert instrucoes is not None

    def test_lookup_xml_full_level(self):
        """Level full com instrucoes_completas."""
        r = _make_lookup_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        assert root.get("level") == "full"
        ic = root.find("instrucoes_completas")
        assert ic is not None

    def test_lookup_markdown(self):
        """Markdown legível do lookup."""
        r = _make_lookup_result()
        md = r.to_markdown()

        assert "Lookup" in md
        assert "found" in md
        assert "INC-009-III" in md

    def test_lookup_to_dict(self):
        """Serialização para dicionário."""
        r = _make_lookup_result()
        d = r.to_dict()

        assert d["reference"] == "Inc. III do Art. 9 da IN 58"
        assert d["status"] == "found"
        assert d["match"]["span_id"] == "INC-009-III"
        assert d["match"]["document_id"] == "IN-58-2022"

    def test_lookup_empty_parent_siblings(self):
        """Sem parent e siblings: seções omitidas."""
        r = _make_lookup_result(include_parent=False, include_siblings=False)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        hierarquia = root.find("hierarquia_normativa")
        assert hierarquia is not None  # ainda tem o dispositivo_principal
        assert hierarquia.find("artigo_pai") is None
        assert hierarquia.find("dispositivos_irmaos") is None

    def test_lookup_parse_failed_status(self):
        """Status=parse_failed."""
        r = _make_lookup_result(
            status="parse_failed",
            reference="texto inválido xyz",
            include_match=False,
            include_parent=False,
            include_siblings=False,
            include_resolved=False,
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        assert root.find("consulta/status").text == "parse_failed"


# =============================================================================
# TESTES CAMPOS NOVOS NO SEARCH
# =============================================================================


class TestNewSearchFields:
    def test_search_stitched_text_in_xml(self):
        """stitched_text prioriza sobre text no XML do search."""
        hit = _make_hit()
        hit.stitched_text = "[CONTEXTO] Art. 33. Texto consolidado..."
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert "Texto consolidado" in disp.text

    def test_search_pure_rerank_score(self):
        """score_rerank no XML quando pure_rerank_score presente."""
        hit = _make_hit()
        hit.pure_rerank_score = 0.92
        r = _make_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("score_rerank") == "0.9200"

    def test_hit_new_fields_default_none(self):
        """Backward compat: novos campos opcionais com defaults."""
        hit = _make_hit()
        assert hit.stitched_text is None
        assert hit.pure_rerank_score is None
        assert hit.parent_node_id is None
        assert hit.is_parent is False
        assert hit.is_sibling is False
        assert hit.is_child_of_seed is False
        assert hit.evidence_url is None
        assert hit.document_url is None
        assert hit.sha256_source is None
        assert hit.graph_boost_applied is None
        assert hit.curation_boost_applied is None

    def test_expanded_chunk_frequency_paths(self):
        """Expanded chunk dict tem campos acessíveis via .get()."""
        ec = _make_expanded_chunk()
        assert ec.get("frequency", 0) == 0
        assert ec.get("paths", []) == []
        assert ec.get("origin_type", "self") == "self"

    def test_expanded_chunk_with_values(self):
        """HybridResult graph_nodes (Hit) aceita novos valores."""
        ec = _make_hybrid_expanded(frequency=10, paths=[["A", "B"]], origin_type="cruzada")
        assert ec.frequency == 10
        assert ec.paths == [["A", "B"]]
        assert ec.origin_type == "cruzada"

    def test_hybrid_result_iteration(self):
        """__len__, __iter__, __getitem__ sobre direct_evidence."""
        r = _make_hybrid_result()

        assert len(r) == 2
        items = list(r)
        assert len(items) == 2
        assert r[0].score == 0.9
        assert r[1].score == 0.78

    def test_hybrid_result_normative_trail(self):
        """normative_trail retorna fontes deduplicadas."""
        r = _make_hybrid_result()
        trail = r.normative_trail

        assert isinstance(trail, list)
        assert len(trail) == 1  # Ambos hits da mesma lei
        assert "LEI 14133/2021" in trail

    def test_hybrid_result_to_dict(self):
        """to_dict do HybridResult."""
        r = _make_hybrid_result()
        d = r.to_dict()

        assert d["query"] == "Quais os critérios de julgamento?"
        assert len(d["direct_evidence"]) == 2
        assert len(d["graph_expansion"]) == 1
        assert d["confidence"] == 0.85
        assert d["mode"] == "hybrid"

    def test_hybrid_result_to_context(self):
        """to_context do HybridResult."""
        r = _make_hybrid_result()
        ctx = r.to_context()

        assert "EVIDÊNCIA DIRETA" in ctx
        assert "EXPANSÃO VIA GRAFO" in ctx
        assert "ART-036" in ctx
        assert "hop=1" in ctx

    def test_hybrid_result_empty_evidence(self):
        """HybridResult sem evidências."""
        r = _make_hybrid_result(hits=[], graph_nodes=[])

        assert len(r) == 0
        assert r.to_response_schema() is None

    def test_hybrid_xml_no_score_rerank_when_none(self):
        """Sem score_rerank quando pure_rerank_score é None."""
        hit = _make_hybrid_hit(pure_rerank_score=None)
        r = _make_hybrid_result(hits=[hit])
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        disp = root.find("base_normativa/fonte/dispositivo")
        assert disp.get("score_rerank") is None

    def test_hybrid_xml_no_doc_foco_when_inactive(self):
        """Sem doc_foco quando docfilter inativo."""
        r = _make_hybrid_result(docfilter_active=False, docfilter_detected_doc_id=None)
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        consulta = root.find("consulta")
        assert consulta.get("doc_foco") is None

    def test_hybrid_xml_query_interpretada(self):
        """query_interpretada usa query_rewrite_clean_query quando presente."""
        r = _make_hybrid_result(
            query_rewrite_active=True,
            query_rewrite_clean_query="critérios julgamento licitações",
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)

        qi = root.find("consulta/query_interpretada")
        assert qi.text == "critérios julgamento licitações"

    def test_hybrid_xml_estrategia(self):
        """Seção consulta tem estrategia composta com doc_foco e dual_lane."""
        # Sem dual_lane, com docfilter
        r = _make_hybrid_result()
        xml = r.to_xml("data")
        root = ET.fromstring(xml)
        estrategia = root.find("consulta/estrategia").text
        assert estrategia == "hybrid (doc_foco=LEI-14133-2021)"

    def test_hybrid_xml_estrategia_dual_lane(self):
        """Estrategia composta com dual_lane e doc_foco."""
        r = _make_hybrid_result(
            dual_lane_active=True,
            docfilter_detected_doc_id="LEI-14133-2021",
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)
        estrategia = root.find("consulta/estrategia").text
        assert estrategia == "hybrid:dual_lane (doc_foco=LEI-14133-2021)"

    def test_hybrid_xml_estrategia_plain(self):
        """Estrategia simples quando sem dual_lane e sem docfilter."""
        r = _make_hybrid_result(
            dual_lane_active=False,
            docfilter_detected_doc_id=None,
        )
        xml = r.to_xml("data")
        root = ET.fromstring(xml)
        assert root.find("consulta/estrategia").text == "hybrid"


# =============================================================================
# TESTES PAYLOAD DIRETO — Hybrid & Lookup
# =============================================================================


class TestPayloadDirectHybridLookup:
    def test_build_hybrid_xml_valid(self):
        """build_hybrid_xml produz XML válido."""
        from vectorgov.payload import build_hybrid_xml

        r = _make_hybrid_result()
        for level in ("data", "instructions", "full"):
            xml = build_hybrid_xml(r, level=level)
            root = ET.fromstring(xml)
            assert root.tag == "vectorgov_knowledge_package"
            assert root.get("endpoint") == "hybrid"

    def test_build_lookup_xml_valid(self):
        """build_lookup_xml produz XML válido."""
        from vectorgov.payload import build_lookup_xml

        r = _make_lookup_result()
        for level in ("data", "instructions", "full"):
            xml = build_lookup_xml(r, level=level)
            root = ET.fromstring(xml)
            assert root.tag == "vectorgov_knowledge_package"
            assert root.get("endpoint") == "lookup"

    def test_build_hybrid_markdown(self):
        """build_hybrid_markdown retorna markdown."""
        from vectorgov.payload import build_hybrid_markdown

        r = _make_hybrid_result()
        md = build_hybrid_markdown(r)
        assert "Resultados Híbridos" in md

    def test_build_lookup_markdown(self):
        """build_lookup_markdown retorna markdown."""
        from vectorgov.payload import build_lookup_markdown

        r = _make_lookup_result()
        md = build_lookup_markdown(r)
        assert "Lookup" in md

    def test_collect_authorized_ids_from_hits(self):
        """_collect_authorized_ids_from_hits retorna IDs corretos."""
        from vectorgov.payload import _collect_authorized_ids_from_hits

        hits = [_make_hybrid_hit(chunk_id="LEI-14133-2021#ART-033")]
        expanded = [_make_hybrid_expanded()]
        ids = _collect_authorized_ids_from_hits(hits, expanded)

        assert "ART-033" in ids
        assert "ART-036" in ids

    def test_get_hits_search_result(self):
        """_get_hits funciona com SearchResult."""
        from vectorgov.payload import _get_hits

        r = _make_result()
        hits = _get_hits(r)
        assert len(hits) == 2

    def test_get_hits_hybrid_result(self):
        """_get_hits funciona com HybridResult."""
        from vectorgov.payload import _get_hits

        r = _make_hybrid_result()
        hits = _get_hits(r)
        assert len(hits) == 2

    def test_get_expanded_search_result(self):
        """_get_expanded funciona com SearchResult."""
        from vectorgov.payload import _get_expanded

        ec = _make_expanded_chunk()
        r = _make_result(expanded=[ec])
        expanded = _get_expanded(r)
        assert len(expanded) == 1

    def test_get_expanded_hybrid_result(self):
        """_get_expanded funciona com HybridResult."""
        from vectorgov.payload import _get_expanded

        r = _make_hybrid_result()
        expanded = _get_expanded(r)
        assert len(expanded) == 1


# =============================================================================
# SEÇÃO 7 — TESTES DE LACUNAS (serialize_to_xml, generate_*, mapa_evidencias)
# =============================================================================


class TestSection7Gaps:
    """Testes para funcionalidades da Seção 7 do spec."""

    def test_serialize_to_xml_search_result(self):
        """serialize_to_xml despacha para build_xml com SearchResult."""
        from vectorgov.payload import serialize_to_xml

        r = _make_result()
        xml = serialize_to_xml(r, level="data")
        root = ET.fromstring(xml)
        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("level") == "data"
        # SearchResult não tem endpoint attribute
        assert root.get("endpoint") is None

    def test_serialize_to_xml_hybrid_result(self):
        """serialize_to_xml despacha para build_hybrid_xml com HybridResult."""
        from vectorgov.payload import serialize_to_xml

        r = _make_hybrid_result()
        xml = serialize_to_xml(r, level="data")
        root = ET.fromstring(xml)
        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("endpoint") == "hybrid"

    def test_serialize_to_xml_lookup_result(self):
        """serialize_to_xml despacha para build_lookup_xml com LookupResult."""
        from vectorgov.payload import serialize_to_xml

        r = _make_lookup_result()
        xml = serialize_to_xml(r, level="data")
        root = ET.fromstring(xml)
        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("endpoint") == "lookup"

    def test_serialize_to_xml_invalid_type(self):
        """serialize_to_xml levanta TypeError para tipo desconhecido."""
        from vectorgov.payload import serialize_to_xml

        with pytest.raises(TypeError, match="Tipo não suportado"):
            serialize_to_xml({"raw": "dict"}, level="data")

    def test_serialize_to_xml_respects_level(self):
        """serialize_to_xml passa level corretamente para cada tipo."""
        from vectorgov.payload import serialize_to_xml

        r = _make_hybrid_result()
        xml = serialize_to_xml(r, level="instructions")
        root = ET.fromstring(xml)
        assert root.get("level") == "instructions"
        assert root.find("instrucoes") is not None

    def test_generate_response_schema_search(self):
        """generate_response_schema funciona com SearchResult."""
        from vectorgov.payload import generate_response_schema

        r = _make_result()
        schema = generate_response_schema(r)
        assert schema is not None
        assert schema["name"] == "resposta_juridica_vectorgov"
        assert schema["strict"] is True
        assert "fundamentacao" in schema["schema"]["properties"]

    def test_generate_response_schema_hybrid(self):
        """generate_response_schema funciona com HybridResult."""
        from vectorgov.payload import generate_response_schema

        r = _make_hybrid_result()
        schema = generate_response_schema(r)
        assert schema is not None
        assert schema["name"] == "resposta_juridica_vectorgov"
        # Enum deve conter IDs de direct_evidence e graph_expansion
        enum_ids = schema["schema"]["properties"]["fundamentacao"]["items"]["properties"]["dispositivo_id"]["enum"]
        assert "ART-33" in enum_ids   # from _make_hybrid_hit chunk_id
        assert "ART-036" in enum_ids  # from graph_expansion

    def test_generate_response_schema_empty_returns_none(self):
        """generate_response_schema retorna None se não houver hits."""
        from vectorgov.payload import generate_response_schema

        r = _make_result()
        r._hits = []  # Limpa hits
        r = SearchResult(
            query="vazia", hits=[], total=0, latency_ms=10,
            cached=False, query_id="q1", mode="search",
        )
        schema = generate_response_schema(r)
        assert schema is None

    def test_generate_anthropic_tool_schema_search(self):
        """generate_anthropic_tool_schema funciona com SearchResult."""
        from vectorgov.payload import generate_anthropic_tool_schema

        r = _make_result()
        tool = generate_anthropic_tool_schema(r)
        assert tool is not None
        assert tool["name"] == "resposta_juridica_vectorgov"
        assert "input_schema" in tool
        assert "description" in tool

    def test_generate_anthropic_tool_schema_hybrid(self):
        """generate_anthropic_tool_schema funciona com HybridResult."""
        from vectorgov.payload import generate_anthropic_tool_schema

        r = _make_hybrid_result()
        tool = generate_anthropic_tool_schema(r)
        assert tool is not None
        assert "input_schema" in tool

    def test_hybrid_full_has_mapa_evidencias(self):
        """Hybrid level=full inclui mapa_evidencias no contrato_resposta."""
        r = _make_hybrid_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        mapa = root.find("instrucoes_completas/contrato_resposta/mapa_evidencias")
        assert mapa is not None
        assert mapa.text is not None
        # Deve conter URLs de evidência
        assert "/api/v1/evidence/" in mapa.text
        # Deve ter seta unicode (→)
        assert "\u2192" in mapa.text

    def test_hybrid_full_mapa_evidencias_has_all_ids(self):
        """mapa_evidencias no hybrid inclui IDs de direct_evidence e graph_expansion."""
        r = _make_hybrid_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        mapa = root.find("instrucoes_completas/contrato_resposta/mapa_evidencias")
        assert mapa is not None
        text = mapa.text
        # IDs de direct_evidence (chunk_id="LEI-14133-2021#ART-33")
        assert "ART-33" in text
        # IDs de graph_expansion
        assert "ART-036" in text

    def test_search_full_has_mapa_evidencias(self):
        """Search level=full já tinha mapa_evidencias (confirmação de regressão)."""
        r = _make_result()
        xml = r.to_xml("full")
        root = ET.fromstring(xml)

        mapa = root.find("instrucoes_completas/contrato_resposta/mapa_evidencias")
        assert mapa is not None
        assert "/api/v1/evidence/" in mapa.text


# =============================================================================
# TESTES SECTION 7.2 GAPS
# =============================================================================


class TestSection72Gaps:
    """Testes para os 5 gaps identificados na Seção 7.2."""

    # --- Gap 1: LookupResult.to_prompt() ---

    def test_lookup_to_prompt_default(self):
        """to_prompt() retorna XML + reference como query."""
        r = _make_lookup_result()
        prompt = r.to_prompt()
        assert "vectorgov_knowledge_package" in prompt
        assert "Inc. III do Art. 9 da IN 58" in prompt
        assert prompt.endswith("Resposta:")

    def test_lookup_to_prompt_custom_query(self):
        """to_prompt() aceita query customizada."""
        r = _make_lookup_result()
        prompt = r.to_prompt(query="O que diz o inciso III?")
        assert "O que diz o inciso III?" in prompt
        assert "vectorgov_knowledge_package" in prompt

    def test_lookup_to_prompt_level_full(self):
        """to_prompt() com level=full inclui instrucoes_completas."""
        r = _make_lookup_result()
        prompt = r.to_prompt(level="full")
        assert "instrucoes_completas" in prompt

    # --- Gap 2: LookupResult.to_messages() ---

    def test_lookup_to_messages_format(self):
        """to_messages() retorna lista com system e user."""
        r = _make_lookup_result()
        msgs = r.to_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "vectorgov_knowledge_package" in msgs[0]["content"]

    def test_lookup_to_messages_default_query(self):
        """to_messages() usa reference como query por padrão."""
        r = _make_lookup_result()
        msgs = r.to_messages()
        assert msgs[1]["content"] == "Inc. III do Art. 9 da IN 58"

    def test_lookup_to_messages_custom_query(self):
        """to_messages() aceita query customizada."""
        r = _make_lookup_result()
        msgs = r.to_messages(query="Explique este inciso")
        assert msgs[1]["content"] == "Explique este inciso"

    def test_lookup_to_messages_level(self):
        """to_messages() respeita level."""
        r = _make_lookup_result()
        msgs_data = r.to_messages(level="data")
        msgs_full = r.to_messages(level="full")
        # data não tem instrucoes
        assert "instrucoes" not in msgs_data[0]["content"]
        # full tem instrucoes_completas
        assert "instrucoes_completas" in msgs_full[0]["content"]

    # --- Gap 3: HybridResult.query_interpretation ---

    def test_hybrid_query_interpretation_minimal(self):
        """query_interpretation retorna dict mínimo sem raw_response."""
        r = _make_hybrid_result()
        qi = r.query_interpretation
        assert qi["original_query"] == "Quais os critérios de julgamento?"

    def test_hybrid_query_interpretation_with_rewrite(self):
        """query_interpretation inclui rewritten_query quando ativa."""
        r = _make_hybrid_result(
            query_rewrite_active=True,
            query_rewrite_clean_query="critérios julgamento licitação",
        )
        qi = r.query_interpretation
        assert qi["original_query"] == "Quais os critérios de julgamento?"
        assert qi["rewritten_query"] == "critérios julgamento licitação"

    def test_hybrid_query_interpretation_with_docfilter(self):
        """query_interpretation inclui detected_document_id quando disponível."""
        r = _make_hybrid_result(
            docfilter_active=True,
            docfilter_detected_doc_id="LEI-14133-2021",
        )
        qi = r.query_interpretation
        assert qi["detected_document_id"] == "LEI-14133-2021"

    def test_hybrid_query_interpretation_from_raw_response(self):
        """query_interpretation usa _raw_response quando disponível."""
        from vectorgov.models import HybridResult
        r = _make_hybrid_result()
        r._raw_response = {
            "query_interpretation": {
                "original_query": "test",
                "entities": ["ETP"],
            }
        }
        qi = r.query_interpretation
        assert qi["original_query"] == "test"
        assert qi["entities"] == ["ETP"]

    # --- Gap 4: LookupResult.to_response_schema() ---

    def test_lookup_to_response_schema_found(self):
        """to_response_schema() retorna schema com IDs de match/parent/siblings."""
        r = _make_lookup_result()
        schema = r.to_response_schema()
        assert schema is not None
        assert schema["name"] == "resposta_juridica_vectorgov"
        assert schema["strict"] is True
        # Verifica que o enum contém os IDs
        enum_ids = schema["schema"]["properties"]["fundamentacao"]["items"][
            "properties"
        ]["dispositivo_id"]["enum"]
        assert "INC-009-III" in enum_ids
        assert "ART-009" in enum_ids
        assert "INC-009-I" in enum_ids
        assert "INC-009-II" in enum_ids

    def test_lookup_to_response_schema_not_found(self):
        """to_response_schema() retorna None quando status=not_found sem match."""
        r = _make_lookup_result(
            status="not_found",
            include_match=False,
            include_parent=False,
            include_siblings=False,
        )
        schema = r.to_response_schema()
        assert schema is None

    def test_lookup_to_response_schema_no_duplicates(self):
        """to_response_schema() não duplica IDs quando match.span_id == sibling."""
        r = _make_lookup_result()
        schema = r.to_response_schema()
        enum_ids = schema["schema"]["properties"]["fundamentacao"]["items"][
            "properties"
        ]["dispositivo_id"]["enum"]
        # INC-009-III aparece no match E nos siblings, mas deve ser único
        assert enum_ids.count("INC-009-III") == 1

    # --- Gap 5: LookupResult.to_anthropic_tool_schema() ---

    def test_lookup_to_anthropic_tool_schema_found(self):
        """to_anthropic_tool_schema() retorna formato Anthropic tool."""
        r = _make_lookup_result()
        tool = r.to_anthropic_tool_schema()
        assert tool is not None
        assert tool["name"] == "resposta_juridica_vectorgov"
        assert "input_schema" in tool
        assert "description" in tool

    def test_lookup_to_anthropic_tool_schema_not_found(self):
        """to_anthropic_tool_schema() retorna None sem match."""
        r = _make_lookup_result(
            status="not_found",
            include_match=False,
            include_parent=False,
            include_siblings=False,
        )
        tool = r.to_anthropic_tool_schema()
        assert tool is None

    # --- Aliases públicos com LookupResult ---

    def test_generate_response_schema_lookup(self):
        """generate_response_schema() detecta LookupResult."""
        from vectorgov.payload import generate_response_schema
        r = _make_lookup_result()
        schema = generate_response_schema(r)
        assert schema is not None
        assert schema["name"] == "resposta_juridica_vectorgov"

    def test_generate_anthropic_tool_schema_lookup(self):
        """generate_anthropic_tool_schema() detecta LookupResult."""
        from vectorgov.payload import generate_anthropic_tool_schema
        r = _make_lookup_result()
        tool = generate_anthropic_tool_schema(r)
        assert tool is not None
        assert tool["name"] == "resposta_juridica_vectorgov"


# =============================================================================
# SEÇÃO 8 — TESTES COM FIXTURES JSON (caminho completo: JSON → parser → to_xml)
# =============================================================================


class TestFixtureSearch:
    """Testes usando fixture JSON real do /sdk/search."""

    def test_fixture_search_parse(self, search_result):
        """Parser instancia SearchResult corretamente a partir do JSON."""
        assert len(search_result.hits) == 3
        assert search_result.query == "Como fazer pesquisa de preços?"
        assert search_result.query_id == "q-search-pesquisa-001"
        assert search_result.cached is False
        assert search_result._raw_response is not None

    def test_fixture_search_hits_metadata(self, search_result):
        """Hits têm metadata tipada com campos corretos."""
        h = search_result.hits[0]
        assert h.score == 0.91
        assert h.metadata.document_type == "LEI"
        assert h.metadata.article == "23"
        assert h.metadata.year == 2021
        assert h.nota_especialista is not None
        assert h.evidence_url is not None

    def test_fixture_search_expanded_chunks(self, search_result):
        """Chunks expandidos são parseados como dicts."""
        assert len(search_result.expanded_chunks) == 1
        ec = search_result.expanded_chunks[0]
        assert ec["span_id"] == "ART-018"
        assert ec["document_id"] == "LEI-14133-2021"
        assert ec["source_chunk_id"] == "LEI-14133-2021#ART-023"

    def test_fixture_search_expansion_stats(self, search_result):
        """Estatísticas de expansão são parseadas como dict."""
        stats = search_result.expansion_stats
        assert stats is not None
        assert stats["expanded_chunks_count"] == 1
        assert stats["citations_scanned_count"] == 4
        assert stats["skipped_self_references"] == 1

    def test_fixture_search_to_xml_roundtrip(self, search_result):
        """JSON → parser → to_xml produz XML válido com dados corretos."""
        xml = search_result.to_xml("data")
        root = ET.fromstring(xml)
        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("version") == "1.0"
        assert root.get("level") == "data"

        # Verifica que os artigos estão no XML
        dispositivos = root.findall(".//dispositivo")
        assert len(dispositivos) >= 3

    def test_fixture_search_to_xml_full(self, search_result):
        """to_xml('full') inclui instrucoes_completas e contrato."""
        xml = search_result.to_xml("full")
        root = ET.fromstring(xml)
        assert root.find("instrucoes_completas") is not None
        assert root.find("instrucoes_completas/contrato_resposta") is not None

    def test_fixture_search_to_messages(self, search_result):
        """to_messages com level gera system+user corretos."""
        msgs = search_result.to_messages(level="instructions")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "pesquisa de preços" in msgs[1]["content"]

    def test_fixture_search_to_dict_passthrough(self, search_result):
        """to_dict retorna _raw_response intacto."""
        d = search_result.to_dict()
        assert d["query_id"] == "q-search-pesquisa-001"
        assert "hits" in d
        assert len(d["hits"]) == 3

    def test_fixture_search_confidence(self, search_result):
        """confidence property calcula valor numérico."""
        c = search_result.confidence
        assert 0.0 <= c <= 1.0

    def test_fixture_search_normative_trail(self, search_result):
        """normative_trail extrai fontes deduplicadas."""
        trail = search_result.normative_trail
        assert len(trail) >= 1
        assert any("14133" in t for t in trail)

    def test_fixture_search_query_interpretation(self, search_result):
        """query_interpretation lê de _raw_response."""
        qi = search_result.query_interpretation
        assert qi["original_query"] == "Como fazer pesquisa de preços?"

    def test_fixture_search_response_schema(self, search_result):
        """to_response_schema gera schema com IDs dos hits."""
        schema = search_result.to_response_schema()
        assert schema is not None
        assert schema["name"] == "resposta_juridica_vectorgov"
        assert schema["strict"] is True


class TestFixtureHybrid:
    """Testes usando fixture JSON real do /api/v1/hybrid."""

    def test_fixture_hybrid_parse(self, hybrid_result):
        """Parser instancia HybridResult com todos os campos."""
        assert len(hybrid_result.direct_evidence) == 2
        assert len(hybrid_result.graph_expansion) == 2
        assert hybrid_result.confidence == 0.87
        assert hybrid_result.hyde_used is True
        assert hybrid_result.docfilter_active is True
        assert hybrid_result.query_rewrite_active is True
        assert hybrid_result.dual_lane_active is True

    def test_fixture_hybrid_direct_evidence(self, hybrid_result):
        """Evidências diretas têm campos extras do hybrid."""
        h = hybrid_result.direct_evidence[0]
        assert h.score == 0.92
        assert h.stitched_text is not None
        assert h.pure_rerank_score == 0.89
        assert h.graph_boost_applied == 0.05
        assert h.evidence_url is not None

    def test_fixture_hybrid_graph_expansion(self, hybrid_result):
        """Graph expansion tem hop, frequency e paths."""
        g = hybrid_result.graph_expansion[0]
        assert g.hop == 1
        assert g.frequency == 5
        assert len(g.paths) == 2
        assert g.span_id == "ART-036"

        g2 = hybrid_result.graph_expansion[1]
        assert g2.hop == 2
        assert g2.frequency == 2

    def test_fixture_hybrid_dual_lane(self, hybrid_result):
        """Campos de dual lane são parseados."""
        assert hybrid_result.dual_lane_filtered_doc == "LEI-14133-2021"
        assert hybrid_result.dual_lane_from_filtered == 5
        assert hybrid_result.dual_lane_from_free == 3

    def test_fixture_hybrid_query_rewrite(self, hybrid_result):
        """Campos de query rewrite são parseados."""
        assert hybrid_result.query_rewrite_clean_query == "critérios julgamento propostas licitação"
        assert hybrid_result.query_rewrite_document_id == "LEI-14133-2021"

    def test_fixture_hybrid_to_xml_roundtrip(self, hybrid_result):
        """JSON → parser → to_xml produz XML válido com endpoint='hybrid'."""
        xml = hybrid_result.to_xml("data")
        root = ET.fromstring(xml)
        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("endpoint") == "hybrid"

        # Seções obrigatórias
        assert root.find("consulta") is not None
        assert root.find("base_normativa") is not None
        assert root.find("contexto_normativo") is not None
        assert root.find("metadados") is not None

    def test_fixture_hybrid_xml_metadados(self, hybrid_result):
        """Metadados contêm hyde, tempos individuais e hits_milvus."""
        xml = hybrid_result.to_xml("data")
        root = ET.fromstring(xml)
        meta = root.find("metadados")
        assert meta is not None
        assert meta.findtext("hyde") == "true"

        # Timings são filhos diretos de <metadados> como <tempo_*_ms>
        assert meta.findtext("tempo_grafo_ms") == "32"
        assert meta.findtext("tempo_busca_ms") == "82"
        # seeds_count tem prioridade sobre hits_milvus no builder
        assert meta.findtext("hits_milvus") == "2"

    def test_fixture_hybrid_to_xml_full(self, hybrid_result):
        """to_xml('full') inclui instrucoes_completas."""
        xml = hybrid_result.to_xml("full")
        root = ET.fromstring(xml)
        assert root.find("instrucoes_completas") is not None

    def test_fixture_hybrid_to_messages(self, hybrid_result):
        """to_messages gera system+user."""
        msgs = hybrid_result.to_messages()
        assert len(msgs) == 2
        assert "hybrid" in msgs[0]["content"]

    def test_fixture_hybrid_query_interpretation(self, hybrid_result):
        """query_interpretation lê de _raw_response."""
        qi = hybrid_result.query_interpretation
        assert qi["original_query"] == "Quais os critérios de julgamento?"
        assert qi["rewritten_query"] == "critérios julgamento propostas licitação"
        assert qi["detected_document_id"] == "LEI-14133-2021"

    def test_fixture_hybrid_normative_trail(self, hybrid_result):
        """normative_trail extrai fontes."""
        trail = hybrid_result.normative_trail
        assert len(trail) >= 1
        assert any("14133" in t for t in trail)

    def test_fixture_hybrid_to_dict_passthrough(self, hybrid_result):
        """to_dict retorna _raw_response intacto."""
        d = hybrid_result.to_dict()
        assert d["confidence"] == 0.87
        assert d["hyde_used"] is True

    def test_fixture_hybrid_response_schema(self, hybrid_result):
        """to_response_schema gera schema com IDs de evidence + graph."""
        schema = hybrid_result.to_response_schema()
        assert schema is not None
        # IDs vêm tanto de direct_evidence quanto de graph_expansion
        enum_values = schema["schema"]["properties"]["fundamentacao"]["items"]["properties"]["dispositivo_id"]["enum"]
        assert "ART-033" in enum_values
        assert "ART-036" in enum_values


class TestFixtureLookup:
    """Testes usando fixture JSON real do /api/v1/lookup."""

    def test_fixture_lookup_parse(self, lookup_result):
        """Parser instancia LookupResult com hierarquia completa."""
        assert lookup_result.status == "found"
        assert lookup_result.elapsed_ms == 38.5
        assert lookup_result.match is not None
        assert lookup_result.parent is not None
        assert len(lookup_result.siblings) == 3
        assert lookup_result.resolved is not None

    def test_fixture_lookup_match(self, lookup_result):
        """Match tem todos os campos tipados."""
        m = lookup_result.match
        assert m.span_id == "PAR-018-2"
        assert m.document_id == "LEI-14133-2021"
        assert m.device_type == "paragraph"
        assert m.article_number == "18"
        assert m.evidence_url is not None

    def test_fixture_lookup_parent(self, lookup_result):
        """Parent é o artigo pai."""
        p = lookup_result.parent
        assert p.span_id == "ART-018"
        assert p.device_type == "article"

    def test_fixture_lookup_siblings(self, lookup_result):
        """Siblings incluem is_current correto."""
        sibs = lookup_result.siblings
        current = [s for s in sibs if s.is_current]
        assert len(current) == 1
        assert current[0].span_id == "PAR-018-2"

    def test_fixture_lookup_resolved(self, lookup_result):
        """Resolved tem componentes parseados."""
        r = lookup_result.resolved
        assert r["device_type"] == "paragraph"
        assert r["article_number"] == "18"
        assert r["paragraph_number"] == "2"
        assert r["resolved_document_id"] == "LEI-14133-2021"

    def test_fixture_lookup_to_xml_roundtrip(self, lookup_result):
        """JSON → parser → to_xml produz XML válido com endpoint='lookup'."""
        xml = lookup_result.to_xml("data")
        root = ET.fromstring(xml)
        assert root.tag == "vectorgov_knowledge_package"
        assert root.get("endpoint") == "lookup"

        # Hierarquia
        assert root.find("consulta") is not None
        assert root.find("hierarquia_normativa") is not None

    def test_fixture_lookup_xml_hierarquia(self, lookup_result):
        """XML contém artigo_pai, dispositivo_principal e irmaos."""
        xml = lookup_result.to_xml("data")
        root = ET.fromstring(xml)
        hier = root.find("hierarquia_normativa")
        assert hier.find("artigo_pai") is not None
        assert hier.find("dispositivo_principal") is not None
        assert hier.find("dispositivos_irmaos") is not None

        irmaos = hier.findall("dispositivos_irmaos/irmao")
        assert len(irmaos) == 3

    def test_fixture_lookup_to_xml_full(self, lookup_result):
        """to_xml('full') inclui instrucoes_completas."""
        xml = lookup_result.to_xml("full")
        root = ET.fromstring(xml)
        assert root.find("instrucoes_completas") is not None

    def test_fixture_lookup_to_messages(self, lookup_result):
        """to_messages gera system+user."""
        msgs = lookup_result.to_messages()
        assert len(msgs) == 2
        assert "lookup" in msgs[0]["content"]

    def test_fixture_lookup_to_prompt(self, lookup_result):
        """to_prompt gera string com XML + query."""
        prompt = lookup_result.to_prompt()
        assert "lookup" in prompt
        assert "Resposta:" in prompt

    def test_fixture_lookup_to_markdown(self, lookup_result):
        """to_markdown gera Markdown legível."""
        md = lookup_result.to_markdown()
        assert "PAR-018-2" in md
        assert "found" in md.lower() or "Encontrado" in md

    def test_fixture_lookup_to_dict_passthrough(self, lookup_result):
        """to_dict retorna _raw_response intacto."""
        d = lookup_result.to_dict()
        assert d["status"] == "found"
        assert d["match"]["span_id"] == "PAR-018-2"

    def test_fixture_lookup_response_schema(self, lookup_result):
        """to_response_schema coleta IDs de match+parent+siblings."""
        schema = lookup_result.to_response_schema()
        assert schema is not None
        enum_values = schema["schema"]["properties"]["fundamentacao"]["items"]["properties"]["dispositivo_id"]["enum"]
        # match + parent + siblings (deduplicado)
        assert "PAR-018-2" in enum_values
        assert "ART-018" in enum_values
        assert "PAR-018-1" in enum_values
        assert "PAR-018-3" in enum_values
