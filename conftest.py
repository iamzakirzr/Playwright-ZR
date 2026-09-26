"""Shared fixtures. Tests request intent-level objects (page objects, service
clients, repositories, chatbot, metrics) and never build them by hand."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import Playwright

from api import AuthClient, BookingClient
from config import Settings, get_settings
from db.connection import create_connection
from db.repositories import BookingRepository, OrderRepository, UserRepository
from pages import CartPage, CheckoutPage, InventoryPage, LoginPage

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

TESTS_ROOT = Path(__file__).parent / "tests"


# --------------------------------------------------------------------------- #
# Markers are derived automatically, so no test needs decorating by hand:
#   * folder names   -> tests/ai/redteam/x.py gets `ai` and `redteam`
#   * fixture usage  -> anything needing Ollama gets `live`, a judge gets `judge`,
#                       the opt-in 7B judge also gets `strong_judge`
# --------------------------------------------------------------------------- #
LIVE_FIXTURES = {"ollama_models", "require_ollama_model"}
#: Folder names that map to a differently named marker (tests/mobile/web -> mobile_web).
FOLDER_MARKER_ALIASES = {"web": "mobile_web", "native": "mobile_native"}
JUDGE_FIXTURES = {"judge", "strong_metrics", "ragas_llm"}
STRONG_JUDGE_FIXTURES = {"strong_metrics", "ragas_llm"}


def pytest_collection_modifyitems(config, items):
    """Attach folder-based and dependency-based markers to every collected test."""
    for item in items:
        try:
            parts = Path(item.fspath).relative_to(TESTS_ROOT).parts
        except ValueError:
            continue
        for folder in parts[:-1]:
            item.add_marker(getattr(pytest.mark, FOLDER_MARKER_ALIASES.get(folder, folder)))
        fixtures = set(getattr(item, "fixturenames", ()))
        if fixtures & LIVE_FIXTURES:
            item.add_marker(pytest.mark.live)
        if fixtures & JUDGE_FIXTURES:
            item.add_marker(pytest.mark.judge)
        if fixtures & STRONG_JUDGE_FIXTURES:
            item.add_marker(pytest.mark.strong_judge)


def pytest_configure(config):
    """Seed the data factories once per run so failures can be replayed with FAKER_SEED."""
    from data import seed_factories

    config._faker_seed = seed_factories()


def pytest_report_header(config):
    """Print the factory seed at the top of every run."""
    return f"test data seed: FAKER_SEED={getattr(config, '_faker_seed', '?')}"


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Typed, env-overridable configuration shared by every layer."""
    return get_settings()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, settings):
    """Allow pinning a pre-installed browser binary (e.g. locked-down CI images)."""
    if settings.browser_executable_path:
        return {**browser_type_launch_args, "executable_path": settings.browser_executable_path}
    return browser_type_launch_args


# --------------------------------------------------------------------------- #
# UI — page objects
# --------------------------------------------------------------------------- #
@pytest.fixture
def login_page(page, settings) -> LoginPage:
    """Login page object bound to the current browser page."""
    return LoginPage(page, settings.ui_base_url)


@pytest.fixture
def inventory_page(page, settings) -> InventoryPage:
    """Inventory (product list) page object."""
    return InventoryPage(page, settings.ui_base_url)


@pytest.fixture
def cart_page(page, settings) -> CartPage:
    """Cart page object."""
    return CartPage(page, settings.ui_base_url)


@pytest.fixture
def checkout_page(page, settings) -> CheckoutPage:
    """Checkout page object (all three checkout steps)."""
    return CheckoutPage(page, settings.ui_base_url)


@pytest.fixture
def logged_in(login_page, inventory_page, settings) -> InventoryPage:
    """Start a test already authenticated on the inventory page."""
    login_page.open().login_as(settings.ui_standard_user, settings.ui_password)
    return inventory_page.expect_loaded()


# --------------------------------------------------------------------------- #
# API — service clients
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def api_request(playwright: Playwright, settings):
    """Session-wide Playwright HTTP client for the booking API."""
    ctx = playwright.request.new_context(base_url=settings.api_base_url)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def auth_client(api_request) -> AuthClient:
    """Service object for the /auth endpoint."""
    return AuthClient(api_request)


@pytest.fixture(scope="session")
def auth_token(auth_client, settings) -> str:
    """A valid API token, created once per session."""
    return auth_client.create_token(settings.api_username, settings.api_password)


@pytest.fixture
def booking_client(api_request) -> BookingClient:
    """Unauthenticated booking client (read-only operations)."""
    return BookingClient(api_request)


@pytest.fixture
def authed_booking_client(api_request, auth_token) -> BookingClient:
    """Booking client carrying the auth cookie (write operations)."""
    return BookingClient(api_request).authenticate(auth_token)


# --------------------------------------------------------------------------- #
# SQL — repositories, each test isolated in a rolled-back transaction
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def db_connection(settings):
    """One seeded SQLite connection per session."""
    conn = create_connection(settings.db_path)
    yield conn
    conn.close()


@pytest.fixture
def db(db_connection):
    """Per-test transaction, rolled back afterwards so tests never see each other's writes."""
    db_connection.execute("BEGIN")
    yield db_connection
    db_connection.execute("ROLLBACK")


@pytest.fixture
def user_repo(db) -> UserRepository:
    """Repository for the users table."""
    return UserRepository(db)


@pytest.fixture
def order_repo(db) -> OrderRepository:
    """Repository for orders and order items."""
    return OrderRepository(db)


@pytest.fixture
def booking_repo(db) -> BookingRepository:
    """Repository for bookings mirrored from the API."""
    return BookingRepository(db)


# --------------------------------------------------------------------------- #
# Ollama (local LLMs): shared by every layer that needs a model
# (AI suites, self-healing locators, vision checks). Missing server or model -> skip.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def ollama_request(playwright: Playwright, settings):
    """Playwright request context pointed at the Ollama server."""
    ctx = playwright.request.new_context(base_url=settings.ollama_host)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def ollama_models(ollama_request) -> set[str]:
    """Names of pulled models; skips the test when Ollama is unreachable."""
    try:
        response = ollama_request.get("/api/tags", timeout=5_000)
        models = {m["name"] for m in response.json().get("models", [])} if response.ok else set()
    except Exception:  # noqa: BLE001 - any failure means "not available"
        models = set()
    if not models:
        pytest.skip("Ollama is not reachable; start `ollama serve` to run live AI tests")
    return models


@pytest.fixture(scope="session")
def require_ollama_model(ollama_models):
    """Factory: ``require_ollama_model("qwen2.5:7b")`` skips the test unless that model is pulled."""

    def _require(name: str) -> None:
        """Skip the current test if ``name`` is not pulled."""
        if name not in ollama_models:
            pytest.skip(f"Model '{name}' not pulled; run `ollama pull {name}`")

    return _require


# --------------------------------------------------------------------------- #
# AI fixtures live in tests/ai/conftest.py so heavy imports (torch, deepeval)
# only load when the AI suite is selected.
# --------------------------------------------------------------------------- #
