# 10 · Mobile: emulation and Appium

## Why
Most mobile bugs in a web shop are layout bugs (a button off-screen, a menu that needs hover), and
Playwright's device emulation finds them in seconds on any laptop. Behaviour that only a real
device shows (the real Android Chrome, rotation, native apps) needs Appium. This repo layers both.

| Layer | Tool | Runs on | Marker |
|---|---|---|---|
| Mobile web | Playwright device descriptors | any machine, every PR | `mobile_web` |
| Mobile native | Appium 2 + UiAutomator2 | Android emulator (CI job `mobile-native`) | `mobile_native` |

## Layer 1: device emulation
- [`tests/mobile/web/conftest.py`](../../tests/mobile/web/conftest.py): a context per phone
  (`Pixel 7`, `iPhone 13`) built from `playwright.devices[name]` (viewport, pixel ratio, touch,
  user agent). The **same** `LoginPage` and `InventoryPage` objects from chapter 02 are reused.
- [`tests/mobile/web/test_mobile_web.py`](../../tests/mobile/web/test_mobile_web.py): single-column
  layout via bounding boxes, no horizontal scroll, tap-to-open menu, landscape, the chat widget on a phone.
- The engine is whatever `--browser` says. For Safari's real engine: `BROWSER=webkit make test-mobile-web`.
  (Firefox can't emulate `isMobile`, so it isn't used here.)

## Layer 2: Appium
- [`mobile/driver_factory.py`](../../mobile/driver_factory.py): `AppiumDriverFactory` builds
  `UiAutomator2Options` from settings (**Factory** pattern), and `appium_is_running()` checks `/status`.
- [`mobile/screens/`](../../mobile/screens): `BaseScreen` + screen objects. The Page Object Model
  again, renamed "screen" as in the Appium world.
- [`tests/mobile/native/`](../../tests/mobile/native): capability unit tests run everywhere; the
  device tests **skip** unless an Appium server answers.

These tests drive **Chrome on Android** against saucedemo, so the locators are the same known
`data-test` attributes. For a native `.apk`, add `create_native(app_path)` screens with
`accessibility_id()` locators; the factory already has `native_options()`.

## Run it locally with an emulator
```bash
npm i -g appium && appium driver install uiautomator2
appium --allow-insecure chromedriver_autodownload &      # fetches the matching chromedriver
emulator -avd <your_avd> &                               # Android Studio AVD with Google APIs
make test-mobile-native
```
Settings: `APPIUM_SERVER_URL`, `ANDROID_DEVICE_NAME` (default `emulator-5554`).

## Try it
Add `iPad Mini` to `PHONES` and see which layout assertion fails. Is it a bug or a wrong assumption?

## Test your knowledge
1. Why doesn't an iPhone profile on Chromium prove Safari compatibility?
2. Why do native tests skip rather than fail without Appium?

<details><summary>Answers</summary>

1. The profile changes screen size, touch and user agent; the rendering engine is still Chromium.
2. Missing infrastructure isn't a product bug; a failure would train people to ignore red builds.
   CI has a dedicated job where Appium *is* present, so there they really run.
</details>
