"""
Cliente HTTP interno do VectorGov SDK.
"""

import time
from typing import Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

from vectorgov.exceptions import (
    VectorGovError,
    AuthError,
    RateLimitError,
    ValidationError,
    ServerError,
    ConnectionError,
    TimeoutError,
)


class HTTPClient:
    """Cliente HTTP minimalista (sem dependências externas)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _get_headers(self) -> dict[str, str]:
        """Retorna headers padrão para requisições."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "vectorgov-python/0.1.0",
            "Accept": "application/json",
        }

    def _handle_error(self, status_code: int, response_body: str) -> None:
        """Converte erros HTTP em exceções apropriadas."""
        from vectorgov.exceptions import TierError

        try:
            error_data = json.loads(response_body)
            message = error_data.get("detail", error_data.get("message", response_body))
        except json.JSONDecodeError:
            error_data = {}
            message = response_body

        if status_code == 401:
            raise AuthError(message)
        elif status_code == 403:
            upgrade_url = error_data.get("upgrade_url") if isinstance(error_data, dict) else None
            raise TierError(message, upgrade_url=upgrade_url)
        elif status_code == 429:
            retry_after = None
            if isinstance(error_data, dict):
                retry_after = error_data.get("retry_after")
            raise RateLimitError(message, retry_after=retry_after)
        elif status_code == 400:
            field = error_data.get("field") if isinstance(error_data, dict) else None
            raise ValidationError(message, field=field)
        elif status_code >= 500:
            raise ServerError(message)
        else:
            raise VectorGovError(message, status_code=status_code)

    def request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> dict[str, Any]:
        """Faz uma requisição HTTP.

        Args:
            method: GET, POST, etc.
            path: Caminho da API (ex: /sdk/search)
            data: Dados para enviar no body (JSON)
            params: Query parameters
            timeout: Timeout em segundos (override do padrão)
            max_retries: Máximo de tentativas (override do padrão)

        Returns:
            Response JSON como dicionário

        Raises:
            VectorGovError: Em caso de erro
        """
        url = f"{self.base_url}{path}"
        req_timeout = timeout if timeout is not None else self.timeout
        req_retries = max_retries if max_retries is not None else self.max_retries

        # Adiciona query params
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if query_string:
                url = f"{url}?{query_string}"

        # Prepara body
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")

        # Tenta com retry
        last_error = None
        for attempt in range(req_retries):
            try:
                request = Request(
                    url,
                    data=body,
                    headers=self._get_headers(),
                    method=method,
                )

                with urlopen(request, timeout=req_timeout) as response:
                    response_body = response.read().decode("utf-8")
                    return json.loads(response_body)

            except HTTPError as e:
                response_body = e.read().decode("utf-8")
                self._handle_error(e.code, response_body)

            except URLError as e:
                last_error = ConnectionError(f"Erro de conexão: {e.reason}")
                if attempt < req_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue

            except TimeoutError:
                last_error = TimeoutError()
                if attempt < req_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue

        if last_error:
            raise last_error
        raise VectorGovError("Erro desconhecido na requisição")

    def get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Requisição GET."""
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        data: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """Requisição POST."""
        return self.request("POST", path, data=data, timeout=timeout)

    def stream(
        self,
        path: str,
        data: Optional[dict] = None,
    ):
        """Faz uma requisição POST com streaming SSE.

        Args:
            path: Caminho da API
            data: Dados para enviar no body

        Yields:
            Dicionários com eventos SSE parseados

        Raises:
            VectorGovError: Em caso de erro
        """
        url = f"{self.base_url}{path}"

        # Prepara body
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")

        # Headers para SSE
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        try:
            request = Request(
                url,
                data=body,
                headers=headers,
                method="POST",
            )

            with urlopen(request, timeout=120) as response:  # Timeout maior para streaming
                for line in response:
                    line = line.decode("utf-8").strip()

                    # Ignora linhas vazias
                    if not line:
                        continue

                    # Parse SSE data lines
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])
                            yield event_data
                        except json.JSONDecodeError:
                            continue

        except HTTPError as e:
            response_body = e.read().decode("utf-8")
            self._handle_error(e.code, response_body)

        except URLError as e:
            raise ConnectionError(f"Erro de conexão: {e.reason}")

        except Exception as e:
            raise VectorGovError(f"Erro no streaming: {str(e)}")


    def delete(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Requisicao DELETE."""
        return self.request("DELETE", path, params=params)

    def post_multipart(
        self,
        path: str,
        files: dict[str, tuple],
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Requisicao POST multipart/form-data para upload de arquivos."""
        import uuid

        url = f"{self.base_url}{path}"
        boundary = uuid.uuid4().hex
        CRLF = "\r\n"

        body_parts = []

        if data:
            for key, value in data.items():
                part = "--" + boundary + CRLF + 'Content-Disposition: form-data; name="' + key + '"' + CRLF + CRLF + str(value) + CRLF
                body_parts.append(part.encode("utf-8"))

        for field_name, (filename, file_obj, content_type) in files.items():
            file_content = file_obj.read()
            header = "--" + boundary + CRLF + 'Content-Disposition: form-data; name="' + field_name + '"; filename="' + filename + '"' + CRLF + "Content-Type: " + content_type + CRLF + CRLF
            body_parts.append(header.encode("utf-8"))
            body_parts.append(file_content)
            body_parts.append(CRLF.encode("utf-8"))

        body_parts.append(("--" + boundary + "--" + CRLF).encode("utf-8"))

        body = b"".join(body_parts)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "vectorgov-python/0.1.0",
            "Accept": "application/json",
        }

        try:
            request = Request(url, data=body, headers=headers, method="POST")
            with urlopen(request, timeout=120) as response:
                response_body = response.read().decode("utf-8")
                return json.loads(response_body)

        except HTTPError as e:
            response_body = e.read().decode("utf-8")
            self._handle_error(e.code, response_body)

        except URLError as e:
            raise ConnectionError(f"Erro de conexao: {e.reason}")
