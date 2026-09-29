"""Shared fixtures. Tests request intent-level objects (page objects, service
clients, repositories, chatbot, metrics) and never build them by hand."""

from __future__ import annotations

import importlib.util
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

# Lean extras (e.g. api-sql CI installs only ``ui``) must not fail collection of
# unrelated suites that import optional stacks. Mirror the Appium guard for AI/visual.
collect_ignore_glob: list[str] = []
if importlib.util.find_spec("appium") is None:
    collect_ignore_glob.append("tests/mobile/**")
if importlib.util.find_spec("PIL") is None:
    collect_ignore_glob.extend(
        [
            "tests/ui/essentials/**",
            "tests/ui/visual/**",
            "tests/unit/test_visual_comparator.py",
        ]
    )
if importlib.util.find_spec("langchain_core") is None:
    collect_ignore_glob.extend(
        [
            "tests/ai/**",
            "tests/ui/healing/**",
            "tests/unit/test_shop_assistant_shared.py",
        ]
    )
if importlib.util.find_spec("deepeval") is None:
    collect_ignore_glob.append("tests/unit/test_metric_factory_gates.py")


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
    """Pick the run's base seed once and share it with xdist workers through FAKER_SEED.

    Workers start after this hook runs on the controller and inherit its environment, so every
    process uses the same base seed as the one printed in the report header.
    """
    from data import seed_factories

    config._faker_seed = seed_factories()
    os.environ["FAKER_SEED"] = str(config._faker_seed)


@pytest.fixture(autouse=True)
def _seed_test_data(request):
    """Reseed Faker per test from (base seed, test id).

    Each test's data then depends only on the base seed and its own id, not on which worker ran
    it or which tests ran before, so ``FAKER_SEED=<n> pytest <that test>`` reproduces it exactly.
    """
    from data import seed_factories

    seed_factories(f"{request.config._faker_seed}:{request.node.nodeid}")


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


@pytest.fixture(scope="session")
def sauce_auth_state(browser, settings, tmp_path_factory) -> Path:
    """Log in through the UI once per session and save cookies + localStorage to a file.

    Modules opt in by overriding ``browser_context_args`` (see ``tests/ui/test_checkout_e2e.py``);
    their tests then start signed in, skipping the login form, which saves a few seconds per test
    and removes a dependency on the login page from unrelated tests.
    """
    context = browser.new_context()
    try:
        page = context.new_page()
        LoginPage(page, settings.ui_base_url).open().login_as(settings.ui_standard_user, settings.ui_password)
        InventoryPage(page, settings.ui_base_url).expect_loaded()
        path = tmp_path_factory.mktemp("auth") / "sauce_state.json"
        context.storage_state(path=path)
        return path
    finally:
        context.close()


@pytest.fixture
def signed_in(inventory_page) -> InventoryPage:
    """Inventory page opened directly; the context must carry ``sauce_auth_state``."""
    return inventory_page.open().expect_loaded()


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
