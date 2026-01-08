"""
Permite executar o servidor MCP via `python -m vectorgov.mcp`.

Uso:
    python -m vectorgov.mcp
    python -m vectorgov.mcp --transport stdio
    python -m vectorgov.mcp --api-key vg_xxx
"""

from vectorgov.mcp.server import main

if __name__ == "__main__":
    main()
