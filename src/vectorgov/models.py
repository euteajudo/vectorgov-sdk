"""
Modelos de dados do VectorGov SDK.
"""

from dataclasses import dataclass, field
from typing import Optional, Iterator, Any
from datetime import datetime


@dataclass
class Metadata:
    """Metadados de um documento encontrado."""

    document_type: str
    """Tipo do documento (lei, decreto, in, etc.)"""

    document_number: str
    """Número do documento"""

    year: int
    """Ano do documento"""

    article: Optional[str] = None
    """Número do artigo"""

    paragraph: Optional[str] = None
    """Número do parágrafo"""

    item: Optional[str] = None
    """Número do inciso"""

    orgao: Optional[str] = None
    """Órgão emissor"""

    extra: dict = field(default_factory=dict)
    """Metadados adicionais"""

    def __repr__(self) -> str:
        parts = [f"{self.document_type.upper()} {self.document_number}/{self.year}"]
        if self.article:
            parts.append(f"Art. {self.article}")
        if self.paragraph:
            parts.append(f"§{self.paragraph}")
        if self.item:
            parts.append(f"inciso {self.item}")
        return ", ".join(parts)


@dataclass
class Hit:
    """Um resultado individual da busca."""

    text: str
    """Texto do chunk encontrado"""

    score: float
    """Score de relevância (0-1)"""

    source: str
    """Fonte formatada (ex: 'Lei 14.133/2021, Art. 33')"""

    metadata: Metadata
    """Metadados completos do documento"""

    chunk_id: Optional[str] = None
    """ID interno do chunk (para debugging)"""

    context: Optional[str] = None
    """Contexto adicional do chunk"""

    def __repr__(self) -> str:
        text_preview = self.text[:100] + "..." if len(self.text) > 100 else self.text
        return f"Hit(score={self.score:.3f}, source='{self.source}', text='{text_preview}')"


@dataclass
class SearchResult:
    """Resultado completo de uma busca."""

    query: str
    """Query original"""

    hits: list[Hit]
    """Lista de resultados encontrados"""

    total: int
    """Quantidade total de resultados"""

    latency_ms: int
    """Tempo de resposta em milissegundos"""

    cached: bool
    """Se o resultado veio do cache"""

    query_id: str
    """ID único da query (para feedback)"""

    mode: str
    """Modo de busca utilizado"""

    timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp da busca"""

    def __len__(self) -> int:
        return len(self.hits)

    def __iter__(self) -> Iterator[Hit]:
        return iter(self.hits)

    def __getitem__(self, index: int) -> Hit:
        return self.hits[index]

    def __repr__(self) -> str:
        return (
            f"SearchResult(query='{self.query[:50]}...', "
            f"total={self.total}, latency={self.latency_ms}ms, cached={self.cached})"
        )

    def to_context(self, max_chars: Optional[int] = None) -> str:
        """Converte os resultados em uma string de contexto.

        Args:
            max_chars: Limite máximo de caracteres (None = sem limite)

        Returns:
            String formatada com os resultados numerados
        """
        parts = []
        total_chars = 0

        for i, hit in enumerate(self.hits, 1):
            entry = f"[{i}] {hit.source}\n{hit.text}\n"

            if max_chars and total_chars + len(entry) > max_chars:
                break

            parts.append(entry)
            total_chars += len(entry)

        return "\n".join(parts)

    def to_messages(
        self,
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_context_chars: Optional[int] = None,
    ) -> list[dict[str, str]]:
        """Converte os resultados em formato de mensagens para chat completions.

        Args:
            query: Pergunta a ser feita (usa self.query se não informado)
            system_prompt: Prompt de sistema customizado
            max_context_chars: Limite de caracteres do contexto

        Returns:
            Lista de mensagens no formato OpenAI/Anthropic
        """
        from vectorgov.config import SYSTEM_PROMPTS

        query = query or self.query
        system = system_prompt or SYSTEM_PROMPTS["default"]
        context = self.to_context(max_chars=max_context_chars)

        return [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Contexto:\n{context}\n\nPergunta: {query}",
            },
        ]

    def to_prompt(
        self,
        query: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_context_chars: Optional[int] = None,
    ) -> str:
        """Converte os resultados em um prompt único (para Gemini e similares).

        Args:
            query: Pergunta a ser feita (usa self.query se não informado)
            system_prompt: Prompt de sistema customizado
            max_context_chars: Limite de caracteres do contexto

        Returns:
            String com o prompt completo
        """
        from vectorgov.config import SYSTEM_PROMPTS

        query = query or self.query
        system = system_prompt or SYSTEM_PROMPTS["default"]
        context = self.to_context(max_chars=max_context_chars)

        return f"""{system}

Contexto:
{context}

Pergunta: {query}

Resposta:"""

    def to_dict(self) -> dict[str, Any]:
        """Converte o resultado para dicionário."""
        return {
            "query": self.query,
            "hits": [
                {
                    "text": hit.text,
                    "score": hit.score,
                    "source": hit.source,
                    "metadata": {
                        "document_type": hit.metadata.document_type,
                        "document_number": hit.metadata.document_number,
                        "year": hit.metadata.year,
                        "article": hit.metadata.article,
                        "paragraph": hit.metadata.paragraph,
                        "item": hit.metadata.item,
                    },
                }
                for hit in self.hits
            ],
            "total": self.total,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
            "query_id": self.query_id,
            "mode": self.mode,
        }
