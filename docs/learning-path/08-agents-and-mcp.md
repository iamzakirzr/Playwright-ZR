# 08 · Agents and MCP servers

## Why
An agent doesn't just talk; it **acts** (adds to cart, calls tools). The failures that matter are
wrong actions: calling the wrong tool, claiming an action it never took, forgetting context across
turns, or doing things outside its job. MCP servers are the tools agents call, so they need
contract tests like any API.

## The app under test
[`apps/shop_assistant/`](../../apps/shop_assistant): a FastAPI service with a tool-calling agent
over Ollama. [`agent.py`](../../apps/shop_assistant/agent.py) has the guards the tests found were
needed: argument normalisation, an "action claimed but no tool called" check, and a hybrid scope
guard (regex allow-list first, LLM classifier second).
Its client is [`api/shop_assistant_client.py`](../../api/shop_assistant_client.py), a service object like chapter 03.

## Read the tests
1. [`tests/ai/agent/test_agent_units.py`](../../tests/ai/agent/test_agent_units.py): guards and tool
   routing with a scripted model. Offline.
2. [`tests/ai/agent/test_agent_live.py`](../../tests/ai/agent/test_agent_live.py): the real model over
   HTTP: **tool correctness** (DeepEval `ToolCorrectnessMetric`), cart state checked through the
   API (not the reply text), multi-turn memory, off-topic refusal.
3. [`tests/ai/agent/test_assistant_feature.py`](../../tests/ai/agent/test_assistant_feature.py): the same in Gherkin.
4. [`tests/ai/mcp/test_store_mcp_server.py`](../../tests/ai/mcp/test_store_mcp_server.py): the MCP
   server in [`apps/store_mcp/`](../../apps/store_mcp) over two transports: in-process (fast) and
   stdio subprocess (what Claude Desktop or Cursor launch).

## Run
```bash
pytest -m "agent and not live"      # offline
pytest -m "agent and live"          # needs Ollama
pytest -m mcp
```

## The key idea: verify the side effect
"I've added it to your cart!" proves nothing. The tests read `/cart/{session}` and assert the
quantity changed. Trust state, not words.

## Try it
Add a `clear_cart` tool to the agent (schema in `TOOLS`, handler in `run_tool`), a scripted unit
test that routes "empty my basket" to it, then a live test that fills the cart, clears it, and checks
`/cart/{session}` through the API.

## Test your knowledge
1. Why does the scope guard fail *open* (allow) when the LLM classifier errors?
2. What does testing MCP over stdio catch that in-process testing misses?

<details><summary>Answers</summary>

1. Blocking a real customer is worse than answering one off-topic question; the regex allow-list
   already handles the clear cases.
2. Startup and packaging bugs: import errors, print statements corrupting the protocol stream,
   a wrong `__main__` entry point.
</details>
