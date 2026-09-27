# 15 · Building and testing agents with LangChain and LangGraph

## Why
Chapters 06 to 14 test AI apps that already exist. This one **builds** an agent the way most
teams do today, with LangChain tools and a LangGraph graph, and tests it at every layer. The same
shop assistant already exists as a hand-written tool loop ([`agent.py`](../../apps/shop_assistant/agent.py),
chapter 08), so you can compare what the framework gives you and what it doesn't.

## The pieces, and where each one lives
| LangChain / LangGraph concept | In this repo |
|---|---|
| Chat model with tool calling (`ChatOllama`, `bind_tools`) | [`langgraph_agent.py`](../../apps/shop_assistant/langgraph_agent.py) `__init__` |
| Tools from typed functions (`@tool`) | `_make_tools`: `Literal[...]` becomes an `enum`, `Field(ge=1)` a `minimum` |
| Injected run config (`RunnableConfig`, hidden from the model) | tools read `thread_id` from it to find the session's cart |
| State graph (`StateGraph`, `MessagesState`) | `_build_graph`, `ShopState` |
| Prebuilt tool executor and router (`ToolNode`, `tools_condition`) | `_build_graph` |
| Memory (`InMemorySaver` checkpointer, `thread_id`) | `compile(checkpointer=...)`, `history()`, `reset()` |
| Loop bound (`recursion_limit`, `GraphRecursionError`) | `_config`, `chat`, `_close_turn` |
| RAG as a graph node vs. as a tool (agentic RAG) | `retrieval="node"` (default) / `retrieval="tool"` |
| LCEL chain (for contrast: a pipeline, not an agent) | [`ai/chatbot/langchain_client.py`](../../ai/chatbot/langchain_client.py), chapter 14 |

```
START -> retrieve -> agent --(tool calls?)--> tools -> agent -> ... -> END
                           \--(no tool calls)--> END
```

## What building it taught (all measured, not assumed)
1. **Let the schema say what's valid.** The hand-written agent failed in CI because the 1.5B model
   sent `{"product": "Product name"}`, copying the schema's description. With
   `product: Literal[<catalogue names>]` the schema is an `enum`, and `ToolNode` turns a violation
   into an error `ToolMessage`. The model reads it and retries with a valid name. The unit test
   `test_invalid_arguments_are_fed_back_and_the_model_recovers` replays the CI arguments.
2. **Only feed back errors the model can fix.** `handle_tool_errors=(ToolInvocationError,
   ValueError)` sends schema and domain errors back; anything else (a broken retriever) propagates
   and fails the test. `handle_tool_errors=True` would hide real bugs behind polite replies. Note:
   in LangGraph 1.2 a schema violation raises `ToolInvocationError`, **not** a `ValueError`; the
   first version of this agent crashed on it.
3. **Don't let a small model decide whether to retrieve.** In tool mode, qwen2.5:1.5b called
   `search_policies` in **0 of 6** policy questions, even when told to ALWAYS call it, and invented
   policy instead: "30 days" for a 45-day window, "open 24 hours", "$5" express shipping. With
   retrieval as a graph node, the same model answers from the store's policy. A decision the model
   can't be trusted with belongs in an edge of the graph.
4. **Bound the loop at the right step.** `recursion_limit = 2n - 1` allows `n` model calls and
   stops *before* a tools step whose result no model call would ever see. A cart change the agent
   never reports is worse than no change. After the bound is hit, `_close_turn` answers the dangling
   tool calls, or the next turn's history would be rejected.
5. **Rebuild the cart into the prompt on every model call.** Same lesson as the hand-written agent:
   a prompt built once per turn goes stale after the first tool call.

## Testing it
- **Offline, no model:** [`ai/chatbot/scripted_chat_model.py`](../../ai/chatbot/scripted_chat_model.py)
  is a LangChain chat model that replays scripted `AIMessage`s. Unlike LangChain's own fakes it
  can `bind_tools`, and it records the tool schemas and every message list the model was shown.
  [`test_langgraph_agent_units.py`](../../tests/ai/langgraph/test_langgraph_agent_units.py) covers:
  graph shape, tool schemas, trajectory, cart state, what the model saw, error feedback, memory,
  thread isolation, the loop bound, and both retrieval modes. 18 tests, under a second.
- **Live, real model:** [`test_langgraph_agent_live.py`](../../tests/ai/langgraph/test_langgraph_agent_live.py)
  runs the four-turn add / ask / remove / check conversation, DeepEval's rule-based
  `ToolCorrectnessMetric` on the calls that took effect, grounded policy answers, and an
  off-topic request that must not touch the cart. Every failure message carries the per-turn
  trajectory.

The oracles are the same as chapter 08's, in order of trust: **state** (read the cart, never the
reply), **trajectory** (which tools, which arguments), then **text**.

## Tracing (optional, hosted)
LangChain and LangGraph send traces to LangSmith when `LANGSMITH_TRACING=true` and
`LANGSMITH_API_KEY` are set; no code change is needed. It needs a hosted account, so nothing here
depends on it: the trajectory the tests assert on comes from the graph's own message history
(`AgentTurn.tool_calls`), which works offline.

## Run
```bash
pytest tests/ai/langgraph -m "not live"   # offline: scripted model
pytest tests/ai/langgraph                 # with Ollama: + real qwen2.5:1.5b
```

## Try it
1. Construct the agent with `retrieval="tool"` in the live fixture and run
   `test_policy_answers_come_from_the_retrieved_policy`. Read the trajectory in the failure
   message: no `search_policies` call, and an invented answer.
2. Add a `clear_cart` tool. Write the unit test first: scripted `tool_call_message("clear_cart")`,
   then assert the cart is empty and the trajectory is `["clear_cart"]`.
3. Change `handle_tool_errors` to `True` and run the unit tests: which test fails, and why is
   that failure the one you want?

## Test your knowledge
1. Why is `product` typed as `Literal[...]` instead of `str` with a good description?
2. What is the difference between the `retrieve` node and the `search_policies` tool, and when
   would you choose the tool?
3. Why is the recursion limit `2n - 1` and not `2n`?
4. Why does the live `ToolCorrectnessMetric` test count only the calls that succeeded?

<details><summary>Answers</summary>

1. A `Literal` becomes an `enum` in the schema: the model sees the exact valid values, and anything
   else is rejected before the tool runs. A description is only a hint, and a 1.5B model copied it.
2. The node always retrieves, before the model runs; the tool lets the model decide. Choose the tool
   when the model is strong enough to decide reliably (measure it, as above) and retrieving on every
   message is too expensive or pulls in irrelevant passages.
3. Steps alternate agent, tools, agent. With `2n` the tools step after the last allowed model call
   would still run, changing the cart without any model call reporting it.
4. A rejected call that the model then corrected had no effect, and the error-feedback loop is how
   LangGraph agents are meant to work. The trajectory still records it, so a test can bound how many
   retries are acceptable.
</details>
