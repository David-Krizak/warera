from __future__ import annotations

import time
from typing import Tuple

from playwright.sync_api import (
    sync_playwright,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from game_selectors import (
    LOGGED_IN_SELECTOR,
    INITIAL_WAIT_SECONDS,
)

CHROME_USER_DATA_DIR = "/home/david/gamebot/warera/chrome-profile"
URL = "https://app.warera.io"


def is_logged_in(page: Page) -> bool:
    try:
        page.locator(LOGGED_IN_SELECTOR).wait_for(state="visible", timeout=15000)
        return True
    except PlaywrightTimeoutError:
        return False


def attach_debug_hooks(page: Page) -> None:
    page.on(
        "framenavigated",
        lambda frame: print(f"[NAVIGATED] {frame.url}") if frame == page.main_frame else None,
    )
    page.on(
        "requestfailed",
        lambda req: print(f"[REQUEST FAILED] {req.url}") if "api" in req.url else None,
    )


def open_game(playwright: Playwright) -> Tuple[BrowserContext, Page]:
    context = playwright.chromium.launch_persistent_context(
        CHROME_USER_DATA_DIR,
        channel="chrome",
        headless=False,
        args=["--profile-directory=Default"],
        viewport={"width": 1600, "height": 900},
    )

    page = context.pages[0] if context.pages else context.new_page()
    attach_debug_hooks(page)

    print("[INFO] Opening page...")
    page.goto(URL, wait_until="domcontentloaded", timeout=30000)

    print("[INFO] Current URL:", page.url)
    print("[INFO] Title:", page.title())

    if not is_logged_in(page):
        context.close()
        raise RuntimeError("Not logged in")

    print("[SUCCESS] Logged in")
    print(f"[INFO] Waiting {INITIAL_WAIT_SECONDS} seconds before reading selectors...")
    time.sleep(INITIAL_WAIT_SECONDS)

    return context, page