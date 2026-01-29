from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _assert_not_found_or_error(page, screenshot_name: str):
    """
    Robust assert for: 'not found' / error message.
    Works even if you don't have div.flash.error.
    """
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(250)

    # Look for any common not-found/error text in MK/EN
    try:
        page.wait_for_selector(
            "text=/Нема пронајдена регистрација|нема пронајдена резервација|не постои|not found|no booking|error|грешк/i",
            timeout=6000,
        )
    except TimeoutError:
        page.screenshot(path=f"{screenshot_name}_FAIL.png", full_page=True)
        print("URL:", page.url)
        print("Body text (first 1200 chars):\n", page.inner_text("body")[:1200])
        raise AssertionError("❌ Expected not-found/error message, but none was detected.")

    page.screenshot(path=f"{screenshot_name}_OK.png", full_page=True)


def test_invalid_email_format_blocked_by_browser():
    """
    Negative case: invalid email format.
    Expected:
      - HTML5 validation blocks submit
      - email input fails checkValidity()
      - URL stays on /booking-status
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

            page.fill("input[name='email']", "not-an-email")  # invalid format
            page.click("button[type='submit']")
            page.wait_for_timeout(250)

            # Should remain on the same page (browser validation blocks submit)
            if "/booking-status" not in page.url:
                page.screenshot(path="invalid_email_unexpected_submit.png", full_page=True)
                raise AssertionError(f"❌ Form submitted unexpectedly. URL: {page.url}")

            is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
            if not is_invalid:
                page.screenshot(path="invalid_email_validity_failed.png", full_page=True)
                raise AssertionError("❌ Expected invalid email format, but input passed validation.")

            page.screenshot(path="invalid_email_blocked_ok.png", full_page=True)
            print("✅ invalid email blocked by browser validation (negative test passed).")

        finally:
            browser.close()


def test_injection_like_email_does_not_crash_and_returns_not_found():
    """
    Negative case: injection-like email input.
    Expected:
      - Either blocked by browser email validation
      - Or backend safely returns not-found/error (no crash, no success)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

            # Make it look like email but still suspicious; browser may mark invalid (that's OK)
            evil = "a@b.com' OR '1'='1"
            page.fill("input[name='email']", evil)

            is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
            if is_invalid:
                page.screenshot(path="injection_blocked_by_browser_ok.png", full_page=True)
                print("✅ injection-like input blocked by browser (negative test passed).")
            else:
                page.click("button[type='submit']")
                _assert_not_found_or_error(page, "injection_safe_not_found")
                print("✅ injection-like input did not crash and returned not-found/error (negative test passed).")

        finally:
            browser.close()


def test_whitespace_email_returns_not_found_or_blocked():
    """
    Negative case: whitespace input.
    Expected:
      - Either browser blocks (type=email / required)
      - Or backend returns not-found/error safely
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

            page.fill("input[name='email']", "   ")  # whitespace

            is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
            if is_invalid:
                page.screenshot(path="whitespace_blocked_by_browser_ok.png", full_page=True)
                print("✅ whitespace blocked by browser validation (negative test passed).")
            else:
                page.click("button[type='submit']")
                _assert_not_found_or_error(page, "whitespace_not_found")
                print("✅ whitespace did not crash and returned not-found/error (negative test passed).")

        finally:
            browser.close()


if __name__ == "__main__":
    test_invalid_email_format_blocked_by_browser()
    test_injection_like_email_does_not_crash_and_returns_not_found()
    test_whitespace_email_returns_not_found_or_blocked()
