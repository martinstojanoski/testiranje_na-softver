import re
from playwright.sync_api import sync_playwright, expect


def test_login_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        username = "user"
        password = "mypassword"

        page.goto("http://127.0.0.1:5000/login", wait_until="domcontentloaded")

        page.locator("input[name='username']").fill(username)
        page.locator("input[name='password']").fill(password)
        page.locator("button[type='submit']").click()

        # ✅ URL assertion with REGEX (no lambda)
        # Ако твојата апликација редиректира назад на /login при грешка:
        expect(page).to_have_url(re.compile(r".*/login(\?.*)?$"), timeout=7000)

        # ✅ Find flash/error message (fallbacks)
        candidates = [
            "[data-testid='flash-message']",
            ".flash",
            ".alert",
            ".alert-danger",
            ".error",
            ".message",
            "#flash",
            "#message",
        ]

        flash_locator = None
        for sel in candidates:
            loc = page.locator(sel)
            if loc.count() > 0:
                flash_locator = loc.first
                break

        # Fallback by text (ако немаш класa/id за flash)
        if flash_locator is None:
            flash_locator = page.get_by_text("Invalid", exact=False)

        # ✅ Expect visible
        expect(flash_locator).to_be_visible(timeout=7000)

        # ✅ Validate content loosely (да не биде fragile)
        text = (flash_locator.inner_text() or "").strip().lower()
        allowed_keywords = ["invalid", "credential", "wrong", "error", "нев", "погреш"]

        if not any(k in text for k in allowed_keywords):
            page.screenshot(path="login_invalid_FAIL_message.png", full_page=True)
            raise AssertionError(
                f"Flash message is visible but unexpected.\n"
                f"Text: {flash_locator.inner_text()!r}\n"
                f"URL: {page.url}"
            )

        page.screenshot(path="login_invalid_PASS.png", full_page=True)
        print("✅ test_login_invalid PASSED (invalid login message shown).")

        context.close()
        browser.close()


if __name__ == "__main__":
    test_login_invalid()
