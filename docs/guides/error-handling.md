# Tratamento de Erros

O VectorGov SDK define 7 classes de exceção para facilitar o tratamento granular de erros.

## Hierarquia

```
VectorGovError (base)
├── AuthError          (401)
├── RateLimitError     (429) — tem retry_after
├── ValidationError    (400) — tem field
├── TierError          (403) — tem upgrade_url
├── ServerError        (500)
├── ConnectionError    (sem HTTP)
└── TimeoutError       (sem HTTP)
```

## Exceções

### `VectorGovError`

Base de todas as exceções. Sempre tem `message`, `status_code` (opcional) e `response` (dict bruto da API, opcional).

```python
from vectorgov.exceptions import VectorGovError

try:
    result = vg.search("query")
except VectorGovError as e:
    print(f"Erro: {e.message}")
    print(f"HTTP: {e.status_code}")
```

### `AuthError` (401)

API key inválida, expirada ou ausente.

```python
from vectorgov.exceptions import AuthError

try:
    vg = VectorGov(api_key="vg_chave_invalida")
    vg.search("teste")
except AuthError:
    print("Verifique sua API key em https://vectorgov.io/playground")
```

### `RateLimitError` (429)

Limite de requisições excedido. O atributo `retry_after` indica quantos segundos aguardar.

```python
import time
from vectorgov.exceptions import RateLimitError

try:
    result = vg.search("query")
except RateLimitError as e:
    print(f"Rate limit. Retry em {e.retry_after}s")
    time.sleep(e.retry_after or 60)
    result = vg.search("query")  # tenta novamente
```

### `ValidationError` (400)

Parâmetros inválidos. O atributo `field` indica qual campo falhou.

```python
from vectorgov.exceptions import ValidationError

try:
    result = vg.search("")  # query vazia
except ValidationError as e:
    print(f"Campo inválido: {e.field}")  # "query"
    print(f"Detalhe: {e.message}")
```

### `TierError` (403)

Recurso não disponível no plano atual (ex: `smart_search` requer Premium). O atributo `upgrade_url` redireciona para upgrade.

```python
from vectorgov.exceptions import TierError

try:
    result = vg.smart_search("query")
except TierError as e:
    print(f"Plano insuficiente: {e.message}")
    if e.upgrade_url:
        print(f"Upgrade: {e.upgrade_url}")
    # Fallback para busca simples
    result = vg.search("query")
```

### `ServerError` (500)

Erro interno do servidor VectorGov. Geralmente transitório.

```python
from vectorgov.exceptions import ServerError

try:
    result = vg.search("query")
except ServerError:
    print("Erro no servidor. Tente novamente em alguns segundos.")
```

### `ConnectionError`

Falha de rede (sem resposta HTTP). DNS, firewall, servidor offline.

```python
from vectorgov.exceptions import ConnectionError

try:
    result = vg.search("query")
except ConnectionError:
    print("Sem conexão com o servidor. Verifique sua rede.")
```

### `TimeoutError`

Requisição excedeu o tempo limite.

```python
from vectorgov.exceptions import TimeoutError

try:
    result = vg.smart_search("query complexa")
except TimeoutError:
    print("Timeout. Tente uma query mais simples ou aumente o timeout.")
```

## Padrão Recomendado

```python
from vectorgov.exceptions import (
    AuthError, RateLimitError, TierError,
    ValidationError, VectorGovError,
)
import time

def buscar_com_retry(vg, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return vg.smart_search(query)

        except TierError:
            # Fallback para método do plano atual
            return vg.search(query)

        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(e.retry_after or 30)
                continue
            raise

        except ValidationError as e:
            # Erro do cliente — não adianta retry
            raise

        except AuthError:
            # API key inválida — não adianta retry
            raise

        except VectorGovError:
            # Erro transitório (server, timeout, connection)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
```
