"""The Playwright playground: a small static site with fake APIs, served inside Playwright.

It is an app under test like ``apps/shop_assistant``, built so each core Playwright technique
(network mocking, dialogs, frames, tabs, files, auth state, emulation, rich input) has a
deterministic page to practise on. :func:`serve_playground` installs it on a browser context.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import BrowserContext

from pages.support import ApiResponse, RecordedRequest, StaticSite

SITE_DIR = Path(__file__).with_name("site")
ORIGIN = "https://playground.local"  # https: geolocation and downloads need a secure context
PRODUCTS = [{"name": "Backpack", "price": 29.99}, {"name": "Bike Light", "price": 9.99}]
ORDERS = [{"id": 1, "product": "Backpack", "quantity": 2}, {"id": 2, "product": "Bike Light", "quantity": 1}]
#: What the page's "Download orders" button exports for ``ORDERS``.
ORDERS_CSV = "id,product,quantity\n1,Backpack,2\n2,Bike Light,1\n"


def _banner_png() -> bytes:
    """A small PNG so the page's <img> has something to load (and something to block)."""
    buffer = io.BytesIO()
    Image.new("RGB", (8, 4), "orange").save(buffer, format="PNG")
    return buffer.getvalue()


def _login(request: RecordedRequest) -> ApiResponse:
    """POST /api/login: returns a token and sets a session cookie."""
    username = (request.body or {}).get("username", "")
    return ApiResponse({"token": f"tok-{username}"}, headers={"Set-Cookie": f"session={username}; Path=/"})


def _me(request: RecordedRequest) -> ApiResponse:
    """GET /api/me: 200 with the user when the session cookie is present, else 401."""
    user = request.cookie("session")
    return ApiResponse({"username": user}) if user else ApiResponse({"error": "not signed in"}, status=401)


def serve_playground(context: BrowserContext) -> StaticSite:
    """The playground site with its default endpoints, installed on ``context``."""
    site = StaticSite(context, SITE_DIR, ORIGIN)
    site.json("GET", "/api/products", PRODUCTS)
    site.api("GET", "/img/banner.png", lambda _r: ApiResponse(_banner_png(), content_type="image/png"))
    site.json("GET", "/api/orders", ORDERS)
    site.api("POST", "/api/login", _login)
    site.api("GET", "/api/me", _me)
    return site.install()
