"""Appium fixtures. Every test here skips unless an Appium server is running with a device attached."""

from __future__ import annotations

from pathlib import Path

import pytest

from mobile import AppiumDriverFactory, appium_is_running
from reporting import attach_png, attach_text

EVIDENCE_DIR = Path("reports/mobile-native")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """Remember each phase's report on the test item so fixtures can see whether the test failed."""
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


def save_evidence(driver, test_name: str) -> Path:
    """Write URL, contexts, page source and a screenshot for a failed test (also attached to Allure)."""
    folder = EVIDENCE_DIR / test_name
    folder.mkdir(parents=True, exist_ok=True)
    summary = f"url: {driver.current_url}\ncontexts: {driver.contexts}\n"
    (folder / "summary.txt").write_text(summary)
    (folder / "page_source.xml").write_text(driver.page_source)
    png = driver.get_screenshot_as_png()
    (folder / "screen.png").write_bytes(png)
    attach_text("device state", summary)
    attach_png("device screen", png)
    return folder


@pytest.fixture(scope="session")
def appium_factory(settings) -> AppiumDriverFactory:
    """Driver factory; skips the session's native tests when Appium isn't reachable."""
    if not appium_is_running(settings.appium_server_url):
        pytest.skip(f"No Appium server at {settings.appium_server_url} (see docs/learning-path/10-mobile.md)")
    return AppiumDriverFactory(settings)


@pytest.fixture
def android_chrome(appium_factory, request):
    """A fresh Chrome-on-Android session per test; on failure, device evidence is saved before it closes."""
    driver = appium_factory.create_chrome()
    yield driver
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        try:
            save_evidence(driver, request.node.name)
        except Exception as error:  # evidence is best-effort; never mask the real failure
            print(f"could not save device evidence: {error}")
    driver.quit()
