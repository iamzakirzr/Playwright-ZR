"""Network interception: mock, modify, block and wait for HTTP traffic.

The UI's behaviour for every backend state (data, empty, error) is tested without that state
having to exist on a real server, which is the main reason to mock the network.
"""

from playwright.sync_api import expect

from pages.playground import ProductsPage


def test_products_render_from_the_api(page, site, base_url_playground):
    """Happy path: the list shows what the API returned, and the request had the right query."""
    products = ProductsPage(page, base_url_playground).open().expect_loaded()

    assert products.names() == ["Backpack - $29.99", "Bike Light - $9.99"]
    assert site.requests_to("/api/products")[0].query == {"currency": ["USD"]}


def test_empty_catalogue_shows_empty_state(page, site, base_url_playground):
    """Mock an edge case the real backend rarely returns."""
    site.json("GET", "/api/products", [])

    products = ProductsPage(page, base_url_playground).open().expect_loaded()

    expect(products.status).to_have_text("No products")


def test_server_error_shows_friendly_message(page, site, base_url_playground):
    """A 500 from the API must not leave the page stuck on "Loading…"."""
    site.json("GET", "/api/products", {"error": "boom"}, status=500)

    products = ProductsPage(page, base_url_playground).open()

    expect(products.status).to_have_text("Could not load products")


def test_page_route_takes_precedence_over_context_route(page, site, base_url_playground):
    """``page.route`` handlers run before ``context.route`` ones: handy for one-test overrides."""
    page.route("**/api/products*", lambda route: route.fulfill(json=[{"name": "Onesie", "price": 7.99}]))

    products = ProductsPage(page, base_url_playground).open().expect_loaded()

    assert products.names() == ["Onesie - $7.99"]


def test_modify_a_real_response(page, site, base_url_playground, real_products_api):
    """Fetch from the real server, change one field, pass the rest through.

    ``route.fetch`` sends the request to the actual network (it skips other routes), so here it
    targets a real HTTP server started by the ``real_products_api`` fixture.
    """

    def discount_first_item(route):
        response = route.fetch(url=real_products_api)
        items = response.json()
        items[0]["price"] = 0
        route.fulfill(response=response, json=items)

    page.route("**/api/products*", discount_first_item)

    products = ProductsPage(page, base_url_playground).open().expect_loaded()

    assert products.names() == ["Backpack - $0.00", "Bike Light - $9.99"]


def test_blocked_images_do_not_break_the_page(page, site, base_url_playground):
    """Abort image requests (faster runs, or simulating a CDN outage); the content still loads."""
    page.route("**/*.png", lambda route: route.abort())

    with page.expect_event("requestfailed", lambda r: r.url.endswith(".png")):
        products = ProductsPage(page, base_url_playground).open()

    products.expect_loaded()
    assert products.banner.evaluate("img => img.naturalWidth") == 0
    assert len(products.names()) == 2


def test_wait_for_the_api_response(page, site, base_url_playground):
    """``expect_response`` waits for a specific call and exposes its status and body."""
    with page.expect_response("**/api/products*") as response_info:
        ProductsPage(page, base_url_playground).open()

    response = response_info.value
    assert response.ok
    assert [p["name"] for p in response.json()] == ["Backpack", "Bike Light"]


def test_crashing_endpoint_answers_500_instead_of_hanging(page, site, base_url_playground):
    """A broken fake endpoint fails fast (HTTP 500) and is recorded, so the test fails for the right reason."""

    def broken(_request):
        raise KeyError("boom")

    site.api("GET", "/api/products", broken)

    products = ProductsPage(page, base_url_playground).open()

    expect(products.status).to_have_text("Could not load products")
    assert site.errors == ["GET /api/products: KeyError('boom')"]
