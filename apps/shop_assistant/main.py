"""FastAPI app: the AI e-commerce assistant that the AI tests exercise over HTTP.

Run it on its own::

    uvicorn apps.shop_assistant.main:app --port 8000

Endpoints:
    GET    /health               liveness
    POST   /chat                 {session_id, message} -> reply, tools_called, sources
    GET    /cart/{session_id}    the session's cart
    DELETE /session/{session_id} reset history and cart
"""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ai.search import BM25Retriever, HybridRetriever, SemanticRetriever, load_documents
from apps.shop_assistant.agent import ShopAgent
from config import get_settings


class ChatRequest(BaseModel):
    """Body of ``POST /chat``."""

    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2000)


class ToolCallOut(BaseModel):
    """One tool call in a chat response."""

    name: str
    arguments: dict
    output: dict


class ChatResponse(BaseModel):
    """Body returned by ``POST /chat``."""

    reply: str
    tools_called: list[ToolCallOut]
    sources: list[str]


class CartItem(BaseModel):
    """One cart line."""

    product: str
    quantity: int
    unit_price: float


class CartResponse(BaseModel):
    """Body returned by ``GET /cart/{session_id}``."""

    items: list[CartItem]
    total: float


@lru_cache(maxsize=1)
def get_agent() -> ShopAgent:
    """Build the agent once per process (indexing the knowledge base is the slow part)."""
    settings = get_settings()
    documents = load_documents()
    retriever = HybridRetriever([BM25Retriever(documents), SemanticRetriever(documents, settings.embedding_model)])
    return ShopAgent(retriever, settings.ollama_host, settings.chatbot_model, k=settings.retrieval_k)


app = FastAPI(title="Sauce Demo Shop Assistant", version="1.0")


@app.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Send one message to the agent within a session."""
    result = get_agent().handle(request.session_id, request.message)
    return ChatResponse(reply=result.reply, tools_called=[asdict(c) for c in result.tools_called], sources=result.sources)


@app.get("/cart/{session_id}", response_model=CartResponse)
def get_cart(session_id: str) -> CartResponse:
    """The session's cart (empty for an unknown session)."""
    return CartResponse(**get_agent().cart(session_id).as_dict())


@app.delete("/session/{session_id}", status_code=204)
def reset_session(session_id: str) -> None:
    """Forget the session's conversation and cart."""
    get_agent().reset(session_id)
