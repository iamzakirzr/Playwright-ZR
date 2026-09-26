"""Entry point: ``python -m apps.store_mcp`` serves the store MCP server over stdio."""
from apps.store_mcp.server import server

if __name__ == "__main__":
    server.run("stdio")
