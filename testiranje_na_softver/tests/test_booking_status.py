from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _create_booking_via_form(page, first_name, last_name, email, phone, checkin, checkout):
    """
    Creates a booking by submitting /booking form.
    Your /booking route saves into SQLite and redirects to /booking-status.
    """
    page.goto(f"{BASE_URL}/booking", wait_until="domcontentloaded")

    page.fill("input[name='first_name']", first_name)
    page.fill("input[name='last_name']", last_name)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)
    page.fill("input[name='checkin_date']", checkin)
    page.fill("input[name='checkout_date']", checkout)

    page.click("button[type='submit']")

    # After successful booking, your app redirects to /booking-status
    page.wait_for_url(f"{BASE_URL}/booking-status", timeout=8000)


def test_booking_status_email_not_found_shows_error():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

        email = "no_such_booking_12345@example.com"
        page.fill("input[name='email']", email)
        page.click("button[type='submit']")

        # Expect flash error: "❌ Нема пронајдена регистрација за овој email."
        page.wait_for_selector("div.flash.error", timeout=5000)
        page.wait_for_selector("text=Нема пронајдена регистрација за овој email", timeout=5000)

        page.screenshot(path="booking_status_not_found.png", full_page=True)

        context.close()
        browser.close()


def test_booking_status_found_shows_booking_details_and_stay_days():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Create unique test data
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        first_name = "Test"
        last_name = f"User{stamp}"
        email = f"test_{stamp}@example.com"
        phone = "070123456"

        checkin = datetime.now().strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        expected_days = 3

        # 1) Create booking (writes to DB)
        _create_booking_via_form(page, first_name, last_name, email, phone, checkin, checkout)

        # 2) Now on /booking-status, search by same email
        # (If your redirect already landed on booking-status page, ensure form is there.)
        page.fill("input[name='email']", email)
        page.click("button[type='submit']")

        # 3) Assertions: booking-result block + values appear
        page.wait_for_selector("div.booking-result", timeout=5000)

        # Name
        page.wait_for_selector(f"text={first_name}", timeout=5000)
        page.wait_for_selector(f"text={last_name}", timeout=5000)

        # Dates
        page.wait_for_selector(f"text={checkin}", timeout=5000)
        page.wait_for_selector(f"text={checkout}", timeout=5000)

        # Stay days (template shows: "Вкупно денови: X дена")
        page.wait_for_selector(f"text=Вкупно денови:", timeout=5000)
        page.wait_for_selector(f"text={expected_days} дена", timeout=5000)

        # Success text in template
        page.wait_for_selector("text=Регистрацијата е успешна", timeout=5000)

        page.screenshot(path="booking_status_found.png", full_page=True)

        context.close()
        browser.close()


def test_booking_status_email_required_browser_validation():
    """
    This checks the HTML5 required validation (client-side).
    If the email input is required, the form should not submit with empty value.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

        # Click submit without filling email
        page.click("button[type='submit']")

        # If browser validation prevents submit, URL remains the same and input is invalid
        if page.url != f"{BASE_URL}/booking-status":
            raise AssertionError(f"❌ Form submitted unexpectedly. URL changed to: {page.url}")

        # Check validity state from DOM
        is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
        if not is_invalid:
            page.screenshot(path="booking_status_email_required_fail.png", full_page=True)
            raise AssertionError("❌ Expected email input to be invalid (required), but it is valid.")

        page.screenshot(path="booking_status_email_required_ok.png", full_page=True)

        context.close()
        browser.close()


if __name__ == "__main__":
    test_booking_status_email_not_found_shows_error()
    test_booking_status_found_shows_booking_details_and_stay_days()
    test_booking_status_email_required_browser_validation()
