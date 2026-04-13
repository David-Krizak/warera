from playwright.sync_api import sync_playwright

URL = "https://app.warera.io/world"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(URL)

        print(">>> Log in manually (including OTP)")
        input(">>> Press ENTER when fully logged in...")

        context.storage_state(path="session.json")
        print(">>> Session saved to session.json")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
