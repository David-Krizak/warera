from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CHROME_USER_DATA_DIR = "/home/david/gamebot/warera/chrome-profile"
URL = "https://app.warera.io"

LOGGED_IN_SELECTOR = 'xpath=//*[@id="companies-nav-button"]'


def is_logged_in(page) -> bool:
    try:
        page.locator(LOGGED_IN_SELECTOR).wait_for(state="visible", timeout=5000)
        return True
    except PlaywrightTimeoutError:
        return False


with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        CHROME_USER_DATA_DIR,
        channel="chrome",
        headless=False,
        args=["--profile-directory=Default"],
        viewport={"width": 1600, "height": 900},
    )

    page = context.pages[0] if context.pages else context.new_page()

    # debug hooks (IMPORTANT)
    page.on("console", lambda msg: print(f"[BROWSER] {msg.type}: {msg.text}"))
    page.on("requestfailed", lambda req: print(f"[REQUEST FAILED] {req.url}"))
    page.on("framenavigated", lambda frame: print(f"[NAVIGATED] {frame.url}"))

    print("[INFO] Opening page...")
    page.goto(URL, wait_until="domcontentloaded", timeout=30000)

    print("[INFO] Current URL:", page.url)
    print("[INFO] Title:", page.title())

    # check login
    if is_logged_in(page):
        print("[SUCCESS] Logged in using copied profile")
    else:
        print("[FAIL] Not logged in")
        print("→ Either cookies didn’t copy OR profile mismatch")

    input("Press ENTER to close...")

    context.close()