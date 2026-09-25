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
# Markers are derived from folder names, so `pytest -m api` just works.
# --------------------------------------------------------------------------- #
def pytest_collection_modifyitems(config, items):
    for item in items:
        try:
            layer = Path(item.fspath).relative_to(TESTS_ROOT).parts[0]
        except ValueError:
            continue
        item.add_marker(getattr(pytest.mark, layer))


@pytest.fixture(scope="session")
def settings() -> Settings:
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
    return LoginPage(page, settings.ui_base_url)


@pytest.fixture
def inventory_page(page, settings) -> InventoryPage:
    return InventoryPage(page, settings.ui_base_url)


@pytest.fixture
def cart_page(page, settings) -> CartPage:
    return CartPage(page, settings.ui_base_url)


@pytest.fixture
def checkout_page(page, settings) -> CheckoutPage:
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
    ctx = playwright.request.new_context(base_url=settings.api_base_url)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def auth_client(api_request) -> AuthClient:
    return AuthClient(api_request)


@pytest.fixture(scope="session")
def auth_token(auth_client, settings) -> str:
    return auth_client.create_token(settings.api_username, settings.api_password)


@pytest.fixture
def booking_client(api_request) -> BookingClient:
    return BookingClient(api_request)


@pytest.fixture
def authed_booking_client(api_request, auth_token) -> BookingClient:
    return BookingClient(api_request).authenticate(auth_token)


# --------------------------------------------------------------------------- #
# SQL — repositories, each test isolated in a rolled-back transaction
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def db_connection(settings):
    conn = create_connection(settings.db_path)
    yield conn
    conn.close()


@pytest.fixture
def db(db_connection):
    db_connection.execute("BEGIN")
    yield db_connection
    db_connection.execute("ROLLBACK")


@pytest.fixture
def user_repo(db) -> UserRepository:
    return UserRepository(db)


@pytest.fixture
def order_repo(db) -> OrderRepository:
    return OrderRepository(db)


@pytest.fixture
def booking_repo(db) -> BookingRepository:
    return BookingRepository(db)


# --------------------------------------------------------------------------- #
# AI fixtures live in tests/ai/conftest.py so heavy imports (torch, deepeval)
# only load when the AI suite is selected.
# --------------------------------------------------------------------------- #
