"""
Integração do VectorGov com HuggingFace Transformers.

Este módulo fornece helpers para usar o VectorGov com modelos locais
do HuggingFace, permitindo RAG com LLMs gratuitos e open-source.

Exemplo básico:
    >>> from vectorgov import VectorGov
    >>> from vectorgov.integrations.transformers import create_rag_pipeline
    >>> from transformers import pipeline
    >>>
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> llm = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
    >>>
    >>> rag = create_rag_pipeline(vg, llm)
    >>> response = rag("O que é ETP?")

Modelos recomendados (português/multilíngue):
    - meta-llama/Llama-3.2-3B-Instruct (leve, bom em português)
    - meta-llama/Llama-3.1-8B-Instruct (melhor qualidade)
    - Qwen/Qwen2.5-7B-Instruct (excelente em português)
    - microsoft/Phi-3-mini-4k-instruct (muito leve)
    - google/gemma-2-9b-it (bom equilíbrio)
"""

from typing import Any, Callable, Dict, List, Optional, Union


def format_prompt_for_transformers(
    query: str,
    context: str,
    system_prompt: Optional[str] = None,
    chat_template: str = "llama",
) -> Union[str, List[Dict[str, str]]]:
    """
    Formata prompt para modelos Transformers.

    Args:
        query: Pergunta do usuário.
        context: Contexto recuperado do VectorGov.
        system_prompt: Prompt de sistema customizado.
        chat_template: Formato do chat ("llama", "chatml", "raw").

    Returns:
        Prompt formatado (string ou lista de mensagens).

    Example:
        >>> from vectorgov import VectorGov
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> results = vg.search("O que é ETP?")
        >>> prompt = format_prompt_for_transformers(
        ...     query="O que é ETP?",
        ...     context=results.to_context(),
        ... )
    """
    if system_prompt is None:
        system_prompt = """Você é um assistente jurídico especializado em legislação brasileira.
Responda com base APENAS no contexto fornecido.
Cite os artigos e fontes relevantes.
Se a informação não estiver no contexto, diga que não encontrou."""

    user_content = f"""Contexto da legislação:
{context}

Pergunta: {query}

Resposta:"""

    if chat_template == "raw":
        return f"{system_prompt}\n\n{user_content}"

    elif chat_template == "chatml":
        return f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_content}<|im_end|>
<|im_start|>assistant
"""

    elif chat_template == "llama":
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    else:
        # Default: retorna lista de mensagens (funciona com a maioria)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]


def create_rag_pipeline(
    vectorgov_client: Any,
    text_generation_pipeline: Any,
    top_k: int = 5,
    mode: str = "balanced",
    max_new_tokens: int = 512,
    temperature: float = 0.1,
    system_prompt: Optional[str] = None,
) -> Callable[[str], str]:
    """
    Cria um pipeline RAG completo com VectorGov + Transformers.

    Args:
        vectorgov_client: Instância do cliente VectorGov.
        text_generation_pipeline: Pipeline do Transformers (text-generation).
        top_k: Número de chunks a recuperar.
        mode: Modo de busca ("fast", "balanced", "precise").
        max_new_tokens: Máximo de tokens na resposta.
        temperature: Temperatura para geração.
        system_prompt: Prompt de sistema customizado.

    Returns:
        Função que recebe uma query e retorna a resposta.

    Example:
        >>> from vectorgov import VectorGov
        >>> from transformers import pipeline
        >>>
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> llm = pipeline("text-generation", model="Qwen/Qwen2.5-3B-Instruct")
        >>>
        >>> rag = create_rag_pipeline(vg, llm)
        >>> response = rag("Quando o ETP pode ser dispensado?")
        >>> print(response)
    """

    def rag_query(query: str) -> str:
        # 1. Busca no VectorGov
        results = vectorgov_client.search(query, top_k=top_k, mode=mode)
        context = results.to_context()

        # 2. Formata prompt
        messages = format_prompt_for_transformers(
            query=query,
            context=context,
            system_prompt=system_prompt,
            chat_template="llama",
        )

        # 3. Gera resposta
        output = text_generation_pipeline(
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=text_generation_pipeline.tokenizer.eos_token_id,
        )

        # 4. Extrai texto gerado
        if isinstance(output, list) and len(output) > 0:
            generated = output[0]
            if "generated_text" in generated:
                # Para pipelines que retornam lista de mensagens
                gen_text = generated["generated_text"]
                if isinstance(gen_text, list):
                    # Pega última mensagem (assistant)
                    for msg in reversed(gen_text):
                        if msg.get("role") == "assistant":
                            return msg.get("content", "").strip()
                    # Fallback: última mensagem
                    return gen_text[-1].get("content", "").strip() if gen_text else ""
                return gen_text.strip()

        return str(output)

    return rag_query


class VectorGovRAG:
    """
    Classe wrapper para RAG com VectorGov + Transformers.

    Fornece interface orientada a objetos e recursos adicionais
    como histórico de conversas e streaming.

    Example:
        >>> from vectorgov import VectorGov
        >>> from vectorgov.integrations.transformers import VectorGovRAG
        >>> from transformers import pipeline
        >>>
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> llm = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
        >>>
        >>> rag = VectorGovRAG(vg, llm)
        >>> response = rag.ask("O que é ETP?")
        >>> print(response.answer)
        >>> print(response.sources)
    """

    def __init__(
        self,
        vectorgov_client: Any,
        text_generation_pipeline: Any,
        top_k: int = 5,
        mode: str = "balanced",
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ):
        """
        Inicializa o RAG.

        Args:
            vectorgov_client: Instância do cliente VectorGov.
            text_generation_pipeline: Pipeline do Transformers.
            top_k: Número de chunks a recuperar.
            mode: Modo de busca.
            max_new_tokens: Máximo de tokens na resposta.
            temperature: Temperatura para geração.
            system_prompt: Prompt de sistema customizado.
        """
        self.vg = vectorgov_client
        self.llm = text_generation_pipeline
        self.top_k = top_k
        self.mode = mode
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt or self._default_system_prompt()
        self._history: List[Dict[str, str]] = []

    def _default_system_prompt(self) -> str:
        return """Você é um assistente jurídico especializado em legislação brasileira.
Responda com base APENAS no contexto fornecido.
Cite os artigos e fontes relevantes.
Se a informação não estiver no contexto, diga que não encontrou."""

    def ask(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
        include_sources: bool = True,
    ) -> "RAGResponse":
        """
        Faz uma pergunta ao sistema RAG.

        Args:
            query: Pergunta do usuário.
            top_k: Override do top_k padrão.
            mode: Override do modo padrão.
            include_sources: Se deve incluir fontes na resposta.

        Returns:
            RAGResponse com answer, sources, e metadados.
        """
        # Busca no VectorGov
        results = self.vg.search(
            query,
            top_k=top_k or self.top_k,
            mode=mode or self.mode,
        )

        context = results.to_context()
        sources = [hit.source for hit in results]

        # Formata prompt
        messages = format_prompt_for_transformers(
            query=query,
            context=context,
            system_prompt=self.system_prompt,
        )

        # Gera resposta
        output = self.llm(
            messages,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=self.temperature > 0,
            pad_token_id=self.llm.tokenizer.eos_token_id,
        )

        # Extrai texto
        answer = self._extract_answer(output)

        # Salva no histórico
        self._history.append({"query": query, "answer": answer})

        return RAGResponse(
            answer=answer,
            sources=sources if include_sources else [],
            query=query,
            context=context,
            latency_ms=results.latency_ms,
            cached=results.cached,
        )

    def _extract_answer(self, output: Any) -> str:
        """Extrai texto da resposta do modelo."""
        if isinstance(output, list) and len(output) > 0:
            generated = output[0]
            if "generated_text" in generated:
                gen_text = generated["generated_text"]
                if isinstance(gen_text, list):
                    for msg in reversed(gen_text):
                        if msg.get("role") == "assistant":
                            return msg.get("content", "").strip()
                    return gen_text[-1].get("content", "").strip() if gen_text else ""
                return gen_text.strip()
        return str(output)

    def clear_history(self) -> None:
        """Limpa histórico de conversas."""
        self._history = []

    @property
    def history(self) -> List[Dict[str, str]]:
        """Retorna histórico de conversas."""
        return self._history.copy()


class RAGResponse:
    """Resposta do sistema RAG."""

    def __init__(
        self,
        answer: str,
        sources: List[str],
        query: str,
        context: str,
        latency_ms: int = 0,
        cached: bool = False,
    ):
        self.answer = answer
        self.sources = sources
        self.query = query
        self.context = context
        self.latency_ms = latency_ms
        self.cached = cached

    def __str__(self) -> str:
        return self.answer

    def __repr__(self) -> str:
        return f"RAGResponse(answer='{self.answer[:50]}...', sources={len(self.sources)})"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "answer": self.answer,
            "sources": self.sources,
            "query": self.query,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
        }


def get_recommended_models() -> Dict[str, Dict[str, Any]]:
    """
    Retorna lista de modelos recomendados para uso com VectorGov.

    Returns:
        Dicionário com informações dos modelos.

    Example:
        >>> from vectorgov.integrations.transformers import get_recommended_models
        >>> models = get_recommended_models()
        >>> for name, info in models.items():
        ...     print(f"{name}: {info['description']}")
    """
    return {
        "meta-llama/Llama-3.2-1B-Instruct": {
            "description": "Modelo ultra-leve, roda em CPU",
            "vram_gb": 2,
            "quality": "básica",
            "speed": "muito rápido",
            "portuguese": "bom",
        },
        "meta-llama/Llama-3.2-3B-Instruct": {
            "description": "Bom equilíbrio leveza/qualidade",
            "vram_gb": 6,
            "quality": "boa",
            "speed": "rápido",
            "portuguese": "bom",
        },
        "meta-llama/Llama-3.1-8B-Instruct": {
            "description": "Alta qualidade, requer GPU",
            "vram_gb": 16,
            "quality": "muito boa",
            "speed": "médio",
            "portuguese": "muito bom",
        },
        "Qwen/Qwen2.5-3B-Instruct": {
            "description": "Excelente em português, leve",
            "vram_gb": 6,
            "quality": "boa",
            "speed": "rápido",
            "portuguese": "excelente",
        },
        "Qwen/Qwen2.5-7B-Instruct": {
            "description": "Melhor opção para português",
            "vram_gb": 14,
            "quality": "muito boa",
            "speed": "médio",
            "portuguese": "excelente",
        },
        "microsoft/Phi-3-mini-4k-instruct": {
            "description": "Muito leve, bom para CPU",
            "vram_gb": 4,
            "quality": "boa",
            "speed": "muito rápido",
            "portuguese": "razoável",
        },
        "google/gemma-2-2b-it": {
            "description": "Modelo Google, leve",
            "vram_gb": 4,
            "quality": "boa",
            "speed": "rápido",
            "portuguese": "bom",
        },
        "mistralai/Mistral-7B-Instruct-v0.3": {
            "description": "Modelo europeu, bom geral",
            "vram_gb": 14,
            "quality": "muito boa",
            "speed": "médio",
            "portuguese": "bom",
        },
    }


def estimate_vram_usage(model_name: str) -> Optional[int]:
    """
    Estima uso de VRAM para um modelo.

    Args:
        model_name: Nome do modelo no HuggingFace.

    Returns:
        Estimativa de VRAM em GB, ou None se desconhecido.
    """
    models = get_recommended_models()
    if model_name in models:
        return models[model_name]["vram_gb"]

    # Estimativa baseada no nome
    name_lower = model_name.lower()
    if "1b" in name_lower:
        return 2
    elif "3b" in name_lower:
        return 6
    elif "7b" in name_lower or "8b" in name_lower:
        return 16
    elif "13b" in name_lower or "14b" in name_lower:
        return 28
    elif "70b" in name_lower:
        return 140

    return None


# Exports públicos
__all__ = [
    "format_prompt_for_transformers",
    "create_rag_pipeline",
    "VectorGovRAG",
    "RAGResponse",
    "get_recommended_models",
    "estimate_vram_usage",
]
