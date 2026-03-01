"""
Cliente HTTP interno do VectorGov SDK.
"""

from __future__ import annotations

import http.client
import json
import random
import ssl
import time
from typing import Any, Optional
from urllib.parse import urlencode, urlparse

from vectorgov.exceptions import (
    AuthError,
    ConnectionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    VectorGovError,
)

_RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _backoff_delay(attempt: int, base_delay: float) -> float:
    """Exponential backoff com jitter (50-100%)."""
    exp = min(base_delay * (2 ** attempt), 30.0)
    return exp * (0.5 + random.random() * 0.5)


def _sanitize_filename(name: str) -> str:
    """Remove caracteres perigosos de filenames para multipart."""
    name = name.replace('"', "_").replace("\\", "_").replace("/", "_")
    return name[:255]


class HTTPClient:
    """Cliente HTTP com connection pooling (http.client keep-alive)."""

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

        parsed = urlparse(self.base_url)
        self._scheme = parsed.scheme
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or (443 if self._scheme == "https" else 80)
        self._base_path = parsed.path.rstrip("/")

        self._conn: Optional[http.client.HTTPSConnection | http.client.HTTPConnection] = None

    def _get_conn(self) -> http.client.HTTPSConnection | http.client.HTTPConnection:
        """Retorna conexão keep-alive, criando se necessário."""
        if self._conn is not None:
            return self._conn

        if self._scheme == "https":
            ctx = ssl.create_default_context()
            self._conn = http.client.HTTPSConnection(
                self._host, self._port, timeout=self.timeout, context=ctx,
            )
        else:
            self._conn = http.client.HTTPConnection(
                self._host, self._port, timeout=self.timeout,
            )
        return self._conn

    def _reset_conn(self) -> None:
        """Fecha e descarta a conexão atual."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def close(self) -> None:
        """Fecha a conexão HTTP."""
        self._reset_conn()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _get_headers(self) -> dict[str, str]:
        """Retorna headers padrão para requisições."""
        from vectorgov import __version__

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"vectorgov-sdk-python/{__version__}",
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
        """Faz uma requisição HTTP com retry e connection pooling.

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
        full_path = f"{self._base_path}{path}"
        req_timeout = timeout if timeout is not None else self.timeout
        req_retries = max_retries if max_retries is not None else self.max_retries

        # Adiciona query params (URL-encoded)
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                full_path = f"{full_path}?{urlencode(filtered)}"

        # Prepara body
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")

        headers = self._get_headers()

        # Tenta com retry
        last_error: Optional[Exception] = None
        last_error_body: Optional[str] = None
        for attempt in range(req_retries):
            try:
                conn = self._get_conn()
                conn.timeout = req_timeout
                conn.request(method, full_path, body=body, headers=headers)
                response = conn.getresponse()
                response_body = response.read().decode("utf-8")

                if 200 <= response.status < 300:
                    return json.loads(response_body)

                # Erro HTTP — checar se é retriable
                if response.status in _RETRIABLE_STATUS_CODES and attempt < req_retries - 1:
                    last_error_body = response_body

                    retry_after = None
                    if response.status == 429:
                        ra_header = response.getheader("Retry-After")
                        if ra_header:
                            try:
                                retry_after = float(ra_header)
                            except (ValueError, TypeError):
                                pass

                    delay = retry_after or _backoff_delay(attempt, self.retry_delay)
                    time.sleep(delay)
                    continue

                # Erro não-retriable — levanta imediato
                self._handle_error(response.status, response_body)

            except (http.client.RemoteDisconnected, http.client.CannotSendRequest,
                    BrokenPipeError, OSError) as e:
                # Conexão quebrou — resetar e retry
                self._reset_conn()
                last_error = ConnectionError(f"Erro de conexão: {e}")
                if attempt < req_retries - 1:
                    time.sleep(_backoff_delay(attempt, self.retry_delay))
                continue

            except TimeoutError:
                self._reset_conn()
                last_error = TimeoutError()
                if attempt < req_retries - 1:
                    time.sleep(_backoff_delay(attempt, self.retry_delay))
                continue

        if last_error:
            raise last_error
        if last_error_body:
            self._handle_error(500, last_error_body)
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
        max_retries: Optional[int] = None,
    ):
        """Faz uma requisição POST com streaming SSE e retry.

        Args:
            path: Caminho da API
            data: Dados para enviar no body
            max_retries: Tentativas de reconexão (default: self.max_retries)

        Yields:
            Dicionários com eventos SSE parseados

        Raises:
            VectorGovError: Em caso de erro
        """
        full_path = f"{self._base_path}{path}"
        retries = max_retries if max_retries is not None else self.max_retries

        body = None
        if data:
            body = json.dumps(data).encode("utf-8")

        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        last_event_id: Optional[str] = None

        for attempt in range(retries):
            try:
                req_headers = dict(headers)
                if last_event_id:
                    req_headers["Last-Event-Id"] = last_event_id

                conn = self._get_conn()
                conn.timeout = 120
                conn.request("POST", full_path, body=body, headers=req_headers)
                response = conn.getresponse()

                if response.status >= 400:
                    response_body = response.read().decode("utf-8")
                    if response.status in _RETRIABLE_STATUS_CODES and attempt < retries - 1:
                        time.sleep(_backoff_delay(attempt, self.retry_delay))
                        self._reset_conn()
                        continue
                    self._handle_error(response.status, response_body)

                # Lê SSE line-by-line
                buffer = b""
                while True:
                    chunk = response.read(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    while b"\n" in buffer:
                        line_bytes, buffer = buffer.split(b"\n", 1)
                        line = line_bytes.decode("utf-8").strip()
                        if not line:
                            continue
                        if line.startswith("id: "):
                            last_event_id = line[4:]
                        elif line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                continue
                # Stream terminou normalmente
                return

            except (http.client.RemoteDisconnected, http.client.CannotSendRequest,
                    BrokenPipeError, OSError):
                self._reset_conn()
                if attempt < retries - 1:
                    time.sleep(_backoff_delay(attempt, self.retry_delay))
                    continue
                raise ConnectionError("Conexão perdida durante streaming")

            except Exception as e:
                self._reset_conn()
                raise VectorGovError(f"Erro no streaming: {str(e)}")

    def delete(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Requisição DELETE."""
        return self.request("DELETE", path, params=params)

    def post_multipart(
        self,
        path: str,
        files: dict[str, tuple],
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Requisição POST multipart/form-data para upload de arquivos."""
        import uuid

        full_path = f"{self._base_path}{path}"
        boundary = uuid.uuid4().hex
        CRLF = "\r\n"

        body_parts = []

        if data:
            for key, value in data.items():
                part = (
                    f"--{boundary}{CRLF}"
                    f'Content-Disposition: form-data; name="{key}"{CRLF}'
                    f"{CRLF}{value}{CRLF}"
                )
                body_parts.append(part.encode("utf-8"))

        for field_name, (filename, file_obj, content_type) in files.items():
            safe_name = _sanitize_filename(filename)
            file_content = file_obj.read()
            header = (
                f"--{boundary}{CRLF}"
                f'Content-Disposition: form-data; name="{field_name}"; filename="{safe_name}"{CRLF}'
                f"Content-Type: {content_type}{CRLF}"
                f"{CRLF}"
            )
            body_parts.append(header.encode("utf-8"))
            body_parts.append(file_content)
            body_parts.append(CRLF.encode("utf-8"))

        body_parts.append(f"--{boundary}--{CRLF}".encode("utf-8"))

        body = b"".join(body_parts)

        from vectorgov import __version__

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": f"vectorgov-sdk-python/{__version__}",
            "Accept": "application/json",
        }

        try:
            conn = self._get_conn()
            conn.timeout = 120
            conn.request("POST", full_path, body=body, headers=headers)
            response = conn.getresponse()
            response_body = response.read().decode("utf-8")

            if 200 <= response.status < 300:
                return json.loads(response_body)

            self._handle_error(response.status, response_body)

        except (http.client.RemoteDisconnected, http.client.CannotSendRequest,
                BrokenPipeError, OSError) as e:
            self._reset_conn()
            raise ConnectionError(f"Erro de conexão: {e}")
