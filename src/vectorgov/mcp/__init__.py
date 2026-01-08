"""
Servidor MCP (Model Context Protocol) do VectorGov.

Este módulo permite usar o VectorGov diretamente em aplicativos compatíveis
com MCP como Claude Desktop, Cursor, Windsurf, etc.

Instalação:
    pip install 'vectorgov[mcp]'

Configuração no Claude Desktop (claude_desktop_config.json):
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

Ou executar diretamente:
    vectorgov-mcp

Ou via Python:
    python -m vectorgov.mcp
"""

from vectorgov.mcp.server import create_server, run_server

__all__ = ["create_server", "run_server"]
