"""
Geração de payloads XML, Markdown, e JSON Schema para LLMs.

Este módulo contém a lógica de serialização dos resultados de busca
em formatos otimizados para consumo por modelos de linguagem.

Formatos disponíveis:
- XML estruturado (vectorgov_knowledge_package, 7 seções narrativas)
- Markdown legível
- JSON Schema para structured output
- Anthropic tool schema

Schema XML (7 seções):
1. consulta — o que foi perguntado
2. base_normativa — dispositivos que fundamentam (agrupados por fonte)
3. contexto_normativo — relacionamentos via grafo
4. notas_especialista — curadoria humana (opcional)
5. jurisprudencia — TCU (opcional)
6. trilha_verificavel — links para PDFs originais
7. metadados — transparência operacional

Três níveis de instrução:
- "data": só dados (7 seções), sem instruções
- "instructions": dados + <instrucoes> com 7 regras operacionais
- "full": dados + <instrucoes_completas> com anti-alucinação e contrato dinâmico
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import OrderedDict
from typing import TYPE_CHECKING, Optional
from urllib.parse import quote
from xml.sax.saxutils import escape as _sax_escape

if TYPE_CHECKING:
    from vectorgov.models import Hit, SearchResult, HybridResult, LookupResult


# =============================================================================
# CACHE DE XML BASE (árvores estáticas)
# =============================================================================

_XML_CACHE: dict[str, str] = {}


def _get_xml_base(level: str) -> str:
    """Retorna XML base (parte estática) cacheado por nível.

    A parte estática (instruções, anti-alucinação, formato, etc.) é idêntica
    entre chamadas. Cachear evita reconstruir a árvore ElementTree toda vez.
    """
    if level not in _XML_CACHE:
        _XML_CACHE[level] = _build_xml_base(level)
    return _XML_CACHE[level]


def _build_xml_base(level: str) -> str:
    """Constrói a parte estática do XML para um nível de instrução."""
    root = ET.Element("_base")
    if level == "instructions":
        instrucoes = ET.SubElement(root, "instrucoes")
        # Lazy import evita circular
        for regra_text in _INSTRUCOES_REGRAS:
            ET.SubElement(instrucoes, "regra").text = regra_text
    elif level == "full":
        ic = ET.SubElement(root, "instrucoes_completas")
        ET.SubElement(ic, "papel").text = _PAPEL_TEXT
        aa = ET.SubElement(ic, "anti_alucinacao")
        for rule in _ANTI_ALUCINACAO_REGRAS:
            r = ET.SubElement(aa, "regra")
            r.set("prioridade", rule["prioridade"])
            r.text = rule["texto"]
        fc = ET.SubElement(ic, "formato_citacao")
        for text in _FORMATO_CITACAO_REGRAS:
            ET.SubElement(fc, "regra").text = text
        er = ET.SubElement(ic, "estrutura_resposta")
        for text in _ESTRUTURA_RESPOSTA_REGRAS:
            ET.SubElement(er, "regra").text = text
        mgd = ET.SubElement(ic, "modo_geracao_documento")
        mgd.set("condition", "quando o usuário pedir geração de documento")
        for text in _MODO_GERACAO_DOC_REGRAS:
            ET.SubElement(mgd, "regra").text = text
    return _element_to_string(root)


# =============================================================================
# ESCAPE XML
# =============================================================================


def escape_xml(text: Optional[str]) -> str:
    """Escape de caracteres especiais para XML válido.

    Converte ``&``, ``<``, ``>``, ``"`` nas entidades XML correspondentes.
    Strings vazias ou ``None`` retornam string vazia.
    Não realiza double-escaping.

    Args:
        text: Texto a escapar.

    Returns:
        Texto com caracteres especiais escapados.
    """
    if text is None:
        return ""
    if not text:
        return ""
    return _sax_escape(text, {'"': "&quot;"})


# =============================================================================
# CONSTANTES — INSTRUÇÕES LEVES (level "instructions")
# =============================================================================

_INSTRUCOES_REGRAS = [
    "Baseie sua resposta EXCLUSIVAMENTE nos dispositivos fornecidos "
    "em base_normativa e contexto_normativo.",
    "Cite cada dispositivo usando: [Lei 14.133/2021, Art. 33, Inc. III]",
    "Se a informação não estiver nos dispositivos, "
    "diga que não encontrou fundamentação.",
    "Quando houver notas_especialista, incorpore como observação prática.",
    "Quando houver jurisprudencia, cite como entendimento do TCU.",
    "Priorize dispositivos com score mais alto (aparecem primeiro).",
    "Use linguagem formal adequada ao contexto jurídico-administrativo.",
]


# =============================================================================
# CONSTANTES — INSTRUÇÕES COMPLETAS (level "full")
# =============================================================================

_PAPEL_TEXT = (
    "Você é um assistente especializado em legislação brasileira de licitações e contratos "
    "públicos. Sua função é responder perguntas com base EXCLUSIVAMENTE nos dispositivos "
    "legais fornecidos neste Knowledge Package."
)

_ANTI_ALUCINACAO_REGRAS: list[dict[str, str]] = [
    {
        "prioridade": "critica",
        "texto": (
            "NUNCA invente, extrapole ou cite dispositivos que não estejam "
            "presentes neste Knowledge Package. Se a informação necessária não estiver aqui, diga "
            'explicitamente: "Não encontrei fundamentação nos dispositivos consultados."'
        ),
    },
    {
        "prioridade": "critica",
        "texto": (
            "NUNCA cite números de artigo, inciso, parágrafo ou alínea "
            "que não apareçam explicitamente no XML. Cada dispositivo tem um id único — use-o."
        ),
    },
    {
        "prioridade": "alta",
        "texto": (
            "Quando houver conflito aparente entre dispositivos, cite ambos "
            "e indique a possível divergência ao invés de escolher um."
        ),
    },
]

_FORMATO_CITACAO_REGRAS = [
    "Cite dispositivos no formato: [Lei 14.133/2021, Art. 33, Inc. III]",
    "Para parágrafos: [Lei 14.133/2021, Art. 36, §2º]",
    "Para normas infralegais: [IN 65/2021, Art. 4º]",
    "Para jurisprudência: [Acórdão XXXX/YYYY-TCU-Plenário]",
]

_ESTRUTURA_RESPOSTA_REGRAS = [
    "Comece com uma resposta direta e objetiva à pergunta.",
    "Em seguida, apresente a fundamentação legal com citações.",
    "Se houver notas de especialista, incorpore como observação prática.",
    "Se houver jurisprudência, cite como entendimento do TCU.",
    "Use linguagem formal adequada ao contexto jurídico-administrativo.",
]

_MODO_GERACAO_DOC_REGRAS = [
    "Para geração de documentos (ETP, TR, parecer), estruture a saída com "
    "seções e subseções numeradas.",
    "Cada seção deve ter fundamentação legal explícita.",
    "Inclua campos obrigatórios conforme a legislação citada.",
]

_FORMATO_OBRIGATORIO_TEXT = (
    "Sua resposta DEVE seguir exatamente esta estrutura:\n\n"
    "1. RESPOSTA DIRETA (1-3 frases objetivas)\n"
    "2. FUNDAMENTAÇÃO LEGAL (cada afirmação com [citação])\n"
    "3. OBSERVAÇÕES PRÁTICAS (somente se houver notas_especialista acima)\n"
    "4. ENTENDIMENTO DO TCU (somente se houver jurisprudencia acima)\n\n"
    "REGRA: toda frase com informação jurídica DEVE ter uma referência "
    "entre colchetes a um dispositivo de base_normativa ou contexto_normativo. "
    "Frase sem referência = frase proibida.\n\n"
    "REGRA DE HIPERLINK: ao citar um dispositivo, crie um link Markdown "
    "usando a URL correspondente em <trilha_verificavel>. "
    "Formato: [Lei 14.133/2021, Art. 33, Inc. III](evidence_url_do_dispositivo) "
    "Se o dispositivo não tem evidence_url, cite sem link."
)

_VERIFICACAO_FINAL_TEXT = (
    "Antes de enviar sua resposta, verifique:\n"
    "- Toda afirmação jurídica tem referência a um dispositivo autorizado?\n"
    "- Nenhum artigo/inciso/parágrafo citado está fora da lista autorizada?\n"
    "- Cada citação tem hiperlink Markdown para a evidence_url correspondente?\n"
    "- Se não encontrou a informação, disse explicitamente?"
)


# =============================================================================
# XML BUILDERS
# =============================================================================


def build_xml(result: SearchResult, level: str = "data") -> str:
    """Gera payload XML no formato vectorgov_knowledge_package.

    Todas as 7 seções de dados são incluídas em TODOS os níveis
    (com omissão de tags vazias via Regra 1). A diferença entre níveis
    é apenas quais instruções são adicionadas.

    Três níveis de instrução:
      - "data": só dados (7 seções), sem instruções
      - "instructions": dados + <instrucoes> com 7 regras operacionais
      - "full": dados + <instrucoes_completas> com anti-alucinação e contrato dinâmico

    Args:
        result: Resultado de busca do SDK.
        level: Nível de instrução.

    Returns:
        String XML pretty-printed.
    """
    if level not in ("data", "instructions", "full"):
        raise ValueError(f"level inválido: {level!r}. Use 'data', 'instructions' ou 'full'.")

    root = ET.Element("vectorgov_knowledge_package")
    root.set("version", "1.0")
    root.set("level", level)

    # Instruções vêm ANTES das seções de dados
    if level == "instructions":
        _build_instrucoes_element(root)
    elif level == "full":
        _build_instrucoes_completas_element(result, root)

    # Todas as 7 seções de dados, com Regra 1 (tags vazias omitidas)
    _build_consulta_element(result, root)           # 1
    _build_base_normativa_element(result, root)      # 2
    if result.expanded_chunks:                       # 3
        _build_contexto_normativo_element(result, root)
    _build_notas_especialista_element(result, root)  # 4
    _build_jurisprudencia_element(result, root)      # 5
    _build_trilha_verificavel_element(result, root)  # 6
    _build_metadados_element(result, root)           # 7

    return _element_to_string(root)


def build_prompt_xml(
    result: SearchResult,
    query: Optional[str] = None,
    level: str = "instructions",
) -> str:
    """Gera um prompt único com XML + query (para Gemini e similares).

    Args:
        result: Resultado de busca.
        query: Pergunta do usuário (usa result.query se omitido).
        level: Nível de detalhe do XML.

    Returns:
        String com XML seguido da query.
    """
    query = query or result.query
    xml = build_xml(result, level=level)
    return f"{xml}\n\nPergunta: {query}\n\nResposta:"


def build_messages_xml(
    result: SearchResult,
    query: Optional[str] = None,
    level: str = "instructions",
) -> list[dict[str, str]]:
    """Gera lista de mensagens com XML no system e query no user.

    Args:
        result: Resultado de busca.
        query: Pergunta do usuário (usa result.query se omitido).
        level: Nível de detalhe do XML.

    Returns:
        Lista de dicts no formato OpenAI/Anthropic chat messages.
    """
    query = query or result.query
    xml = build_xml(result, level=level)

    return [
        {"role": "system", "content": xml},
        {"role": "user", "content": query},
    ]


# =============================================================================
# MARKDOWN BUILDER
# =============================================================================


def build_markdown(result: SearchResult) -> str:
    """Gera Markdown legível a partir de um SearchResult.

    Args:
        result: Resultado de busca.

    Returns:
        String Markdown formatada.
    """
    parts: list[str] = []

    parts.append(f"# Resultados para: {result.query}\n")
    parts.append(f"**Modo:** {result.mode} | **Latência:** {result.latency_ms}ms | "
                 f"**Cache:** {'sim' if result.cached else 'não'}\n")

    if not result.hits:
        parts.append("_Nenhum resultado encontrado._\n")
        return "\n".join(parts)

    # Dispositivos
    parts.append("## Dispositivos\n")
    for i, hit in enumerate(result.hits, 1):
        parts.append(f"### [{i}] {hit.source} (score: {hit.score:.3f})\n")
        parts.append(f"{hit.text}\n")

        if hit.nota_especialista:
            parts.append(f"> **Nota do Especialista:** {hit.nota_especialista}\n")
        if hit.jurisprudencia_tcu:
            parts.append(f"> **Jurisprudência TCU:** {hit.jurisprudencia_tcu}")
            if hit.acordao_tcu_link:
                parts.append(f" ([link]({hit.acordao_tcu_link}))")
            parts.append("\n")

    # Trechos citados
    if result.expanded_chunks:
        parts.append("## Trechos Citados (expansão por citação)\n")
        for j, ec in enumerate(result.expanded_chunks, 1):
            source_info = ec.source_chunk_id or "(origem não informada)"
            parts.append(f"### [XC-{j}] {ec.document_id}, {ec.span_id}\n")
            parts.append(f"- **Citado por:** {source_info}\n")
            if ec.source_citation_raw:
                parts.append(f"- **Citação original:** {ec.source_citation_raw}\n")
            parts.append(f"\n{ec.text}\n")

    # Stats
    if result.expansion_stats:
        s = result.expansion_stats
        parts.append(
            f"\n---\n_Expansão: {s.expanded_chunks_count} expandidos, "
            f"{s.citations_scanned_count} encontradas, "
            f"{s.citations_resolved_count} resolvidas, "
            f"{s.expansion_time_ms:.0f}ms_\n"
        )

    return "\n".join(parts)


# =============================================================================
# JSON SCHEMA BUILDER
# =============================================================================


def build_response_schema(
    result: SearchResult,
    include_jurisprudencia: bool = False,
    include_observacoes: bool = False,
) -> Optional[dict]:
    """Gera JSON Schema para structured output (response_format).

    O schema restringe o enum de `dispositivo_id` aos IDs
    efetivamente presentes nos resultados, prevenindo alucinação
    mecanicamente via constrained decoding.

    Args:
        result: Resultado de busca (usado para extrair IDs válidos).
        include_jurisprudencia: Mantido para compatibilidade. Os campos
            nullable são sempre incluídos no schema.
        include_observacoes: Mantido para compatibilidade.

    Returns:
        Dict com wrapper {name, strict, schema}, ou None se não houver hits.
    """
    if not result.hits:
        return None

    authorized_ids, _evidence_map = _collect_authorized_ids(result)
    if not authorized_ids:
        return None

    schema = {
        "type": "object",
        "properties": {
            "resposta_direta": {
                "type": "string",
                "description": (
                    "Resposta objetiva à pergunta em 1-3 frases, "
                    "baseada exclusivamente nos dispositivos fornecidos"
                ),
            },
            "fundamentacao": {
                "type": "array",
                "description": (
                    "Lista de afirmações jurídicas, cada uma vinculada "
                    "a um dispositivo-fonte"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "afirmacao": {
                            "type": "string",
                            "description": "Afirmação jurídica baseada no dispositivo",
                        },
                        "dispositivo_id": {
                            "type": "string",
                            "enum": authorized_ids,
                            "description": (
                                "ID do dispositivo (RESTRITO aos retornados na busca)"
                            ),
                        },
                        "citacao_formatada": {
                            "type": "string",
                            "description": (
                                "Citação legível: Lei 14.133/2021, Art. 33, Inc. III"
                            ),
                        },
                        "evidence_link": {
                            "type": ["string", "null"],
                            "description": (
                                "URL de evidência do dispositivo para hiperlink "
                                "verificável. null se não disponível"
                            ),
                        },
                    },
                    "required": ["afirmacao", "dispositivo_id", "citacao_formatada"],
                    "additionalProperties": False,
                },
            },
            "observacoes_praticas": {
                "type": ["string", "null"],
                "description": (
                    "Notas do especialista incorporadas. "
                    "null se não houver notas_especialista no XML"
                ),
            },
            "jurisprudencia_tcu": {
                "type": ["string", "null"],
                "description": (
                    "Entendimento do TCU. "
                    "null se não houver jurisprudencia no XML"
                ),
            },
            "dispositivos_nao_utilizados": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": authorized_ids,
                },
                "description": (
                    "IDs dos dispositivos fornecidos que não foram "
                    "relevantes para a resposta"
                ),
            },
            "informacao_insuficiente": {
                "type": "boolean",
                "description": (
                    "true se os dispositivos fornecidos não foram "
                    "suficientes para responder completamente"
                ),
            },
        },
        "required": [
            "resposta_direta",
            "fundamentacao",
            "informacao_insuficiente",
        ],
        "additionalProperties": False,
    }

    return {
        "name": "resposta_juridica_vectorgov",
        "strict": True,
        "schema": schema,
    }


def build_anthropic_tool_schema(result: SearchResult) -> Optional[dict]:
    """Gera schema no formato Anthropic tool_use para structured output.

    Args:
        result: Resultado de busca.

    Returns:
        Dict no formato Anthropic tool, ou None se não houver hits.
    """
    wrapper = build_response_schema(result)
    if wrapper is None:
        return None

    return {
        "name": wrapper["name"],
        "description": (
            "Gera uma resposta jurídica fundamentada nos dispositivos legais fornecidos. "
            "Use APENAS as fontes listadas no enum de dispositivo_id."
        ),
        "input_schema": wrapper["schema"],
    }


# =============================================================================
# XML SECTION BUILDERS (7 seções narrativas)
# =============================================================================


def _build_consulta_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 1: <consulta> — informações sobre a query."""
    consulta = ET.SubElement(root, "consulta")
    ET.SubElement(consulta, "query_original").text = result.query

    # query interpretada (da _raw_response, ou fallback para original)
    interpreted = result.query
    if result._raw_response and "query_interpretation" in result._raw_response:
        qi = result._raw_response["query_interpretation"]
        interpreted = qi.get("rewritten_query", result.query)
    ET.SubElement(consulta, "query_interpretada").text = interpreted

    ET.SubElement(consulta, "confianca_global").text = f"{_calculate_confidence(result):.4f}"
    ET.SubElement(consulta, "estrategia").text = result.mode


def _build_base_normativa_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 2: <base_normativa> — dispositivos agrupados por fonte (Regra 3).

    Regras aplicadas:
    - Regra 3: Agrupamento por fonte normativa
    - Regra 4: Ordenação por score decrescente dentro de cada fonte
    - Regra 5: Apenas evidência direta (relevancia="direta")
    """
    if not result.hits:
        return

    base = ET.SubElement(root, "base_normativa")
    groups = _group_hits_by_source(result.hits)

    for _key, group in groups.items():
        fonte = ET.SubElement(base, "fonte")
        fonte.set("lei", group["lei"])
        fonte.set("tipo", group["tipo"])
        fonte.set("relevancia", "direta")

        # Regra 4: ordenar por score decrescente; desempate por canonical_start
        sorted_hits = sorted(
            group["hits"],
            key=lambda h: (-h.score, h.canonical_start if h.canonical_start is not None else float("inf")),
        )

        for hit in sorted_hits:
            _build_dispositivo_element(hit, fonte)


def _build_dispositivo_element(hit: Hit, parent: ET.Element) -> None:
    """Constrói <dispositivo> individual dentro de <fonte>.

    Regra 5: article_consolidated → tipo="artigo_consolidado"
    Regra 6: origin_type != "self" → atributos origem/origem_ref
    """
    disp = ET.SubElement(parent, "dispositivo")

    span_id = _extract_span_id(hit.chunk_id)
    disp.set("id", span_id)

    # Tipo: prioriza device_type explícito do metadata (Regra 5: article_consolidated)
    m = hit.metadata
    if m.device_type == "article_consolidated":
        tipo = "artigo_consolidado"
    elif m.device_type:
        # Mapeia device_type da API para label XML
        _DEVICE_MAP = {
            "article": "artigo",
            "paragraph": "paragrafo",
            "inciso": "inciso",
            "alinea": "alinea",
        }
        tipo = _DEVICE_MAP.get(m.device_type, m.device_type)
    elif m.item:
        tipo = "inciso"
    elif m.paragraph:
        tipo = "paragrafo"
    elif m.article:
        tipo = "artigo"
    else:
        tipo = "dispositivo"
    disp.set("tipo", tipo)

    if m.article:
        disp.set("artigo", str(m.article))

    if m.device_type == "article_consolidated":
        disp.set("score", "consolidado")
    else:
        disp.set("score", f"{hit.score:.4f}")

    # Evidence URL (construída a partir do chunk_id)
    if hit.chunk_id:
        disp.set("evidence_url", f"/api/v1/evidence/{quote(hit.chunk_id, safe='')}")

    # Score do reranker puro (antes de boosts)
    if hit.pure_rerank_score is not None:
        disp.set("score_rerank", f"{hit.pure_rerank_score:.4f}")

    # Regra 6: Proveniência normativa
    if hit.origin_type and hit.origin_type != "self":
        disp.set("origem", "referencia_cruzada")
        if hit.origin_reference:
            disp.set("origem_ref", hit.origin_reference)

    # stitched_text tem prioridade sobre text
    disp.text = hit.stitched_text or hit.text or ""


def _build_contexto_normativo_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 3: <contexto_normativo> — dispositivos expandidos via grafo (Regra 5)."""
    ctx = ET.SubElement(root, "contexto_normativo")

    for ec in result.expanded_chunks:
        disp = ET.SubElement(ctx, "dispositivo_relacionado")
        disp.set("id", ec.span_id or "")
        disp.set("lei", ec.document_id or "")
        disp.set("relacao", ec.relacao)
        disp.set("hop", str(ec.hop))
        disp.text = ec.text or ""


def _build_notas_especialista_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 4: <notas_especialista> — omitida se nenhum hit tem nota (Regra 1)."""
    notas = [(hit, hit.nota_especialista) for hit in result.hits if hit.nota_especialista]
    if not notas:
        return

    section = ET.SubElement(root, "notas_especialista")
    for hit, nota in notas:
        el = ET.SubElement(section, "nota")
        el.set("dispositivo_ref", _extract_span_id(hit.chunk_id))
        el.text = nota


def _build_jurisprudencia_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 5: <jurisprudencia> — omitida se nenhum hit tem jurisprudência (Regra 1)."""
    juris = [(hit, hit.jurisprudencia_tcu) for hit in result.hits if hit.jurisprudencia_tcu]
    if not juris:
        return

    section = ET.SubElement(root, "jurisprudencia")
    for hit, texto in juris:
        ac = ET.SubElement(section, "acordao")
        ac.set("dispositivo_ref", _extract_span_id(hit.chunk_id))
        if hit.acordao_tcu_key:
            ac.set("chave", hit.acordao_tcu_key)
        if hit.acordao_tcu_link:
            ac.set("link", hit.acordao_tcu_link)
        ac.text = texto


def _build_trilha_verificavel_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 6: <trilha_verificavel> — links para PDFs originais."""
    hits_with_id = [h for h in result.hits if h.chunk_id]
    if not hits_with_id:
        return

    trilha = ET.SubElement(root, "trilha_verificavel")
    for hit in hits_with_id:
        ev = ET.SubElement(trilha, "evidencia")
        ev.set("dispositivo_ref", _extract_span_id(hit.chunk_id))
        ev.set("url", f"/api/v1/evidence/{quote(hit.chunk_id, safe='')}")
        if hit.page_number is not None:
            ev.set("pagina", str(hit.page_number))
        if hit.canonical_hash:
            ev.set("hash", hit.canonical_hash)


# =============================================================================
# INSTRUÇÕES — level "instructions" (7 regras leves)
# =============================================================================


def _build_instrucoes_element(root: ET.Element) -> None:
    """Constrói <instrucoes> com 7 regras operacionais leves."""
    instrucoes = ET.SubElement(root, "instrucoes")
    for regra_text in _INSTRUCOES_REGRAS:
        ET.SubElement(instrucoes, "regra").text = regra_text


# =============================================================================
# INSTRUÇÕES COMPLETAS — level "full" (anti-alucinação + contrato dinâmico)
# =============================================================================


def _build_instrucoes_completas_element(
    result: SearchResult,
    root: ET.Element,
) -> None:
    """Constrói <instrucoes_completas> com sistema anti-alucinação e contrato dinâmico."""
    ic = ET.SubElement(root, "instrucoes_completas")

    # <papel>
    ET.SubElement(ic, "papel").text = _PAPEL_TEXT

    # <anti_alucinacao>
    aa = ET.SubElement(ic, "anti_alucinacao")
    for rule in _ANTI_ALUCINACAO_REGRAS:
        r = ET.SubElement(aa, "regra")
        r.set("prioridade", rule["prioridade"])
        r.text = rule["texto"]

    # <formato_citacao>
    fc = ET.SubElement(ic, "formato_citacao")
    for text in _FORMATO_CITACAO_REGRAS:
        ET.SubElement(fc, "regra").text = text

    # <estrutura_resposta>
    er = ET.SubElement(ic, "estrutura_resposta")
    for text in _ESTRUTURA_RESPOSTA_REGRAS:
        ET.SubElement(er, "regra").text = text

    # <modo_geracao_documento>
    mgd = ET.SubElement(ic, "modo_geracao_documento")
    mgd.set("condition", "quando o usuário pedir geração de documento")
    for text in _MODO_GERACAO_DOC_REGRAS:
        ET.SubElement(mgd, "regra").text = text

    # <contrato_resposta> — gerado dinamicamente
    _build_contrato_resposta(result, ic)


def _build_contrato_resposta(
    result: SearchResult,
    parent: ET.Element,
) -> None:
    """Constrói <contrato_resposta> com whitelist dinâmica e mapa de evidências."""
    cr = ET.SubElement(parent, "contrato_resposta")

    # <formato_obrigatorio>
    ET.SubElement(cr, "formato_obrigatorio").text = _FORMATO_OBRIGATORIO_TEXT

    # Coleta IDs autorizados e mapa de evidências
    authorized_ids, evidence_map = _collect_authorized_ids(result)

    # <dispositivos_autorizados>
    if authorized_ids:
        ET.SubElement(cr, "dispositivos_autorizados").text = (
            "Você SÓ pode citar os seguintes IDs. Qualquer outro é alucinação:\n"
            + ", ".join(authorized_ids)
        )

    # <mapa_evidencias>
    if evidence_map:
        lines = [f"{sid} \u2192 {url}" for sid, url in evidence_map.items()]
        ET.SubElement(cr, "mapa_evidencias").text = "\n".join(lines)

    # <verificacao_final>
    ET.SubElement(cr, "verificacao_final").text = _VERIFICACAO_FINAL_TEXT


# =============================================================================
# METADADOS
# =============================================================================


def _build_metadados_element(result: SearchResult, root: ET.Element) -> None:
    """Seção 7: <metadados> — transparência operacional."""
    meta = ET.SubElement(root, "metadados")
    ET.SubElement(meta, "pipeline").text = "fenix"
    ET.SubElement(meta, "tempo_total_ms").text = str(result.latency_ms)

    # Reranker: tenta extrair da raw_response, senão assume true
    reranker = True
    if result._raw_response and "reranker" in result._raw_response:
        reranker = bool(result._raw_response["reranker"])
    ET.SubElement(meta, "reranker").text = str(reranker).lower()

    has_graph = bool(result.expanded_chunks)
    ET.SubElement(meta, "grafo_expandido").text = str(has_graph).lower()
    ET.SubElement(meta, "cache_hit").text = str(result.cached).lower()

    ET.SubElement(meta, "query_id").text = result.query_id or ""

    if result.expansion_stats:
        es = result.expansion_stats
        exp = ET.SubElement(meta, "expansao")
        ET.SubElement(exp, "expandidos").text = str(es.expanded_chunks_count)
        ET.SubElement(exp, "citacoes_encontradas").text = str(es.citations_scanned_count)
        ET.SubElement(exp, "citacoes_resolvidas").text = str(es.citations_resolved_count)
        ET.SubElement(exp, "tempo_ms").text = f"{es.expansion_time_ms:.0f}"


# =============================================================================
# HELPERS INTERNOS
# =============================================================================


def _extract_span_id(chunk_id: str) -> str:
    """Extrai span_id do chunk_id (parte após #)."""
    if not chunk_id:
        return ""
    if "#" in chunk_id:
        return chunk_id.split("#", 1)[1]
    return chunk_id


def _group_hits_by_source(hits: list) -> OrderedDict:
    """Agrupa hits por fonte normativa (Regra 3).

    Returns:
        OrderedDict preservando a ordem de primeira aparição.
    """
    groups: OrderedDict = OrderedDict()
    for hit in hits:
        m = hit.metadata
        doc_type = (m.document_type or "DOC").upper()
        doc_num = m.document_number or "?"
        doc_year = str(m.year) if m.year else "?"
        key = f"{doc_type}|{doc_num}|{doc_year}"

        if key not in groups:
            groups[key] = {
                "lei": f"{doc_num}/{doc_year}",
                "tipo": doc_type,
                "hits": [],
            }
        groups[key]["hits"].append(hit)
    return groups


def _calculate_confidence(result: SearchResult) -> float:
    """Calcula score de confiança do resultado.

    Fórmula:
    - Base: média ponderada das relevâncias (peso = score²)
    - Penalidade: se menos de 2 hits, reduz 20%
    - Bonus: se top hit score > 0.9, adiciona 5%

    Returns:
        Float entre 0.0 e 1.0.
    """
    if not result.hits:
        return 0.0

    scores = [h.score for h in result.hits]

    # Média ponderada (peso = score²)
    weights = [s * s for s in scores]
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0

    confidence = sum(s * w for s, w in zip(scores, weights)) / total_weight

    # Penalidade por poucos hits
    if len(scores) < 2:
        confidence *= 0.8

    # Bonus por top hit forte
    if scores[0] > 0.9:
        confidence = min(1.0, confidence + 0.05)

    return round(min(1.0, max(0.0, confidence)), 4)


def _extract_normative_trail(result: SearchResult) -> list[str]:
    """Extrai lista deduplicada de fontes normativas dos hits.

    Returns:
        Lista de nomes de documentos (ex: ["LEI 14133/2021", "IN 65/2021"]).
    """
    seen: set[str] = set()
    trail: list[str] = []

    for hit in result.hits:
        m = hit.metadata
        # Formata nome legível
        doc_type = m.document_type.upper() if m.document_type else "DOC"
        doc_num = m.document_number or "?"
        doc_year = m.year or "?"
        name = f"{doc_type} {doc_num}/{doc_year}"

        if name not in seen:
            seen.add(name)
            trail.append(name)

    return trail


def _collect_ids(
    hits: list,
    expanded: Optional[list] = None,
    *,
    with_evidence: bool = False,
) -> tuple[list[str], dict[str, str]] | list[str]:
    """Coleta IDs autorizados (e opcionalmente mapa de evidências) de hits + expanded.

    Função unificada que substitui as 3 variantes anteriores.

    Args:
        hits: Lista de Hit (ou qualquer objeto com .chunk_id).
        expanded: Lista de ExpandedChunk/GraphNode (ou qualquer objeto com .span_id e .chunk_id).
        with_evidence: Se True, retorna tupla (ids, evidence_map). Se False, retorna só ids.

    Returns:
        Se with_evidence=True: Tupla (authorized_ids, evidence_map).
        Se with_evidence=False: Lista authorized_ids.
    """
    authorized_ids: list[str] = []
    evidence_map: dict[str, str] = {}

    for hit in hits:
        span_id = _extract_span_id(hit.chunk_id)
        if span_id and span_id not in authorized_ids:
            authorized_ids.append(span_id)
            if with_evidence and hit.chunk_id:
                evidence_map[span_id] = f"/api/v1/evidence/{quote(hit.chunk_id, safe='')}"

    for ec in (expanded or []):
        if ec.span_id and ec.span_id not in authorized_ids:
            authorized_ids.append(ec.span_id)
            if with_evidence and ec.chunk_id:
                evidence_map[ec.span_id] = f"/api/v1/evidence/{quote(ec.chunk_id, safe='')}"

    if with_evidence:
        return authorized_ids, evidence_map
    return authorized_ids


def _collect_authorized_ids(result: SearchResult) -> tuple[list[str], dict[str, str]]:
    """Coleta IDs autorizados e mapa de evidências de um SearchResult.

    Wrapper de compatibilidade sobre ``_collect_ids()``.
    """
    return _collect_ids(result.hits, result.expanded_chunks, with_evidence=True)  # type: ignore[return-value]


def _get_hits(result) -> list:
    """Retorna lista de hits de SearchResult ou HybridResult (duck-typing)."""
    return result.hits


def _get_expanded(result) -> list:
    """Retorna lista de expanded chunks de SearchResult ou HybridResult."""
    if hasattr(result, "graph_nodes"):
        return result.graph_nodes
    return result.expanded_chunks


# =============================================================================
# HYBRID XML BUILDERS
# =============================================================================


def build_hybrid_xml(result: HybridResult, level: str = "data") -> str:
    """Gera payload XML para resultado de busca híbrida.

    Args:
        result: Resultado de busca híbrida.
        level: Nível de instrução ("data", "instructions", "full").

    Returns:
        String XML pretty-printed.
    """
    if level not in ("data", "instructions", "full"):
        raise ValueError(f"level inválido: {level!r}. Use 'data', 'instructions' ou 'full'.")

    root = ET.Element("vectorgov_knowledge_package")
    root.set("version", "1.0")
    root.set("level", level)
    root.set("endpoint", "hybrid")

    # Instruções
    if level == "instructions":
        _build_instrucoes_element(root)
    elif level == "full":
        _build_instrucoes_completas_for_hybrid(result, root)

    # Seções de dados
    _build_hybrid_consulta_element(result, root)
    _build_hybrid_base_normativa_element(result, root)
    if result.graph_nodes:
        _build_hybrid_contexto_normativo_element(result, root)
    _build_notas_especialista_for_hits(result.hits, root)
    _build_jurisprudencia_for_hits(result.hits, root)
    _build_trilha_verificavel_for_hits(result.hits, root)
    _build_hybrid_metadados_element(result, root)

    return _element_to_string(root)


def build_hybrid_prompt_xml(
    result: HybridResult,
    query: Optional[str] = None,
    level: str = "instructions",
) -> str:
    """Gera prompt único com XML + query para hybrid."""
    query = query or result.query
    xml = build_hybrid_xml(result, level=level)
    return f"{xml}\n\nPergunta: {query}\n\nResposta:"


def build_hybrid_messages_xml(
    result: HybridResult,
    query: Optional[str] = None,
    level: str = "instructions",
) -> list[dict[str, str]]:
    """Gera lista de mensagens com XML no system e query no user para hybrid."""
    query = query or result.query
    xml = build_hybrid_xml(result, level=level)
    return [
        {"role": "system", "content": xml},
        {"role": "user", "content": query},
    ]


def build_hybrid_markdown(result: HybridResult) -> str:
    """Gera Markdown legível a partir de um HybridResult."""
    parts: list[str] = []

    parts.append(f"# Resultados Híbridos para: {result.query}\n")
    parts.append(
        f"**Modo:** {result.mode} | **Confiança:** {result.confidence:.3f} | "
        f"**Tempo:** {result.search_time_ms:.0f}ms | "
        f"**Cache:** {'sim' if result.cached else 'não'}\n"
    )

    if result.hyde_used:
        parts.append(f"**HyDE:** ativo\n")
    if result.docfilter_active and result.docfilter_detected_doc_id:
        parts.append(f"**Doc Foco:** {result.docfilter_detected_doc_id}\n")

    if not result.hits:
        parts.append("_Nenhum resultado encontrado._\n")
        return "\n".join(parts)

    parts.append("## Evidências Diretas\n")
    for i, hit in enumerate(result.hits, 1):
        parts.append(f"### [{i}] {hit.source} (score: {hit.score:.3f})\n")
        parts.append(f"{hit.stitched_text or hit.text}\n")
        if hit.nota_especialista:
            parts.append(f"> **Nota do Especialista:** {hit.nota_especialista}\n")
        if hit.jurisprudencia_tcu:
            parts.append(f"> **Jurisprudência TCU:** {hit.jurisprudencia_tcu}\n")

    if result.graph_nodes:
        parts.append("## Expansão via Grafo\n")
        for j, hit in enumerate(result.graph_nodes, 1):
            parts.append(
                f"### [G-{j}] {hit.document_id}, {hit.span_id} "
                f"(hop={hit.hop}, freq={hit.frequency})\n"
            )
            parts.append(f"{hit.text}\n")

    return "\n".join(parts)


def _build_hybrid_consulta_element(result: HybridResult, root: ET.Element) -> None:
    """Seção 1 (hybrid): <consulta> com doc_foco e backend confidence."""
    consulta = ET.SubElement(root, "consulta")
    if result.docfilter_detected_doc_id:
        consulta.set("doc_foco", result.docfilter_detected_doc_id)

    ET.SubElement(consulta, "query_original").text = result.query

    # Query interpretada
    interpreted = result.query
    if result.query_rewrite_active and result.query_rewrite_clean_query:
        interpreted = result.query_rewrite_clean_query
    ET.SubElement(consulta, "query_interpretada").text = interpreted

    ET.SubElement(consulta, "confianca_global").text = f"{result.confidence:.4f}"

    # Estrategia composta: mode + dual_lane + doc_foco
    estrategia = result.mode
    if result.dual_lane_active:
        estrategia += ":dual_lane"
    if result.docfilter_detected_doc_id:
        estrategia += f" (doc_foco={result.docfilter_detected_doc_id})"
    ET.SubElement(consulta, "estrategia").text = estrategia


def _build_hybrid_base_normativa_element(result: HybridResult, root: ET.Element) -> None:
    """Seção 2 (hybrid): <base_normativa> usando direct_evidence."""
    if not result.hits:
        return

    base = ET.SubElement(root, "base_normativa")
    groups = _group_hits_by_source(result.hits)

    for _key, group in groups.items():
        fonte = ET.SubElement(base, "fonte")
        fonte.set("lei", group["lei"])
        fonte.set("tipo", group["tipo"])
        fonte.set("relevancia", "direta")

        sorted_hits = sorted(
            group["hits"],
            key=lambda h: (-h.score, h.canonical_start if h.canonical_start is not None else float("inf")),
        )
        for hit in sorted_hits:
            _build_dispositivo_element(hit, fonte)


def _build_hybrid_contexto_normativo_element(result: HybridResult, root: ET.Element) -> None:
    """Seção 3 (hybrid): <contexto_normativo> com freq e origem."""
    ctx = ET.SubElement(root, "contexto_normativo")

    _DEVICE_MAP_PT = {
        "article": "artigo",
        "paragraph": "paragrafo",
        "inciso": "inciso",
        "alinea": "alinea",
    }

    for hit in result.graph_nodes:
        disp = ET.SubElement(ctx, "dispositivo_relacionado")
        disp.set("id", hit.span_id or "")
        disp.set("lei", hit.document_id or "")
        if hit.device_type:
            disp.set("tipo", _DEVICE_MAP_PT.get(hit.device_type, hit.device_type))
        disp.set("hop", str(hit.hop))
        if hit.frequency:
            disp.set("freq", str(hit.frequency))
        disp.text = hit.text or ""


def _build_hybrid_metadados_element(result: HybridResult, root: ET.Element) -> None:
    """Seção 7 (hybrid): <metadados> flat com timings e stats."""
    meta = ET.SubElement(root, "metadados")
    ET.SubElement(meta, "pipeline").text = "fenix"
    ET.SubElement(meta, "tempo_total_ms").text = str(int(result.search_time_ms))

    # Timings flat (direto em metadados, sem wrapper)
    if result.stats:
        timings_data = result.stats.get("timings", {})
        for src_key, xml_key in (
            ("search_ms", "tempo_busca_ms"),
            ("rerank_ms", "tempo_rerank_ms"),
            ("graph_ms", "tempo_grafo_ms"),
        ):
            val = timings_data.get(src_key)
            if val is not None:
                ET.SubElement(meta, xml_key).text = str(int(val))

        # Stats contadores
        hits_milvus = result.stats.get("seeds_count", result.stats.get("hits_milvus"))
        if hits_milvus is not None:
            ET.SubElement(meta, "hits_milvus").text = str(hits_milvus)

        graph_nodes = result.stats.get("graph_nodes")
        if graph_nodes is not None:
            ET.SubElement(meta, "nodes_grafo").text = str(graph_nodes)

        total_chunks = result.stats.get("total_chunks")
        if total_chunks is not None:
            ET.SubElement(meta, "total_chunks").text = str(total_chunks)

        total_tokens = result.stats.get("total_tokens")
        if total_tokens is not None:
            ET.SubElement(meta, "total_tokens").text = str(total_tokens)

    ET.SubElement(meta, "reranker").text = "true"
    ET.SubElement(meta, "hyde").text = str(result.hyde_used).lower()

    has_graph = bool(result.graph_nodes)
    ET.SubElement(meta, "grafo_expandido").text = str(has_graph).lower()
    ET.SubElement(meta, "cache_hit").text = str(result.cached).lower()


def _build_instrucoes_completas_for_hybrid(
    result: HybridResult,
    root: ET.Element,
) -> None:
    """Constrói <instrucoes_completas> para HybridResult."""
    ic = ET.SubElement(root, "instrucoes_completas")

    ET.SubElement(ic, "papel").text = _PAPEL_TEXT

    aa = ET.SubElement(ic, "anti_alucinacao")
    for rule in _ANTI_ALUCINACAO_REGRAS:
        r = ET.SubElement(aa, "regra")
        r.set("prioridade", rule["prioridade"])
        r.text = rule["texto"]

    fc = ET.SubElement(ic, "formato_citacao")
    for text in _FORMATO_CITACAO_REGRAS:
        ET.SubElement(fc, "regra").text = text

    er = ET.SubElement(ic, "estrutura_resposta")
    for text in _ESTRUTURA_RESPOSTA_REGRAS:
        ET.SubElement(er, "regra").text = text

    mgd = ET.SubElement(ic, "modo_geracao_documento")
    mgd.set("condition", "quando o usuário pedir geração de documento")
    for text in _MODO_GERACAO_DOC_REGRAS:
        ET.SubElement(mgd, "regra").text = text

    # Contrato
    cr = ET.SubElement(ic, "contrato_resposta")
    ET.SubElement(cr, "formato_obrigatorio").text = _FORMATO_OBRIGATORIO_TEXT

    authorized_ids, evidence_map = _collect_authorized_ids_from_hits_with_evidence(
        result.hits, result.graph_nodes,
    )
    if authorized_ids:
        ET.SubElement(cr, "dispositivos_autorizados").text = (
            "Você SÓ pode citar os seguintes IDs. Qualquer outro é alucinação:\n"
            + ", ".join(authorized_ids)
        )

    # Mapa de evidências (URLs verificáveis por span_id)
    if evidence_map:
        lines = [f"{sid} \u2192 {url}" for sid, url in evidence_map.items()]
        ET.SubElement(cr, "mapa_evidencias").text = "\n".join(lines)

    ET.SubElement(cr, "verificacao_final").text = _VERIFICACAO_FINAL_TEXT


# Helpers compartilhados entre search e hybrid

def _build_notas_especialista_for_hits(hits: list, root: ET.Element) -> None:
    """Seção 4: <notas_especialista> — genérica para lista de hits."""
    notas = [(hit, hit.nota_especialista) for hit in hits if hit.nota_especialista]
    if not notas:
        return

    section = ET.SubElement(root, "notas_especialista")
    for hit, nota in notas:
        el = ET.SubElement(section, "nota")
        el.set("dispositivo_ref", _extract_span_id(hit.chunk_id))
        el.text = nota


def _build_jurisprudencia_for_hits(hits: list, root: ET.Element) -> None:
    """Seção 5: <jurisprudencia> — genérica para lista de hits."""
    juris = [(hit, hit.jurisprudencia_tcu) for hit in hits if hit.jurisprudencia_tcu]
    if not juris:
        return

    section = ET.SubElement(root, "jurisprudencia")
    for hit, texto in juris:
        ac = ET.SubElement(section, "acordao")
        ac.set("dispositivo_ref", _extract_span_id(hit.chunk_id))
        if hit.acordao_tcu_key:
            ac.set("chave", hit.acordao_tcu_key)
        if hit.acordao_tcu_link:
            ac.set("link", hit.acordao_tcu_link)
        ac.text = texto


def _build_trilha_verificavel_for_hits(hits: list, root: ET.Element) -> None:
    """Seção 6: <trilha_verificavel> — genérica para lista de hits."""
    hits_with_id = [h for h in hits if h.chunk_id]
    if not hits_with_id:
        return

    trilha = ET.SubElement(root, "trilha_verificavel")
    for hit in hits_with_id:
        ev = ET.SubElement(trilha, "evidencia")
        ev.set("dispositivo_ref", _extract_span_id(hit.chunk_id))
        ev.set("url", f"/api/v1/evidence/{quote(hit.chunk_id, safe='')}")
        if hit.page_number is not None:
            ev.set("pagina", str(hit.page_number))
        if hit.canonical_hash:
            ev.set("hash", hit.canonical_hash)


def _collect_authorized_ids_from_hits(
    hits: list,
    expanded: Optional[list] = None,
) -> list[str]:
    """Wrapper de compatibilidade sobre ``_collect_ids()``."""
    return _collect_ids(hits, expanded, with_evidence=False)  # type: ignore[return-value]


def _collect_authorized_ids_from_hits_with_evidence(
    hits: list,
    expanded: Optional[list] = None,
) -> tuple[list[str], dict[str, str]]:
    """Wrapper de compatibilidade sobre ``_collect_ids()``."""
    return _collect_ids(hits, expanded, with_evidence=True)  # type: ignore[return-value]


def _build_schema_dict(authorized_ids: list[str]) -> dict:
    """Constrói o dict JSON Schema wrapper a partir de IDs autorizados."""
    schema = {
        "type": "object",
        "properties": {
            "resposta_direta": {
                "type": "string",
                "description": (
                    "Resposta objetiva à pergunta em 1-3 frases, "
                    "baseada exclusivamente nos dispositivos fornecidos"
                ),
            },
            "fundamentacao": {
                "type": "array",
                "description": (
                    "Lista de afirmações jurídicas, cada uma vinculada "
                    "a um dispositivo-fonte"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "afirmacao": {
                            "type": "string",
                            "description": "Afirmação jurídica baseada no dispositivo",
                        },
                        "dispositivo_id": {
                            "type": "string",
                            "enum": authorized_ids,
                            "description": (
                                "ID do dispositivo (RESTRITO aos retornados na busca)"
                            ),
                        },
                        "citacao_formatada": {
                            "type": "string",
                            "description": (
                                "Citação legível: Lei 14.133/2021, Art. 33, Inc. III"
                            ),
                        },
                        "evidence_link": {
                            "type": ["string", "null"],
                            "description": (
                                "URL de evidência do dispositivo para hiperlink "
                                "verificável. null se não disponível"
                            ),
                        },
                    },
                    "required": ["afirmacao", "dispositivo_id", "citacao_formatada"],
                    "additionalProperties": False,
                },
            },
            "observacoes_praticas": {
                "type": ["string", "null"],
                "description": "Notas do especialista. null se não houver",
            },
            "jurisprudencia_tcu": {
                "type": ["string", "null"],
                "description": "Entendimento do TCU. null se não houver",
            },
            "dispositivos_nao_utilizados": {
                "type": "array",
                "items": {"type": "string", "enum": authorized_ids},
                "description": "IDs dos dispositivos não relevantes para a resposta",
            },
            "informacao_insuficiente": {
                "type": "boolean",
                "description": "true se os dispositivos não foram suficientes",
            },
        },
        "required": ["resposta_direta", "fundamentacao", "informacao_insuficiente"],
        "additionalProperties": False,
    }

    return {
        "name": "resposta_juridica_vectorgov",
        "strict": True,
        "schema": schema,
    }


# =============================================================================
# LOOKUP XML BUILDERS
# =============================================================================


def build_lookup_xml(result: LookupResult, level: str = "data") -> str:
    """Gera payload XML para resultado de lookup.

    Args:
        result: Resultado de lookup.
        level: Nível de instrução ("data", "instructions", "full").

    Returns:
        String XML pretty-printed.
    """
    if level not in ("data", "instructions", "full"):
        raise ValueError(f"level inválido: {level!r}. Use 'data', 'instructions' ou 'full'.")

    root = ET.Element("vectorgov_knowledge_package")
    root.set("version", "1.0")
    root.set("level", level)
    root.set("endpoint", "lookup")

    # Instruções
    if level == "instructions":
        _build_instrucoes_element(root)
    elif level == "full":
        _build_lookup_instrucoes_completas(result, root)

    # Consulta
    consulta = ET.SubElement(root, "consulta")
    ET.SubElement(consulta, "referencia_original").text = result.reference
    ET.SubElement(consulta, "status").text = result.status

    if result.resolved:
        ref_res = ET.SubElement(consulta, "referencia_resolvida")
        r = result.resolved
        if r.get("device_type"):
            ref_res.set("device_type", r["device_type"])
        if r.get("article_number"):
            ref_res.set("artigo", r["article_number"])
        if r.get("paragraph_number"):
            ref_res.set("paragrafo", r["paragraph_number"])
        if r.get("inciso_number"):
            ref_res.set("inciso", r["inciso_number"])
        if r.get("alinea_letter"):
            ref_res.set("alinea", r["alinea_letter"])
        if r.get("resolved_document_id"):
            ref_res.set("documento", r["resolved_document_id"])
        if r.get("resolved_span_id"):
            ref_res.set("span_id", r["resolved_span_id"])

    # Hierarquia normativa (só se found)
    if result.status == "found" and result.match:
        hier = ET.SubElement(root, "hierarquia_normativa")

        # Artigo pai
        if result.parent:
            pai = ET.SubElement(hier, "artigo_pai")
            pai.set("id", result.parent.span_id)
            pai.set("device_type", result.parent.device_type)
            pai.text = result.parent.text or ""

        # Dispositivo principal
        disp = ET.SubElement(hier, "dispositivo_principal")
        disp.set("id", result.match.span_id)
        disp.set("tipo", result.match.device_type)
        if result.match.article_number:
            disp.set("artigo", result.match.article_number)
        disp.text = result.match.text or ""

        # Irmãos
        if result.siblings:
            irmaos = ET.SubElement(hier, "dispositivos_irmaos")
            for sib in result.siblings:
                el = ET.SubElement(irmaos, "irmao")
                el.set("id", sib.span_id)
                el.set("tipo", sib.device_type)
                el.set("atual", str(sib.is_current).lower())
                el.text = sib.text or ""

    # Candidatos (ambiguous)
    if result.status == "ambiguous" and result.candidates:
        cands = ET.SubElement(root, "candidatos")
        for cand in result.candidates:
            el = ET.SubElement(cands, "candidato")
            el.set("document_id", cand.document_id)
            el.set("node_id", cand.node_id)
            if cand.tipo_documento:
                el.set("tipo_documento", cand.tipo_documento)
            el.text = cand.text or ""

    # Metadados
    meta = ET.SubElement(root, "metadados")
    ET.SubElement(meta, "pipeline").text = "fenix"
    ET.SubElement(meta, "tempo_total_ms").text = str(int(result.elapsed_ms))

    return _element_to_string(root)


def _build_lookup_instrucoes_completas(result: LookupResult, root: ET.Element) -> None:
    """Constrói instrucoes_completas para lookup."""
    ic = ET.SubElement(root, "instrucoes_completas")
    ET.SubElement(ic, "papel").text = _PAPEL_TEXT

    aa = ET.SubElement(ic, "anti_alucinacao")
    for rule in _ANTI_ALUCINACAO_REGRAS:
        r = ET.SubElement(aa, "regra")
        r.set("prioridade", rule["prioridade"])
        r.text = rule["texto"]

    # Contrato simplificado para lookup
    if result.match:
        cr = ET.SubElement(ic, "contrato_resposta")
        ids = [result.match.span_id]
        if result.parent:
            ids.append(result.parent.span_id)
        for sib in result.siblings:
            if sib.span_id not in ids:
                ids.append(sib.span_id)
        ET.SubElement(cr, "dispositivos_autorizados").text = (
            "Você SÓ pode citar os seguintes IDs:\n" + ", ".join(ids)
        )
    ET.SubElement(ic, "verificacao_final").text = _VERIFICACAO_FINAL_TEXT


def build_lookup_prompt_xml(
    result: LookupResult,
    query: Optional[str] = None,
    level: str = "instructions",
) -> str:
    """Gera prompt único com XML + query para lookup."""
    query = query or result.reference
    xml = build_lookup_xml(result, level=level)
    return f"{xml}\n\nPergunta: {query}\n\nResposta:"


def build_lookup_messages_xml(
    result: LookupResult,
    query: Optional[str] = None,
    level: str = "instructions",
) -> list[dict[str, str]]:
    """Gera lista de mensagens com XML no system e query no user para lookup."""
    query = query or result.reference
    xml = build_lookup_xml(result, level=level)
    return [
        {"role": "system", "content": xml},
        {"role": "user", "content": query},
    ]


def build_lookup_markdown(result: LookupResult) -> str:
    """Gera Markdown legível a partir de um LookupResult."""
    parts: list[str] = []

    parts.append(f"# Lookup: {result.reference}\n")
    parts.append(f"**Status:** {result.status} | **Tempo:** {result.elapsed_ms:.0f}ms\n")

    if result.message:
        parts.append(f"_{result.message}_\n")

    if result.resolved:
        r = result.resolved
        comp = []
        if r.get("device_type"):
            comp.append(f"Tipo: {r['device_type']}")
        if r.get("article_number"):
            comp.append(f"Art. {r['article_number']}")
        if r.get("inciso_number"):
            comp.append(f"Inc. {r['inciso_number']}")
        if r.get("resolved_document_id"):
            comp.append(f"Doc: {r['resolved_document_id']}")
        if comp:
            parts.append(f"**Resolvido:** {', '.join(comp)}\n")

    if result.status == "found" and result.match:
        parts.append("## Dispositivo Principal\n")
        parts.append(f"**{result.match.span_id}** ({result.match.device_type})\n")
        parts.append(f"{result.match.text}\n")

        if result.parent:
            parts.append("## Artigo Pai\n")
            parts.append(f"**{result.parent.span_id}** ({result.parent.device_type})\n")
            parts.append(f"{result.parent.text}\n")

        if result.siblings:
            parts.append("## Dispositivos Irmãos\n")
            for sib in result.siblings:
                marker = "**>**" if sib.is_current else "  "
                parts.append(f"{marker} **{sib.span_id}** — {sib.text[:80]}...\n")

    if result.status == "ambiguous" and result.candidates:
        parts.append("## Candidatos\n")
        for cand in result.candidates:
            parts.append(f"- **{cand.document_id}** ({cand.node_id}): {cand.text[:80]}...\n")

    return "\n".join(parts)


def _element_to_string(root: ET.Element) -> str:
    """Serializa ElementTree para string XML pretty-printed."""
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=False)


# =============================================================================
# ENTRY POINT UNIFICADO — serialize_to_xml (Seção 7)
# =============================================================================


def serialize_to_xml(
    result,
    level: str = "data",
) -> str:
    """Entry point unificado para serialização XML.

    Detecta automaticamente o tipo de resultado (SearchResult, HybridResult,
    LookupResult) e despacha para o builder correto.

    Args:
        result: Resultado de busca (SearchResult, HybridResult ou LookupResult).
        level: Nível de instrução ("data", "instructions", "full").

    Returns:
        String XML pretty-printed.

    Raises:
        TypeError: Se o tipo de resultado não for reconhecido.

    Example:
        >>> xml = serialize_to_xml(result, level="full")
    """
    # Import local para evitar circular
    from vectorgov.models import SearchResult, HybridResult, LookupResult

    if isinstance(result, HybridResult):
        return build_hybrid_xml(result, level=level)
    elif isinstance(result, LookupResult):
        return build_lookup_xml(result, level=level)
    elif isinstance(result, SearchResult):
        return build_xml(result, level=level)
    else:
        raise TypeError(
            f"Tipo não suportado: {type(result).__name__}. "
            "Use SearchResult, HybridResult ou LookupResult."
        )


# =============================================================================
# ALIASES PÚBLICOS — generate_* (Seção 7)
# =============================================================================


def generate_response_schema(
    result,
    include_jurisprudencia: bool = False,
    include_observacoes: bool = False,
) -> Optional[dict]:
    """Gera JSON Schema para structured output (alias público).

    Detecta tipo do resultado e gera schema com enum restrito aos IDs
    efetivamente presentes, prevenindo alucinação via constrained decoding.

    Args:
        result: SearchResult, HybridResult ou LookupResult.
        include_jurisprudencia: Mantido para compatibilidade (no-op).
        include_observacoes: Mantido para compatibilidade (no-op).

    Returns:
        Dict wrapper ``{name, strict, schema}``, ou None se não houver hits.
    """
    from vectorgov.models import HybridResult, LookupResult

    if isinstance(result, HybridResult):
        return result.to_response_schema()
    if isinstance(result, LookupResult):
        return result.to_response_schema()
    return build_response_schema(
        result,
        include_jurisprudencia=include_jurisprudencia,
        include_observacoes=include_observacoes,
    )


def generate_anthropic_tool_schema(result) -> Optional[dict]:
    """Gera schema no formato Anthropic tool_use (alias público).

    Args:
        result: SearchResult, HybridResult ou LookupResult.

    Returns:
        Dict no formato Anthropic tool, ou None se não houver hits.
    """
    from vectorgov.models import HybridResult, LookupResult

    if isinstance(result, HybridResult):
        return result.to_anthropic_tool_schema()
    if isinstance(result, LookupResult):
        return result.to_anthropic_tool_schema()
    return build_anthropic_tool_schema(result)
