"""
Exceções customizadas do VectorGov SDK.
"""

from typing import Optional


class VectorGovError(Exception):
    """Exceção base para todos os erros do VectorGov SDK."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthError(VectorGovError):
    """Erro de autenticação (API key inválida ou expirada)."""

    def __init__(self, message: str = "API key inválida ou expirada"):
        super().__init__(message, status_code=401)


class RateLimitError(VectorGovError):
    """Rate limit excedido."""

    def __init__(
        self,
        message: str = "Rate limit excedido",
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base}. Tente novamente em {self.retry_after} segundos."
        return base


class ValidationError(VectorGovError):
    """Erro de validação de parâmetros."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, status_code=400)
        self.field = field


class ServerError(VectorGovError):
    """Erro interno do servidor."""

    def __init__(self, message: str = "Erro interno do servidor"):
        super().__init__(message, status_code=500)


class ConnectionError(VectorGovError):
    """Erro de conexão com o servidor."""

    def __init__(self, message: str = "Não foi possível conectar ao servidor"):
        super().__init__(message)


class TimeoutError(VectorGovError):
    """Timeout na requisição."""

    def __init__(self, message: str = "A requisição excedeu o tempo limite"):
        super().__init__(message)
