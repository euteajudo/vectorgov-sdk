# VectorGov MCP Server

Servidor MCP (Model Context Protocol) que permite integrar busca em legislação brasileira diretamente em ferramentas como Claude Desktop, Cursor, Windsurf, Cline e Continue.dev.

## O que é MCP?

O [Model Context Protocol](https://modelcontextprotocol.io/) é um padrão aberto criado pela Anthropic que permite que LLMs acessem ferramentas e dados externos de forma padronizada. Com o servidor MCP do VectorGov, você pode pesquisar legislação brasileira diretamente em conversas com o Claude ou em seu IDE.

## Instalação

```bash
pip install 'vectorgov[mcp]'
```

Ou, se preferir usar `uvx` (recomendado para Claude Desktop):

```bash
uvx vectorgov-mcp
```

## Configuração

### Obter API Key

1. Acesse [vectorgov.io/playground](https://vectorgov.io/playground)
2. Faça login ou crie uma conta
3. Na seção "API Keys", clique em "Nova API Key"
4. Copie a chave gerada (começa com `vg_`)

### Claude Desktop

Edite o arquivo de configuração:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

#### Opção 1: Usando uvx (Recomendado)

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "uvx",
            "args": ["vectorgov-mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

#### Opção 2: Usando Python instalado

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "python",
            "args": ["-m", "vectorgov.mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

#### Opção 3: Com caminho completo (Windows)

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "C:\\Users\\SeuUsuario\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
            "args": ["-m", "vectorgov.mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

### Cursor IDE

Adicione ao arquivo `.cursor/mcp.json` na raiz do seu projeto:

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "uvx",
            "args": ["vectorgov-mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

Ou configure globalmente em `~/.cursor/mcp.json`.

### Windsurf

Adicione ao arquivo de configuração do Windsurf:

```json
{
    "mcpServers": {
        "vectorgov": {
            "command": "uvx",
            "args": ["vectorgov-mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    }
}
```

### Cline (VSCode Extension)

1. Abra as configurações do Cline
2. Vá para "MCP Servers"
3. Clique em "Add Server"
4. Configure:

```json
{
    "name": "vectorgov",
    "command": "uvx",
    "args": ["vectorgov-mcp"],
    "env": {
        "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
    }
}
```

### Continue.dev

Adicione ao arquivo `~/.continue/config.json`:

```json
{
    "mcpServers": [
        {
            "name": "vectorgov",
            "command": "uvx",
            "args": ["vectorgov-mcp"],
            "env": {
                "VECTORGOV_API_KEY": "vg_sua_chave_aqui"
            }
        }
    ]
}
```

## Ferramentas Disponíveis

O servidor expõe três ferramentas que podem ser usadas pelo LLM:

### 1. `search_legislation`

Busca semântica em legislação brasileira.

**Parâmetros:**
- `query` (obrigatório): Pergunta ou termo de busca
- `top_k` (opcional): Quantidade de resultados (1-50, padrão: 5)
- `document_type` (opcional): Filtrar por tipo (lei, decreto, in, portaria)
- `year` (opcional): Filtrar por ano

**Exemplo de uso pelo LLM:**
> "Pesquise na legislação quando o ETP pode ser dispensado"

### 2. `list_available_documents`

Lista os documentos disponíveis na base.

**Exemplo de uso pelo LLM:**
> "Quais documentos estão disponíveis para consulta?"

### 3. `get_article_text`

Obtém o texto completo de um artigo específico.

**Parâmetros:**
- `document_type` (obrigatório): Tipo do documento (lei, decreto, in)
- `document_number` (obrigatório): Número do documento
- `year` (obrigatório): Ano do documento
- `article_number` (obrigatório): Número do artigo

**Exemplo de uso pelo LLM:**
> "Mostre o Art. 33 da Lei 14.133/2021"

## Recursos Disponíveis

### `legislation://info`

Informações sobre a base de legislação, incluindo documentos disponíveis e exemplos de uso.

## Executar Manualmente

Para testar o servidor manualmente:

```bash
# Via uvx (sem instalar)
uvx vectorgov-mcp

# Via pip (após instalar)
vectorgov-mcp

# Via Python
python -m vectorgov.mcp

# Com API key via argumento
vectorgov-mcp --api-key vg_sua_chave

# Com transporte diferente (para debugging)
vectorgov-mcp --transport sse
```

## Variáveis de Ambiente

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `VECTORGOV_API_KEY` | Chave de API do VectorGov | Sim |

## Troubleshooting

### "API key não fornecida"

**Causa:** A variável `VECTORGOV_API_KEY` não está configurada.

**Solução:**
1. Verifique se a chave está correta no arquivo de configuração
2. Certifique-se de que a chave começa com `vg_`
3. Teste a chave acessando https://vectorgov.io/playground

### "O SDK MCP não está instalado"

**Causa:** A dependência `mcp` não foi instalada.

**Solução:**
```bash
pip install 'vectorgov[mcp]'
# ou
pip install mcp
```

### Servidor não aparece no Claude Desktop

**Causas possíveis:**

1. **Arquivo de configuração em local errado**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **JSON inválido**
   - Verifique se não há vírgulas extras ou faltando
   - Use um validador de JSON online

3. **Python/uvx não encontrado**
   - Use o caminho completo para o executável
   - Verifique se Python está no PATH do sistema

4. **Claude Desktop não reiniciado**
   - Feche completamente o Claude Desktop (não apenas a janela)
   - Abra novamente

### Erro "Module not found: vectorgov"

**Causa:** O pacote não está instalado no Python correto.

**Solução:**
```bash
# Verificar qual Python está sendo usado
which python
python -c "import vectorgov; print(vectorgov.__version__)"

# Reinstalar se necessário
pip install --upgrade vectorgov[mcp]
```

### Timeout ou lentidão

**Causas possíveis:**

1. **Primeira execução:** O modelo pode demorar para carregar
2. **Conexão lenta:** Verifique sua conexão de internet
3. **Muitos resultados:** Reduza o `top_k` na busca

### Logs para debugging

Para ver logs detalhados do servidor:

```bash
# Linux/macOS
VECTORGOV_API_KEY=vg_xxx vectorgov-mcp 2>&1 | tee mcp.log

# Windows (PowerShell)
$env:VECTORGOV_API_KEY="vg_xxx"; vectorgov-mcp 2>&1 | Tee-Object mcp.log
```

## FAQ

### Quais documentos estão disponíveis?

Atualmente a base contém:
- **Lei 14.133/2021** - Nova Lei de Licitações e Contratos
- **IN SEGES 58/2022** - Estudo Técnico Preliminar (ETP)
- **IN SEGES 65/2021** - Pesquisa de Preços
- **IN SEGES 81/2022** - Plano de Contratações Anual

### Preciso de internet para usar?

Sim, o servidor faz requisições para a API VectorGov em https://vectorgov.io.

### Posso usar com outros LLMs além do Claude?

Sim! Qualquer ferramenta que suporte o protocolo MCP pode usar o servidor VectorGov, incluindo:
- Claude Desktop
- Cursor IDE
- Windsurf
- Cline
- Continue.dev
- Qualquer aplicação compatível com MCP

### Como atualizar o servidor?

```bash
pip install --upgrade vectorgov[mcp]
```

### Posso usar múltiplos servidores MCP?

Sim, você pode configurar múltiplos servidores no mesmo arquivo de configuração:

```json
{
    "mcpServers": {
        "vectorgov": { ... },
        "outro-servidor": { ... }
    }
}
```

## Suporte

- **Documentação:** https://vectorgov.io/documentacao
- **Issues:** https://github.com/euteajudo/vectorgov-sdk/issues
- **Email:** suporte@vectorgov.io
