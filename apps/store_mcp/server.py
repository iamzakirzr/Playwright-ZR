"""A small MCP (Model Context Protocol) server exposing the store to AI agents.

MCP is how agents such as Claude, Copilot or Cursor get *tools*. Testing an
MCP server means testing a contract: tool discovery (names and JSON schemas),
tool results, and error behaviour, over both in-process and stdio transports.

Two MCP v2 conventions matter for testability:

* Return **typed models** (Pydantic). They publish an output schema and
  ``structured_content`` that clients can validate; a bare ``dict`` does not.
* Raise ``ToolError`` for *expected* failures, whose message reaches the agent.
  Any other exception is treated as a crash and its text is withheld from the
  client, a deliberate security default.

Run it for a real client (stdio)::

    python -m apps.store_mcp
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from ai.search import BM25Retriever, load_documents
from apps.shop_assistant.catalog import PRODUCTS, UnknownProductError, resolve_product

server = MCPServer(
    name="sauce-store",
    instructions="Tools for the Sauce Demo Store: list products, look up prices, search store policies.",
)
_retriever = BM25Retriever(load_documents())


class Product(BaseModel):
    """A catalogue entry."""

    name: str
    price: float


class Passage(BaseModel):
    """A policy passage returned by search."""

    id: str
    text: str


@server.tool()
def list_products() -> list[Product]:
    """List every product in the catalogue with its price in USD."""
    return [Product(name=name, price=price) for name, price in PRODUCTS.items()]


@server.tool()
def get_price(product: str) -> Product:
    """Return the catalogue name and price of a product (loose names such as "backpack" are accepted).

    Raises:
        ToolError: If the product isn't sold (the agent sees the message).
    """
    try:
        name = resolve_product(product)
    except UnknownProductError as exc:
        raise ToolError(str(exc)) from exc
    return Product(name=name, price=PRODUCTS[name])


@server.tool()
def search_policies(query: str, k: int = 3) -> list[Passage]:
    """Keyword-search the store policy knowledge base; returns up to ``k`` passages, best first.

    Raises:
        ToolError: If ``k`` is outside 1-10.
    """
    if not 1 <= k <= 10:
        raise ToolError("k must be between 1 and 10")
    return [Passage(id=r.document.id, text=r.document.text) for r in _retriever.search(query, k=k, min_score=1e-9)]
