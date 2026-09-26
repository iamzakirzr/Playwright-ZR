"""MCP server testing: the contract an AI agent depends on.

Checked over two transports:
* **in-process** (``Client(server)``): fast, for every tool and edge case;
* **stdio subprocess** (``python -m apps.store_mcp``): what Claude Desktop or
  Cursor actually launch, proving the server starts and speaks the protocol.
"""
import sys

import pytest
from mcp import Client, StdioServerParameters

from ai.asyncio_bridge import run_sync
from apps.shop_assistant.catalog import PRODUCTS
from apps.store_mcp.server import server

EXPECTED_TOOLS = {"list_products", "get_price", "search_policies"}


async def _list_tools(target):
    """Connect to ``target`` and return its tool list."""
    async with Client(target) as client:
        return (await client.list_tools()).tools


async def _call(target, name: str, arguments: dict):
    """Connect to ``target`` and call one tool."""
    async with Client(target) as client:
        return await client.call_tool(name, arguments)


def call(name: str, **arguments):
    """Call a tool on the in-process server (sync helper for tests)."""
    return run_sync(_call(server, name, arguments))


class TestDiscovery:
    """Tool discovery: names, descriptions and input schemas are the API agents plan with."""

    def test_exposes_exactly_the_expected_tools(self):
        """No tool is missing and nothing unexpected is exposed (least privilege)."""
        assert {t.name for t in run_sync(_list_tools(server))} == EXPECTED_TOOLS

    def test_every_tool_is_described(self):
        """Agents choose tools from their descriptions, so none may be empty."""
        assert all(t.description and len(t.description) > 20 for t in run_sync(_list_tools(server)))

    def test_input_schemas_declare_required_parameters(self):
        """``get_price`` must require ``product``; ``search_policies`` must require ``query``."""
        schemas = {t.name: t.input_schema for t in run_sync(_list_tools(server))}
        assert schemas["get_price"]["required"] == ["product"]
        assert "query" in schemas["search_policies"]["required"]
        assert schemas["search_policies"]["properties"]["k"]["default"] == 3


class TestToolResults:
    """Happy-path results, checked against the source of truth (the catalogue and the corpus)."""

    def test_list_products_matches_catalogue(self):
        """Structured output lists every catalogue product with its price."""
        result = call("list_products")
        assert not result.is_error
        items = result.structured_content["result"]
        assert {i["name"]: i["price"] for i in items} == PRODUCTS

    @pytest.mark.parametrize("loose, name", [("backpack", "Sauce Labs Backpack"), ("bike lights", "Sauce Labs Bike Light")])
    def test_get_price_resolves_loose_names(self, loose, name):
        """Loose product names resolve to the catalogue entry and its price."""
        result = call("get_price", product=loose)
        assert result.structured_content == {"name": name, "price": PRODUCTS[name]}

    def test_search_policies_ranks_relevant_passage_first(self):
        """A shipping query returns shipping passages, best first."""
        result = call("search_policies", query="express shipping cost", k=2)
        ids = [p["id"] for p in result.structured_content["result"]]
        assert ids[0] == "shipping-3"


class TestErrors:
    """Errors must come back as tool errors (is_error=True) that the agent can read, not crash the server."""

    def test_unknown_product_is_a_tool_error(self):
        """Asking for a product that isn't sold returns an error result mentioning it."""
        result = call("get_price", product="gaming laptop")
        assert result.is_error
        assert "gaming laptop" in result.content[0].text

    @pytest.mark.parametrize("k", [0, 11])
    def test_out_of_range_k_is_rejected(self, k):
        """Server-side validation rejects k outside 1-10."""
        assert call("search_policies", query="refund", k=k).is_error

    def test_missing_required_argument_is_rejected(self):
        """Schema validation fails a call without the required argument."""
        assert call("get_price").is_error

    def test_server_survives_errors(self):
        """After an error, the next call on the same server still succeeds."""
        call("get_price", product="nonsense")
        assert not call("list_products").is_error


def test_stdio_transport_end_to_end():
    """Launch the server as a real subprocess over stdio (as MCP clients do) and call a tool."""
    params = StdioServerParameters(command=sys.executable, args=["-m", "apps.store_mcp"])

    tools = run_sync(_list_tools(params))
    result = run_sync(_call(params, "get_price", {"product": "onesie"}))

    assert {t.name for t in tools} == EXPECTED_TOOLS
    assert result.structured_content == {"name": "Sauce Labs Onesie", "price": 7.99}
