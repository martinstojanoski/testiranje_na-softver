from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"


def test_invalid_email_format_blocked_by_browser():
    """
    Invalid email format should be blocked by HTML5 validation (input[type=email]).
    Expectation:
      - The form does NOT submit
      - The email input is invalid according to checkValidity()
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

        page.fill("input[name='email']", "not-an-email")  # invalid format
        page.click("button[type='submit']")

        # Should remain on the same page (no POST due to browser validation)
        if page.url != f"{BASE_URL}/booking-status":
            page.screenshot(path="invalid_email_unexpected_submit.png", full_page=True)
            raise AssertionError(f"❌ Form submitted unexpectedly. URL: {page.url}")

        # DOM check: invalid email must fail validity check
        is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
        if not is_invalid:
            page.screenshot(path="invalid_email_validity_failed.png", full_page=True)
            raise AssertionError("❌ Expected invalid email format, but input passed validation.")

        page.screenshot(path="invalid_email_blocked_ok.png", full_page=True)

        context.close()
        browser.close()


def test_injection_like_email_does_not_crash_and_returns_not_found():
    """
    Injection-like input must NOT crash the app.
    Since backend uses parameterized query (WHERE email = ?),
    expected behavior is: NOT FOUND flash error.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

        # Keep it "email-ish" so browser is less likely to block it
        evil = "a@b.com' OR '1'='1"
        page.fill("input[name='email']", evil)

        # If browser blocks it as invalid email, treat that as acceptable outcome too.
        is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
        if is_invalid:
            page.screenshot(path="injection_blocked_by_browser_ok.png", full_page=True)
        else:
            page.click("button[type='submit']")

            # Must show "not found" flash error, not a server crash
            page.wait_for_selector("div.flash.error", timeout=5000)
            page.wait_for_selector("text=Нема пронајдена регистрација за овој email.", timeout=5000)

            page.screenshot(path="injection_safe_not_found_ok.png", full_page=True)

        context.close()
        browser.close()


def test_whitespace_email_returns_not_found():
    """
    Edge invalid: whitespace input.
    Browser required attribute checks empty string, but whitespace may pass required.
    Backend will search whitespace in DB and should show not found error.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

        page.fill("input[name='email']", "   ")  # only spaces

        # Browser may mark it invalid because type=email expects format.
        is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
        if is_invalid:
            page.screenshot(path="whitespace_blocked_by_browser_ok.png", full_page=True)
        else:
            page.click("button[type='submit']")
            page.wait_for_selector("div.flash.error", timeout=5000)
            page.wait_for_selector("text=Нема пронајдена регистрација за овој email.", timeout=5000)
            page.screenshot(path="whitespace_not_found_ok.png", full_page=True)

        context.close()
        browser.close()


if __name__ == "__main__":
    test_invalid_email_format_blocked_by_browser()
    test_injection_like_email_does_not_crash_and_returns_not_found()
    test_whitespace_email_returns_not_found()
