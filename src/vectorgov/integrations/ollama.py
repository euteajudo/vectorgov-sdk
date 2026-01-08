"""
Integração do VectorGov com Ollama.

Este módulo fornece helpers para usar o VectorGov com modelos locais
rodando no Ollama, permitindo RAG completamente local e gratuito.

Exemplo básico:
    >>> from vectorgov import VectorGov
    >>> from vectorgov.integrations.ollama import create_rag_pipeline
    >>>
    >>> vg = VectorGov(api_key="vg_xxx")
    >>> rag = create_rag_pipeline(vg, model="qwen2.5:7b")
    >>> response = rag("O que é ETP?")

Com classe VectorGovOllama:
    >>> from vectorgov.integrations.ollama import VectorGovOllama
    >>> ollama_rag = VectorGovOllama(vg, model="qwen2.5:7b")
    >>> result = ollama_rag.ask("Quando o ETP pode ser dispensado?")
    >>> print(result.answer)
    >>> print(result.sources)

Modelos recomendados:
    - qwen2.5:3b (leve, bom em português)
    - qwen2.5:7b (melhor qualidade)
    - qwen3:8b (excelente, mais recente)
    - llama3.2:3b (leve, multilíngue)
    - mistral:7b (bom equilíbrio)
"""

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


# URL padrão do Ollama
DEFAULT_OLLAMA_URL = "http://localhost:11434"


@dataclass
class OllamaResponse:
    """Resposta estruturada do RAG com Ollama."""

    answer: str
    """Resposta gerada pelo modelo."""

    sources: List[str]
    """Lista de fontes citadas."""

    latency_ms: int
    """Latência total em milissegundos."""

    model: str
    """Modelo usado para geração."""

    cached: bool = False
    """Se a busca veio do cache."""

    tokens_used: Optional[int] = None
    """Tokens usados na geração (se disponível)."""


def check_ollama_available(base_url: str = DEFAULT_OLLAMA_URL) -> bool:
    """
    Verifica se o Ollama está disponível.

    Args:
        base_url: URL base do Ollama.

    Returns:
        True se disponível, False caso contrário.
    """
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def list_models(base_url: str = DEFAULT_OLLAMA_URL) -> List[str]:
    """
    Lista modelos disponíveis no Ollama.

    Args:
        base_url: URL base do Ollama.

    Returns:
        Lista de nomes de modelos.

    Example:
        >>> from vectorgov.integrations.ollama import list_models
        >>> models = list_models()
        >>> print(models)
        ['qwen2.5:7b', 'llama3.2:3b', ...]
    """
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def generate(
    prompt: str,
    model: str = "qwen2.5:7b",
    base_url: str = DEFAULT_OLLAMA_URL,
    system: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 512,
    stream: bool = False,
) -> str:
    """
    Gera texto usando o Ollama.

    Args:
        prompt: Prompt para o modelo.
        model: Nome do modelo no Ollama.
        base_url: URL base do Ollama.
        system: Prompt de sistema.
        temperature: Temperatura para geração.
        max_tokens: Máximo de tokens na resposta.
        stream: Se deve fazer streaming (não implementado).

    Returns:
        Texto gerado pelo modelo.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")


def create_rag_pipeline(
    vectorgov_client: Any,
    model: str = "qwen2.5:7b",
    base_url: str = DEFAULT_OLLAMA_URL,
    top_k: int = 5,
    mode: str = "balanced",
    temperature: float = 0.1,
    max_tokens: int = 512,
    system_prompt: Optional[str] = None,
) -> Callable[[str], str]:
    """
    Cria um pipeline RAG simples com VectorGov + Ollama.

    Args:
        vectorgov_client: Instância do VectorGov.
        model: Nome do modelo no Ollama.
        base_url: URL base do Ollama.
        top_k: Número de resultados a recuperar.
        mode: Modo de busca ('fast', 'balanced', 'precise').
        temperature: Temperatura para geração.
        max_tokens: Máximo de tokens na resposta.
        system_prompt: Prompt de sistema customizado.

    Returns:
        Função que recebe uma query e retorna a resposta.

    Example:
        >>> from vectorgov import VectorGov
        >>> from vectorgov.integrations.ollama import create_rag_pipeline
        >>>
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> rag = create_rag_pipeline(vg, model="qwen3:8b")
        >>> response = rag("O que é ETP?")
        >>> print(response)
    """
    if system_prompt is None:
        system_prompt = """Você é um assistente jurídico especializado em legislação brasileira.
Responda com base APENAS no contexto fornecido.
Cite os artigos e fontes relevantes.
Se a informação não estiver no contexto, diga que não encontrou."""

    def pipeline(query: str) -> str:
        # 1. Busca no VectorGov
        results = vectorgov_client.search(query, top_k=top_k, mode=mode)

        if results.total == 0:
            return "Não encontrei informações relevantes na base de conhecimento."

        # 2. Monta contexto
        context = results.to_context()

        # 3. Monta prompt
        user_prompt = f"""Contexto da legislação:
{context}

Pergunta: {query}

Resposta:"""

        # 4. Gera resposta
        response = generate(
            prompt=user_prompt,
            model=model,
            base_url=base_url,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response

    return pipeline


class VectorGovOllama:
    """
    Classe completa para RAG com VectorGov + Ollama.

    Oferece mais controle que create_rag_pipeline, incluindo:
    - Respostas estruturadas com fontes
    - Métricas de latência
    - Histórico de conversas (opcional)

    Example:
        >>> from vectorgov import VectorGov
        >>> from vectorgov.integrations.ollama import VectorGovOllama
        >>>
        >>> vg = VectorGov(api_key="vg_xxx")
        >>> rag = VectorGovOllama(vg, model="qwen3:8b")
        >>>
        >>> result = rag.ask("O que é ETP?")
        >>> print(result.answer)
        >>> print(result.sources)
        >>> print(f"Latência: {result.latency_ms}ms")
    """

    def __init__(
        self,
        vectorgov_client: Any,
        model: str = "qwen2.5:7b",
        base_url: str = DEFAULT_OLLAMA_URL,
        top_k: int = 5,
        mode: str = "balanced",
        temperature: float = 0.1,
        max_tokens: int = 512,
        system_prompt: Optional[str] = None,
    ):
        """
        Inicializa o RAG com Ollama.

        Args:
            vectorgov_client: Instância do VectorGov.
            model: Nome do modelo no Ollama.
            base_url: URL base do Ollama.
            top_k: Número de resultados padrão.
            mode: Modo de busca padrão.
            temperature: Temperatura para geração.
            max_tokens: Máximo de tokens na resposta.
            system_prompt: Prompt de sistema customizado.
        """
        self.vg = vectorgov_client
        self.model = model
        self.base_url = base_url
        self.top_k = top_k
        self.mode = mode
        self.temperature = temperature
        self.max_tokens = max_tokens

        if system_prompt is None:
            self.system_prompt = """Você é um assistente jurídico especializado em legislação brasileira.
Responda com base APENAS no contexto fornecido.
Cite os artigos e fontes relevantes.
Se a informação não estiver no contexto, diga que não encontrou."""
        else:
            self.system_prompt = system_prompt

        # Verifica se Ollama está disponível
        if not check_ollama_available(base_url):
            raise ConnectionError(
                f"Ollama não está disponível em {base_url}. "
                "Certifique-se de que o Ollama está rodando."
            )

        # Verifica se o modelo está disponível
        available_models = list_models(base_url)
        if model not in available_models:
            raise ValueError(
                f"Modelo '{model}' não encontrado no Ollama. "
                f"Modelos disponíveis: {available_models}. "
                f"Use 'ollama pull {model}' para baixar."
            )

    def ask(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> OllamaResponse:
        """
        Faz uma pergunta ao sistema RAG.

        Args:
            query: Pergunta do usuário.
            top_k: Override do top_k padrão.
            mode: Override do modo padrão.

        Returns:
            OllamaResponse com resposta, fontes e métricas.
        """
        start_time = time.time()

        # Usa valores padrão se não especificado
        top_k = top_k or self.top_k
        mode = mode or self.mode

        # 1. Busca no VectorGov
        results = self.vg.search(query, top_k=top_k, mode=mode)

        if results.total == 0:
            return OllamaResponse(
                answer="Não encontrei informações relevantes na base de conhecimento.",
                sources=[],
                latency_ms=int((time.time() - start_time) * 1000),
                model=self.model,
                cached=results.cached,
            )

        # 2. Extrai fontes
        sources = [hit.source for hit in results.hits]

        # 3. Monta contexto
        context = results.to_context()

        # 4. Monta prompt
        user_prompt = f"""Contexto da legislação:
{context}

Pergunta: {query}

Resposta:"""

        # 5. Gera resposta
        answer = generate(
            prompt=user_prompt,
            model=self.model,
            base_url=self.base_url,
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return OllamaResponse(
            answer=answer,
            sources=sources,
            latency_ms=latency_ms,
            model=self.model,
            cached=results.cached,
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        use_rag: bool = True,
    ) -> str:
        """
        Chat com histórico de mensagens.

        Args:
            messages: Lista de mensagens [{"role": "user/assistant", "content": "..."}]
            use_rag: Se deve usar RAG para a última mensagem.

        Returns:
            Resposta do modelo.
        """
        if not messages:
            return ""

        last_message = messages[-1]["content"]

        if use_rag:
            # Busca contexto para a última mensagem
            results = self.vg.search(last_message, top_k=self.top_k, mode=self.mode)
            context = results.to_context() if results.total > 0 else ""

            if context:
                # Adiciona contexto ao system prompt
                enhanced_system = f"""{self.system_prompt}

Contexto relevante da legislação:
{context}"""
            else:
                enhanced_system = self.system_prompt
        else:
            enhanced_system = self.system_prompt

        # Monta payload para Ollama
        ollama_messages = [{"role": "system", "content": enhanced_system}]
        ollama_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")


def get_recommended_models() -> Dict[str, Dict[str, Any]]:
    """
    Retorna modelos recomendados para uso com VectorGov no Ollama.

    Returns:
        Dicionário com informações dos modelos.

    Example:
        >>> from vectorgov.integrations.ollama import get_recommended_models
        >>> models = get_recommended_models()
        >>> for name, info in models.items():
        ...     print(f"{name}: {info['description']}")
    """
    return {
        "qwen2.5:0.5b": {
            "description": "Ultra-leve, roda em qualquer máquina",
            "ram_gb": 1,
            "quality": "básica",
            "speed": "muito rápido",
            "portuguese": "bom",
            "command": "ollama pull qwen2.5:0.5b",
        },
        "qwen2.5:3b": {
            "description": "Leve e eficiente, bom para português",
            "ram_gb": 4,
            "quality": "boa",
            "speed": "rápido",
            "portuguese": "muito bom",
            "command": "ollama pull qwen2.5:3b",
        },
        "qwen2.5:7b": {
            "description": "Excelente qualidade em português",
            "ram_gb": 8,
            "quality": "muito boa",
            "speed": "médio",
            "portuguese": "excelente",
            "command": "ollama pull qwen2.5:7b",
        },
        "qwen3:8b": {
            "description": "Mais recente, melhor raciocínio",
            "ram_gb": 8,
            "quality": "excelente",
            "speed": "médio",
            "portuguese": "excelente",
            "command": "ollama pull qwen3:8b",
        },
        "llama3.2:3b": {
            "description": "Meta Llama, leve e multilíngue",
            "ram_gb": 4,
            "quality": "boa",
            "speed": "rápido",
            "portuguese": "bom",
            "command": "ollama pull llama3.2:3b",
        },
        "mistral:7b": {
            "description": "Bom equilíbrio geral",
            "ram_gb": 8,
            "quality": "boa",
            "speed": "médio",
            "portuguese": "bom",
            "command": "ollama pull mistral:7b",
        },
        "gemma2:9b": {
            "description": "Google Gemma, boa qualidade",
            "ram_gb": 10,
            "quality": "muito boa",
            "speed": "médio",
            "portuguese": "bom",
            "command": "ollama pull gemma2:9b",
        },
    }
